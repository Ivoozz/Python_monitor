"""
Collector module that runs on System A.
Polls multiple agent systems via XML-RPC and collects metrics.
"""

import os
import sys
import time
import json
import logging
import configparser
import xmlrpc.client
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.monitoring.storage import create_storage, StorageBackend


class AgentConnection:
    """Manages connection to a single agent."""

    def __init__(self, name: str, host: str, port: int, timeout: int = 10):
        self.name = name
        self.host = host
        self.port = port
        self.timeout = timeout
        self.proxy = None
        self._last_success = None
        self._failure_count = 0

    def connect(self) -> bool:
        """Establish connection to the agent."""
        try:
            url = f"http://{self.host}:{self.port}"
            self.proxy = xmlrpc.client.ServerProxy(url, allow_none=True)
            # Test connection with ping
            result = self.proxy.ping()
            return result == "pong"
        except Exception as e:
            logging.debug(f"Failed to connect to {self.name}: {e}")
            self.proxy = None
            return False

    def is_connected(self) -> bool:
        """Check if connection is active."""
        if self.proxy is None:
            return False
        
        try:
            self.proxy.ping()
            return True
        except Exception:
            return False

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Fetch metrics from the agent."""
        if not self.is_connected():
            if not self.connect():
                self._failure_count += 1
                return None

        try:
            metrics = self.proxy.get_metrics()
            self._last_success = datetime.now()
            self._failure_count = 0
            return metrics
        except xmlrpc.client.Fault as e:
            logging.error(f"XML-RPC fault from {self.name}: {e}")
            self._failure_count += 1
            self.proxy = None
            return None
        except Exception as e:
            logging.warning(f"Failed to get metrics from {self.name}: {e}")
            self._failure_count += 1
            self.proxy = None
            return None


class ThresholdMonitor:
    """Monitors metrics against configurable thresholds."""

    def __init__(self, config: configparser.ConfigParser):
        self.config = config
        self.thresholds = {
            "cpu_temp_warning": float(config.get("thresholds", "cpu_temp_warning", fallback=70)),
            "cpu_temp_critical": float(config.get("thresholds", "cpu_temp_critical", fallback=85)),
            "load_warning": float(config.get("thresholds", "load_warning", fallback=2.0)),
            "load_critical": float(config.get("thresholds", "load_critical", fallback=4.0)),
            "cpu_usage_warning": float(config.get("thresholds", "cpu_usage_warning", fallback=80)),
            "cpu_usage_critical": float(config.get("thresholds", "cpu_usage_critical", fallback=95)),
        }

    def check_metrics(self, metrics: Dict[str, Any], agent_name: str) -> List[Dict[str, Any]]:
        """Check metrics against thresholds and return alerts."""
        alerts = []

        # Check CPU temperature
        temp = metrics.get("cpu_temperature")
        if temp is not None:
            if temp >= self.thresholds["cpu_temp_critical"]:
                alerts.append({
                    "agent": agent_name,
                    "type": "cpu_temperature",
                    "severity": "critical",
                    "value": temp,
                    "threshold": self.thresholds["cpu_temp_critical"],
                    "message": f"CPU temperature critical: {temp}°C"
                })
            elif temp >= self.thresholds["cpu_temp_warning"]:
                alerts.append({
                    "agent": agent_name,
                    "type": "cpu_temperature",
                    "severity": "warning",
                    "value": temp,
                    "threshold": self.thresholds["cpu_temp_warning"],
                    "message": f"CPU temperature high: {temp}°C"
                })

        # Check system load (1min)
        load = metrics.get("system_load", {}).get("1min", 0)
        num_cpus = metrics.get("cpu_usage", 1)  # Approximate
        
        if load >= self.thresholds["load_critical"]:
            alerts.append({
                "agent": agent_name,
                "type": "system_load",
                "severity": "critical",
                "value": load,
                "threshold": self.thresholds["load_critical"],
                "message": f"System load critical: {load}"
            })
        elif load >= self.thresholds["load_warning"]:
            alerts.append({
                "agent": agent_name,
                "type": "system_load",
                "severity": "warning",
                "value": load,
                "threshold": self.thresholds["load_warning"],
                "message": f"System load high: {load}"
            })

        # Check CPU usage
        cpu_usage = metrics.get("cpu_usage", 0)
        if cpu_usage >= self.thresholds["cpu_usage_critical"]:
            alerts.append({
                "agent": agent_name,
                "type": "cpu_usage",
                "severity": "critical",
                "value": cpu_usage,
                "threshold": self.thresholds["cpu_usage_critical"],
                "message": f"CPU usage critical: {cpu_usage}%"
            })
        elif cpu_usage >= self.thresholds["cpu_usage_warning"]:
            alerts.append({
                "agent": agent_name,
                "type": "cpu_usage",
                "severity": "warning",
                "value": cpu_usage,
                "threshold": self.thresholds["cpu_usage_warning"],
                "message": f"CPU usage high: {cpu_usage}%"
            })

        # Check security threats
        threats = metrics.get("security_threats", [])
        for threat in threats:
            alerts.append({
                "agent": agent_name,
                "type": "security_threat",
                "severity": threat.get("severity", "unknown"),
                "value": threat,
                "message": f"Security threat: {threat.get('description', 'Unknown')}"
            })

        return alerts


class Collector:
    """Main collector that polls multiple agents and stores metrics."""

    def __init__(self, config_path: str = "config/config.ini"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Set up logging
        self._setup_logging()
        
        # Initialize components
        self.storage = self._init_storage()
        self.threshold_monitor = ThresholdMonitor(self.config)
        
        # Agent management
        self.agents: Dict[str, AgentConnection] = {}
        self._load_agents()
        
        # Control flags
        self._running = False
        self._stop_event = threading.Event()
        
        # Metrics queue for thread-safe processing
        self._metrics_queue = queue.Queue()
        
        # Polling settings
        self.poll_interval = int(self.config.get("general", "poll_interval", fallback=10))

    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from file."""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            config.read(self.config_path)
        else:
            # Try alternative path
            alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   self.config_path)
            if os.path.exists(alt_path):
                config.read(alt_path)
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
        return config

    def _setup_logging(self):
        """Configure logging with file rotation."""
        log_file = self.config.get("logging", "log_file", fallback="/var/log/monitoring/collector.log")
        log_level = self.config.get("general", "log_level", fallback="INFO")
        max_size = int(self.config.get("logging", "max_log_size", fallback=10)) * 1024 * 1024
        backup_count = int(self.config.get("logging", "backup_count", fallback=5))

        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Configure rotating file handler
        from logging.handlers import RotatingFileHandler
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_size,
            backupCount=backup_count
        )
        handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        root_logger.addHandler(handler)
        
        # Also add console handler for important messages
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root_logger.addHandler(console)

    def _init_storage(self) -> StorageBackend:
        """Initialize storage backend."""
        backend = self.config.get("storage", "backend", fallback="log")
        
        if backend == "mysql":
            return create_storage(
                "mysql",
                host=self.config.get("mysql", "host", fallback="localhost"),
                port=int(self.config.get("mysql", "port", fallback=3306)),
                user=self.config.get("mysql", "user", fallback="monitor"),
                password=self.config.get("mysql", "password", fallback="changeme"),
                database=self.config.get("mysql", "database", fallback="monitoring")
            )
        elif backend == "sqlite":
            return create_storage("sqlite", db_path="/var/log/monitoring/metrics.db")
        else:
            log_dir = self.config.get("logging", "log_file", fallback="/var/log/monitoring/collector.log")
            log_dir = os.path.dirname(log_file) if log_dir else "/var/log/monitoring"
            return create_storage("log", log_dir=f"{log_dir}/data")

    def _load_agents(self):
        """Load agents from configuration."""
        if self.config.has_section("agents"):
            for name, address in self.config.items("agents"):
                if "=" in name:
                    name = name.split("=", 1)[0].strip()
                if "=" in address:
                    address = address.split("=", 1)[1].strip()
                
                if ":" in address:
                    host, port = address.rsplit(":", 1)
                    try:
                        port = int(port)
                        self.agents[name] = AgentConnection(name, host, port)
                        logging.info(f"Loaded agent: {name} at {host}:{port}")
                    except ValueError:
                        logging.error(f"Invalid port for agent {name}: {address}")

    def add_agent(self, name: str, host: str, port: int):
        """Add a new agent to monitor."""
        self.agents[name] = AgentConnection(name, host, port)
        logging.info(f"Added agent: {name} at {host}:{port}")

    def remove_agent(self, name: str):
        """Remove an agent from monitoring."""
        if name in self.agents:
            del self.agents[name]
            logging.info(f"Removed agent: {name}")

    def poll_agent(self, name: str) -> Optional[Dict[str, Any]]:
        """Poll a single agent for metrics."""
        agent = self.agents.get(name)
        if not agent:
            return None

        metrics = agent.get_metrics()
        if metrics:
            metrics["_agent_name"] = name
            return metrics
        return None

    def poll_all_agents(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Poll all agents concurrently."""
        all_metrics = []
        all_alerts = []

        with ThreadPoolExecutor(max_workers=len(self.agents)) as executor:
            future_to_agent = {
                executor.submit(self.poll_agent, name): name 
                for name in self.agents
            }

            for future in as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    metrics = future.result()
                    if metrics:
                        all_metrics.append(metrics)
                        
                        # Check thresholds
                        alerts = self.threshold_monitor.check_metrics(metrics, agent_name)
                        all_alerts.extend(alerts)
                        
                        if alerts:
                            for alert in alerts:
                                logging.warning(f"Alert: {alert['message']}")
                except Exception as e:
                    logging.error(f"Error polling agent {agent_name}: {e}")

        return all_metrics, all_alerts

    def store_metrics(self, metrics_list: List[Dict[str, Any]]):
        """Store metrics to the configured storage backend."""
        for metrics in metrics_list:
            agent_name = metrics.pop("_agent_name", "unknown")
            timestamp = metrics.pop("timestamp", None)
            
            if timestamp:
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except (ValueError, TypeError):
                    timestamp = None

            # Store each metric type separately
            if "cpu_temperature" in metrics:
                temp = metrics["cpu_temperature"]
                if temp is not None:
                    self.storage.save_metric(
                        agent_name, "cpu_temperature", temp, timestamp
                    )

            if "cpu_usage" in metrics:
                self.storage.save_metric(
                    agent_name, "cpu_usage", metrics["cpu_usage"], timestamp
                )

            if "system_load" in metrics:
                self.storage.save_metric(
                    agent_name, "system_load", 
                    json.dumps(metrics["system_load"]), timestamp
                )

            if "security_threats" in metrics:
                threats = metrics["security_threats"]
                if threats:
                    self.storage.save_metric(
                        agent_name, "security_threats",
                        json.dumps(threats), timestamp
                    )

            if "memory" in metrics:
                self.storage.save_metric(
                    agent_name, "memory",
                    json.dumps(metrics["memory"]), timestamp
                )

    def start(self):
        """Start the collector polling loop."""
        self._running = True
        logging.info("Collector started")
        logging.info(f"Monitoring {len(self.agents)} agent(s)")

        while not self._stop_event.is_set():
            try:
                # Poll all agents
                metrics_list, alerts = self.poll_all_agents()
                
                # Store metrics
                if metrics_list:
                    self.store_metrics(metrics_list)
                    logging.debug(f"Collected metrics from {len(metrics_list)} agent(s)")
                
                # Log alerts
                for alert in alerts:
                    if alert["severity"] in ["critical", "warning"]:
                        log_func = logging.warning if alert["severity"] == "warning" else logging.error
                        log_func(f"ALERT [{alert['severity']}]: {alert['message']}")
                
                # Wait for next poll interval
                self._stop_event.wait(timeout=self.poll_interval)

            except Exception as e:
                logging.error(f"Error in collector loop: {e}")
                self._stop_event.wait(timeout=self.poll_interval)

        logging.info("Collector stopped")

    def stop(self):
        """Stop the collector."""
        self._stop_event.set()
        self._running = False
        logging.info("Stopping collector...")

    def get_storage(self) -> StorageBackend:
        """Get the storage backend."""
        return self.storage


def main():
    """Main entry point for the collector."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitoring Collector")
    parser.add_argument("--config", default="config/config.ini", 
                        help="Path to config file")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")

    args = parser.parse_args()

    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    try:
        collector = Collector(config_path=args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        collector.start()
    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
        collector.stop()
    except Exception as e:
        logging.error(f"Collector error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
