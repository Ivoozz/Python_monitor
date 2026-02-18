"""
Agent module that runs on System B (the system being monitored).
Provides system metrics via XML-RPC.
"""

import os
import sys
import json
import logging
import platform
import xmlrpc.server
import xmlrpc.client
from socketserver import ThreadingMixIn
from datetime import datetime
from typing import Dict, Any, Optional, List
import threading
import time

# Import required libraries for metrics
try:
    import psutil
except ImportError:
    print("Error: psutil not installed. Install with: pip install psutil")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Agent")


class ThreadedXMLRPCServer(ThreadingMixIn, xmlrpc.server.SimpleXMLRPCServer):
    """Threaded XML-RPC server for handling multiple concurrent requests."""
    allow_reuse_address = True
    daemon_threads = True


class MetricsCollector:
    """Collects system metrics from the monitored machine."""

    def __init__(self):
        self._cpu_temp_cache = None
        self._cpu_temp_cache_time = 0
        self._cache_ttl = 5  # Cache temperature for 5 seconds

    def get_cpu_temperature(self) -> Optional[float]:
        """
        Get CPU temperature in Celsius.
        Returns None if temperature sensor is not available.
        
        OS-Specific Notes:
        - Linux: Uses /sys/class/thermal/thermal_zone* or psutil
        - Windows: Uses WMI (via psutil)
        - macOS: Uses IOKit (via psutil)
        """
        current_time = time.time()
        
        # Return cached value if still valid
        if (self._cpu_temp_cache is not None and 
            current_time - self._cpu_temp_cache_time < self._cache_ttl):
            return self._cpu_temp_cache

        temperature = None
        system = platform.system()

        try:
            if system == "Linux":
                temperature = self._get_linux_temperature()
            elif system == "Windows":
                temperature = self._get_windows_temperature()
            elif system == "Darwin":
                temperature = self._get_macos_temperature()
            else:
                logger.warning(f"Unsupported OS: {system}")
        except Exception as e:
            logger.warning(f"Failed to get CPU temperature: {e}")

        # Update cache
        self._cpu_temp_cache = temperature
        self._cpu_temp_cache_time = current_time

        return temperature

    def _get_linux_temperature(self) -> Optional[float]:
        """Get temperature on Linux systems."""
        # Try psutil first (works on most systems)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Try common sensor names
                for name in ['cpu_thermal', 'coretemp', 'k10temp', 'acpitz']:
                    for key, entries in temps.items():
                        if name in key.lower():
                            return entries[0].current
                # Use first available temperature
                for entries in temps.values():
                    if entries:
                        return entries[0].current
        except Exception:
            pass

        # Fallback: try reading from thermal zones
        thermal_zones = []
        for i in range(10):
            thermal_path = f"/sys/class/thermal/thermal_zone{i}"
            if os.path.exists(thermal_path):
                try:
                    with open(f"{thermal_path}/temp", "r") as f:
                        temp_millidegrees = int(f.read().strip())
                        thermal_zones.append(temp_millidegrees / 1000.0)
                except Exception:
                    pass

        if thermal_zones:
            # Return average of all thermal zones
            return sum(thermal_zones) / len(thermal_zones)

        return None

    def _get_windows_temperature(self) -> Optional[float]:
        """Get temperature on Windows systems."""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for entries in temps.values():
                    if entries:
                        return entries[0].current
        except Exception:
            pass
        return None

    def _get_macos_temperature(self) -> Optional[float]:
        """Get temperature on macOS systems."""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for entries in temps.values():
                    if entries:
                        return entries[0].current
        except Exception:
            pass
        return None

    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage.
        Returns percentage (0-100).
        """
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.error(f"Failed to get CPU usage: {e}")
            return 0.0

    def get_system_load(self) -> Dict[str, float]:
        """
        Get system load averages.
        Returns dict with '1min', '5min', '15min' keys.
        """
        try:
            load_avg = os.getloadavg()
            return {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2]
            }
        except Exception as e:
            logger.error(f"Failed to get system load: {e}")
            # On systems without load average (e.g., Windows)
            return {
                "1min": 0.0,
                "5min": 0.0,
                "15min": 0.0
            }

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        try:
            mem = psutil.virtual_memory()
            return {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent,
                "used": mem.used,
                "free": mem.free
            }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {}

    def get_disk_usage(self, path: str = "/") -> Dict[str, Any]:
        """Get disk usage for specified path."""
        try:
            disk = psutil.disk_usage(path)
            return {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        except Exception as e:
            logger.error(f"Failed to get disk usage: {e}")
            return {}

    def get_security_threats(self) -> List[Dict[str, Any]]:
        """
        Check for potential security threats.
        
        NOTE: This is a basic implementation. For production use,
        consider integrating with proper security tools like:
        - fail2ban (for SSH brute force)
        - AIDE (file integrity)
        - rkhunter (rootkits)
        - ClamAV (malware)
        
        This implementation checks:
        - Failed login attempts
        - Suspicious processes
        - Port scans (basic)
        """
        threats = []
        system = platform.system()

        try:
            if system == "Linux":
                threats.extend(self._check_linux_security())
            elif system == "Windows":
                threats.extend(self._check_windows_security())
            elif system == "Darwin":
                threats.extend(self._check_macos_security())
        except Exception as e:
            logger.error(f"Failed to check security threats: {e}")

        return threats

    def _check_linux_security(self) -> List[Dict[str, Any]]:
        """Check for security issues on Linux."""
        threats = []

        # Check for failed SSH logins (if auth.log is available)
        auth_log_paths = [
            "/var/log/auth.log",
            "/var/log/secure"
        ]
        
        for log_path in auth_log_paths:
            if os.path.exists(log_path):
                try:
                    # Check last 50 lines for failed login attempts
                    with open(log_path, "r") as f:
                        lines = f.readlines()[-50:]
                    
                    failed_logins = 0
                    for line in lines:
                        if "Failed password" in line or "authentication failure" in line:
                            failed_logins += 1
                    
                    if failed_logins > 10:
                        threats.append({
                            "type": "brute_force",
                            "severity": "high",
                            "description": f"Multiple failed SSH login attempts detected ({failed_logins})",
                            "timestamp": datetime.now().isoformat()
                        })
                        break
                except PermissionError:
                    logger.warning(f"Cannot read {log_path} - permission denied")
                except Exception as e:
                    logger.warning(f"Error reading {log_path}: {e}")
                break

        # Check for suspicious processes
        suspicious_processes = [
            "nc -l", "netcat -l",  # Listening network shells
            "ncat -l",
            "python -m SimpleHTTPServer",  # Unintentional file servers
        ]

        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                cmdline = " ".join(proc.info.get('cmdline') or [])
                for susp in suspicious_processes:
                    if susp in cmdline:
                        threats.append({
                            "type": "suspicious_process",
                            "severity": "medium",
                            "description": f"Suspicious process: {cmdline[:100]}",
                            "timestamp": datetime.now().isoformat()
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Check for listening on unusual ports
        unusual_ports = [31337, 12345, 54321]  # Common backdoor ports
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN' and conn.laddr.port in unusual_ports:
                threats.append({
                    "type": "unusual_port",
                    "severity": "high",
                    "description": f"Process listening on unusual port {conn.laddr.port}",
                    "timestamp": datetime.now().isoformat()
                })

        return threats

    def _check_windows_security(self) -> List[Dict[str, Any]]:
        """Check for security issues on Windows."""
        threats = []
        # Windows-specific checks would go here
        # For now, check for suspicious services
        return threats

    def _check_macos_security(self) -> List[Dict[str, Any]]:
        """Check for security issues on macOS."""
        threats = []
        # macOS-specific checks would go here
        return threats

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all system metrics at once."""
        return {
            "cpu_temperature": self.get_cpu_temperature(),
            "cpu_usage": self.get_cpu_usage(),
            "system_load": self.get_system_load(),
            "memory": self.get_memory_usage(),
            "disk": self.get_disk_usage(),
            "security_threats": self.get_security_threats(),
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "hostname": platform.node()
        }


