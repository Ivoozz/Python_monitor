#!/usr/bin/env python3
"""
XML-RPC Collector for System Monitoring
Runs on System A and collects metrics from multiple System B agents
"""

import sys
import json
import time
import logging
import xmlrpc.client
from datetime import datetime
from typing import Dict, List, Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal

# Import storage abstractions
sys.path.append('/home/engine/project/storage')
from storage_factory import StorageFactory


class MetricCollector:
    """Collector that polls multiple agents and stores metrics"""
    
    def __init__(self, config_path: str = '/home/engine/project/config/collector_config.json'):
        """Initialize the collector"""
        self.config = self.load_config(config_path)
        self.agents = self.config.get('agents', [])
        self.running = False
        self.storage = StorageFactory.create_storage(self.config.get('storage', {}))
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger('MetricCollector')
        
        self.logger.info(f"Collector initialized with {len(self.agents)} agents")
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load collector configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "agents": [
                {"host": "localhost", "port": 8000, "name": "localhost"}
            ],
            "poll_interval": 30,
            "timeout": 10,
            "storage": {
                "type": "file",
                "log_file": "/var/log/metrics_collector.log",
                "metrics_file": "/var/log/metrics_data.log",
                "rotation": {
                    "max_size": "10MB",
                    "backup_count": 5
                }
            },
            "thresholds": {
                "cpu_usage": 80,
                "cpu_temperature": 70,
                "system_load": 2.0,
                "memory_usage": 85,
                "disk_usage": 90
            }
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('storage', {})
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config.get('log_file', '/var/log/metrics_collector.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def create_agent_proxy(self, agent_config: Dict[str, Any]) -> xmlrpc.client.ServerProxy:
        """Create XML-RPC proxy for an agent"""
        host = agent_config.get('host', 'localhost')
        port = agent_config.get('port', 8000)
        url = f"http://{host}:{port}"
        return xmlrpc.client.ServerProxy(url, allow_none=True)
    
    def collect_from_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics from a single agent"""
        agent_name = agent_config.get('name', agent_config.get('host'))
        timeout = self.config.get('timeout', 10)
        
        try:
            proxy = self.create_agent_proxy(agent_config)
            
            # Test connection
            result = proxy.ping()
            self.logger.debug(f"Ping successful for {agent_name}: {result}")
            
            # Get metrics
            metrics = proxy.get_metrics()
            
            # Add metadata
            metrics['agent_name'] = agent_name
            metrics['collection_time'] = datetime.now().isoformat()
            metrics['status'] = 'success'
            
            # Check thresholds
            metrics['alerts'] = self.check_thresholds(metrics)
            
            self.logger.info(f"Successfully collected metrics from {agent_name}")
            return metrics
            
        except xmlrpc.client.Fault as e:
            error_msg = f"XML-RPC fault from {agent_name}: {e.faultString}"
            self.logger.error(error_msg)
            return {
                'agent_name': agent_name,
                'status': 'error',
                'error': error_msg,
                'collection_time': datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Error collecting from {agent_name}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'agent_name': agent_name,
                'status': 'error',
                'error': error_msg,
                'collection_time': datetime.now().isoformat()
            }
    
    def check_thresholds(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check metrics against thresholds and generate alerts"""
        alerts = []
        thresholds = self.config.get('thresholds', {})
        
        # Check CPU usage
        if 'cpu_usage' in metrics and 'cpu_usage' in thresholds:
            if metrics['cpu_usage'] > thresholds['cpu_usage']:
                alerts.append({
                    'type': 'CPU_USAGE',
                    'severity': 'HIGH',
                    'value': metrics['cpu_usage'],
                    'threshold': thresholds['cpu_usage'],
                    'message': f"CPU usage ({metrics['cpu_usage']:.1f}%) exceeds threshold ({thresholds['cpu_usage']}%)"
                })
        
        # Check CPU temperature
        if metrics.get('cpu_temperature') and 'cpu_temperature' in thresholds:
            if metrics['cpu_temperature'] > thresholds['cpu_temperature']:
                alerts.append({
                    'type': 'CPU_TEMPERATURE',
                    'severity': 'HIGH',
                    'value': metrics['cpu_temperature'],
                    'threshold': thresholds['cpu_temperature'],
                    'message': f"CPU temperature ({metrics['cpu_temperature']:.1f}°C) exceeds threshold ({thresholds['cpu_temperature']}°C)"
                })
        
        # Check system load
        if 'system_load' in metrics and 'system_load' in thresholds:
            if metrics['system_load']['1min'] > thresholds['system_load']:
                alerts.append({
                    'type': 'SYSTEM_LOAD',
                    'severity': 'MEDIUM',
                    'value': metrics['system_load']['1min'],
                    'threshold': thresholds['system_load'],
                    'message': f"System load ({metrics['system_load']['1min']:.2f}) exceeds threshold ({thresholds['system_load']})"
                })
        
        # Check memory usage
        if 'memory_usage' in metrics and 'memory_usage' in thresholds:
            if metrics['memory_usage']['percent'] > thresholds['memory_usage']:
                alerts.append({
                    'type': 'MEMORY_USAGE',
                    'severity': 'MEDIUM',
                    'value': metrics['memory_usage']['percent'],
                    'threshold': thresholds['memory_usage'],
                    'message': f"Memory usage ({metrics['memory_usage']['percent']:.1f}%) exceeds threshold ({thresholds['memory_usage']}%)"
                })
        
        # Check disk usage
        if 'disk_usage' in metrics and 'disk_usage' in thresholds:
            if metrics['disk_usage']['percent'] > thresholds['disk_usage']:
                alerts.append({
                    'type': 'DISK_USAGE',
                    'severity': 'HIGH',
                    'value': metrics['disk_usage']['percent'],
                    'threshold': thresholds['disk_usage'],
                    'message': f"Disk usage ({metrics['disk_usage']['percent']:.1f}%) exceeds threshold ({thresholds['disk_usage']}%)"
                })
        
        # Check security threats
        if metrics.get('security_threats', {}).get('status') in ['WARNING', 'ERROR']:
            alerts.append({
                'type': 'SECURITY_THREAT',
                'severity': 'CRITICAL',
                'status': metrics['security_threats']['status'],
                'message': f"Security issues detected: {len(metrics['security_threats'].get('issues', []))} issues found"
            })
        
        return alerts
    
    def collect_all_metrics(self) -> List[Dict[str, Any]]:
        """Collect metrics from all agents"""
        if not self.agents:
            self.logger.warning("No agents configured")
            return []
        
        results = []
        max_workers = min(len(self.agents), 10)  # Limit concurrent connections
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_agent = {
                executor.submit(self.collect_from_agent, agent): agent 
                for agent in self.agents
            }
            
            for future in as_completed(future_to_agent):
                try:
                    result = future.result(timeout=self.config.get('timeout', 10))
                    results.append(result)
                except Exception as e:
                    agent = future_to_agent[future]
                    self.logger.error(f"Error in future for {agent.get('name', 'unknown')}: {e}")
        
        return results
    
    def store_metrics(self, metrics_list: List[Dict[str, Any]]):
        """Store metrics using the storage abstraction"""
        try:
            self.storage.store(metrics_list)
            self.logger.debug(f"Stored {len(metrics_list)} metric records")
        except Exception as e:
            self.logger.error(f"Error storing metrics: {e}")
    
    def start_collection(self):
        """Start the collection loop"""
        self.running = True
        poll_interval = self.config.get('poll_interval', 30)
        
        self.logger.info(f"Starting collection loop (interval: {poll_interval}s)")
        
        while self.running:
            try:
                start_time = time.time()
                
                self.logger.info("Starting metric collection cycle")
                metrics = self.collect_all_metrics()
                
                # Store metrics
                self.store_metrics(metrics)
                
                # Report alerts
                for metric in metrics:
                    if metric.get('alerts'):
                        for alert in metric['alerts']:
                            self.logger.warning(
                                f"ALERT [{alert['severity']}] from {metric['agent_name']}: {alert['message']}"
                            )
                
                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, poll_interval - elapsed)
                
                if sleep_time > 0:
                    self.logger.debug(f"Collection cycle completed in {elapsed:.2f}s, sleeping for {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Collection cycle took {elapsed:.2f}s, longer than poll interval ({poll_interval}s)")
                
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                if not self.running:
                    break
                time.sleep(5)  # Brief pause before retrying
    
    def stop_collection(self):
        """Stop the collection loop"""
        self.logger.info("Stopping collection...")
        self.running = False


def main():
    """Main entry point for the collector"""
    collector = MetricCollector()
    
    # Handle shutdown gracefully
    def signal_handler(signum, frame):
        collector.stop_collection()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        collector.start_collection()
    except Exception as e:
        collector.logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()