class Agent:
    """XML-RPC Agent that serves metrics to the collector."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9000):
        self.host = host
        self.port = port
        self.metrics_collector = MetricsCollector()
        self.server = None
        self._running = False

    def start(self):
        """Start the XML-RPC server."""
        try:
            self.server = ThreadedXMLRPCServer((self.host, self.port))
            self.server.register_instance(self)
            self.server.register_introspection_functions()

            logger.info(f"Agent started on {self.host}:{self.port}")
            logger.info(f"Platform: {platform.system()} {platform.release()}")

            self._running = True
            self.server.serve_forever()

        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            raise

    def stop(self):
        """Stop the XML-RPC server."""
        if self.server:
            logger.info("Stopping agent...")
            self._running = False
            self.server.shutdown()
            self.server.server_close()
            logger.info("Agent stopped")

    # XML-RPC exposed methods

    def get_metrics(self) -> Dict[str, Any]:
        """Get all system metrics (XML-RPC method)."""
        return self.metrics_collector.get_all_metrics()

    def get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature (XML-RPC method)."""
        return self.metrics_collector.get_cpu_temperature()

    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage (XML-RPC method)."""
        return self.metrics_collector.get_cpu_usage()

    def get_system_load(self) -> Dict[str, float]:
        """Get system load averages (XML-RPC method)."""
        return self.metrics_collector.get_system_load()

    def get_security_threats(self) -> List[Dict[str, Any]]:
        """Get security threats (XML-RPC method)."""
        return self.metrics_collector.get_security_threats()

    def ping(self) -> str:
        """Simple ping/pong method for connectivity test."""
        return "pong"

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "status": "running" if self._running else "stopped",
            "platform": platform.system(),
            "hostname": platform.node(),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Main entry point for the agent."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitoring Agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9000, help="Port to listen on")
    parser.add_argument("--log-level", default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")

    args = parser.parse_args()

    # Configure logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    agent = Agent(host=args.host, port=args.port)

    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        agent.stop()
    except Exception as e:
        logger.error(f"Agent error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
