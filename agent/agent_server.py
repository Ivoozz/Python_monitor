#!/usr/bin/env python3
"""
XML-RPC Agent Server for System Monitoring
Runs on System B and exposes system metrics via XML-RPC
"""

import sys
import logging
import subprocess
import platform
import xmlrpc.client
import socket
from datetime import datetime
from typing import Dict, Any, Optional
import re

logger = logging.getLogger('AgentServer')


class MonitorAgent:
    """Agent that collects system metrics and exposes them via XML-RPC"""
    
    def __init__(self, config_path: str = '/home/engine/project/config/agent_config.json'):
        """Initialize the monitor agent"""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.hostname = socket.gethostname()
        logger.info(f"Agent initialized on host: {self.hostname}")
    
    def setup_logging(self):
        """Setup logging with configurable file path"""
        import os
        
        # Determine log file path
        log_file = self.config.get('log_file')
        
        if not log_file:
            # Try /var/log/ first, but catch permission errors
            try:
                log_file = '/var/log/monitor_agent.log'
                # Test if we can write to /var/log/
                with open('/tmp/test_write', 'w') as f:
                    f.write('test')
                os.remove('/tmp/test_write')
            except:
                # Fallback to user directory
                log_file = './logs/monitor_agent.log'
        
        # Create directory if needed
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except:
                # Final fallback
                log_file = './monitor_agent.log'
        
        # Configure logging if not already configured
        if not logger.handlers:
            try:
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        logging.StreamHandler(sys.stdout)
                    ]
                )
            except:
                # Last resort: console only
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(sys.stdout)
                    ]
                )
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load agent configuration"""
        try:
            import json
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}. Using defaults.")
            return {
                "host": "0.0.0.0",
                "port": 8000,
                "check_interval": 30
            }
    
    def get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature in Celsius"""
        try:
            system = platform.system().lower()
            
            if system == "linux":
                # Try multiple methods to get temperature
                temp = self._get_linux_temperature()
                if temp is not None:
                    return temp
                
                # Try using vcgencmd (Raspberry Pi)
                try:
                    output = subprocess.check_output(['vcgencmd', 'measure_temp'], 
                                                   universal_newlines=True)
                    temp_str = output.strip().split('=')[1].split("'")[0]
                    return float(temp_str)
                except:
                    pass
                    
                # Try sensors command
                try:
                    output = subprocess.check_output(['sensors'], 
                                                   universal_newlines=True)
                    # Parse sensors output for temperature
                    for line in output.split('\n'):
                        if 'Core' in line or 'temp' in line.lower():
                            match = re.search(r'\+([0-9.]+)°C', line)
                            if match:
                                return float(match.group(1))
                except:
                    pass
            
            elif system == "darwin":  # macOS
                try:
                    output = subprocess.check_output(
                        ['sysctl', '-n', 'machdep.xcpm.cpu_thermal_state'],
                        universal_newlines=True
                    )
                    # macOS doesn't provide direct temperature, return None
                    logger.info("macOS detected - temperature sensor not available via standard APIs")
                    return None
                except:
                    pass
            
            elif system == "windows":
                logger.info("Windows detected - temperature requires WMI or third-party tools")
                return None
            
            logger.warning("Could not retrieve CPU temperature - sensor not available")
            return None
            
        except Exception as e:
            logger.error(f"Error getting CPU temperature: {e}")
            return None
    
    def _get_linux_temperature(self) -> Optional[float]:
        """Get temperature on Linux systems"""
        temp_files = [
            '/sys/class/thermal/thermal_zone0/temp',
            '/sys/class/thermal/thermal_zone1/temp',
            '/sys/class/hwmon/hwmon0/temp1_input',
            '/sys/class/hwmon/hwmon1/temp1_input'
        ]
        
        for temp_file in temp_files:
            try:
                with open(temp_file, 'r') as f:
                    temp_millidegrees = int(f.read().strip())
                    return temp_millidegrees / 1000.0
            except:
                continue
        
        return None
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            # Use a more reliable method
            output = subprocess.check_output(
                ['python3', '-c', 
                 'import psutil; print(psutil.cpu_percent(interval=1))'],
                universal_newlines=True
            )
            return float(output.strip())
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            # Fallback to top
            try:
                output = subprocess.check_output(['top', '-bn1'], 
                                               universal_newlines=True)
                for line in output.split('\n'):
                    if 'Cpu(s)' in line:
                        match = re.search(r'([0-9.]+)%us', line)
                        if match:
                            return float(match.group(1))
            except:
                pass
            return 0.0
    
    def get_system_load(self) -> Dict[str, float]:
        """Get system load averages"""
        try:
            load1, load5, load15 = None, None, None
            
            if platform.system().lower() == "windows":
                # Windows doesn't have load average
                return {"1min": 0.0, "5min": 0.0, "15min": 0.0}
            
            try:
                import psutil
                load1, load5, load15 = psutil.getloadavg()
            except:
                # Fallback to uptime command
                output = subprocess.check_output(['uptime'], universal_newlines=True)
                parts = output.split('load average:')[1].strip().split(',')
                load1 = float(parts[0].strip())
                load5 = float(parts[1].strip())
                load15 = float(parts[2].strip())
            
            return {"1min": load1, "5min": load5, "15min": load15}
        except Exception as e:
            logger.error(f"Error getting system load: {e}")
            return {"1min": 0.0, "5min": 0.0, "15min": 0.0}
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                "total": mem.total / (1024**3),  # GB
                "available": mem.available / (1024**3),  # GB
                "used": mem.used / (1024**3),  # GB
                "percent": mem.percent
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {"total": 0.0, "available": 0.0, "used": 0.0, "percent": 0.0}
    
    def check_security_threats(self) -> Dict[str, Any]:
        """Check for potential security threats"""
        threats = {
            "status": "OK",
            "issues": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check for suspicious processes
            suspicious_processes = self._check_suspicious_processes()
            if suspicious_processes:
                threats["issues"].extend(suspicious_processes)
            
            # Check for unauthorized SSH attempts
            ssh_issues = self._check_ssh_attempts()
            if ssh_issues:
                threats["issues"].extend(ssh_issues)
            
            # Check for high network activity
            network_issues = self._check_network_activity()
            if network_issues:
                threats["issues"].extend(network_issues)
            
            if threats["issues"]:
                threats["status"] = "WARNING"
            
        except Exception as e:
            logger.error(f"Error checking security threats: {e}")
            threats["issues"].append(f"Security check error: {str(e)}")
            threats["status"] = "ERROR"
        
        return threats
    
    def _check_suspicious_processes(self) -> list:
        """Check for suspicious processes"""
        issues = []
        try:
            import psutil
            
            # Check for processes running from suspicious locations
            suspicious_paths = ['/tmp/', '/var/tmp/', '/dev/shm/']
            
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                try:
                    exe = proc.info.get('exe')
                    if exe and any(exe.startswith(path) for path in suspicious_paths):
                        issues.append(f"Suspicious process: {proc.info['name']} (PID: {proc.info['pid']}) from {exe}")
                    
                    # Check for processes with no executable path
                    if exe is None and proc.info.get('cmdline'):
                        issues.append(f"Process with no executable path: {proc.info['name']} (PID: {proc.info['pid']})")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Error checking processes: {e}")
        
        return issues
    
    def _check_ssh_attempts(self) -> list:
        """Check for failed SSH login attempts"""
        issues = []
        try:
            # Check /var/log/auth.log for failed SSH attempts (Linux)
            if platform.system().lower() == "linux":
                try:
                    result = subprocess.run(
                        ['tail', '-n', '100', '/var/log/auth.log'],
                        capture_output=True, text=True, timeout=5
                    )
                    failed_count = 0
                    for line in result.stdout.split('\n'):
                        if 'Failed password' in line:
                            failed_count += 1
                    
                    if failed_count > 10:  # Threshold for suspicious activity
                        issues.append(f"High number of failed SSH attempts: {failed_count} in recent logs")
                except:
                    pass
        except Exception as e:
            logger.error(f"Error checking SSH attempts: {e}")
        
        return issues
    
    def _check_network_activity(self) -> list:
        """Check for unusual network activity"""
        issues = []
        try:
            import psutil
            
            connections = psutil.net_connections(kind='inet')
            listening_ports = len([c for c in connections if c.status == 'LISTEN'])
            
            # Alert if too many listening ports (potential backdoor)
            if listening_ports > 100:
                issues.append(f"Unusually high number of listening ports: {listening_ports}")
            
            # Check for established connections to suspicious ports
            suspicious_ports = [1234, 4444, 5555, 6666, 7777, 8888, 9999]
            established_conns = [c for c in connections if c.status == 'ESTABLISHED']
            
            for conn in established_conns:
                if conn.laddr and conn.laddr.port in suspicious_ports:
                    issues.append(f"Connection on suspicious port: {conn.laddr.port}")
                    
        except Exception as e:
            logger.error(f"Error checking network activity: {e}")
        
        return issues
    
    def get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage statistics"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                "total": disk.total / (1024**3),  # GB
                "used": disk.used / (1024**3),  # GB
                "free": disk.free / (1024**3),  # GB
                "percent": (disk.used / disk.total) * 100
            }
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {"total": 0.0, "used": 0.0, "free": 0.0, "percent": 0.0}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all system metrics"""
        metrics = {
            "hostname": self.hostname,
            "timestamp": datetime.now().isoformat(),
            "cpu_temperature": self.get_cpu_temperature(),
            "cpu_usage": self.get_cpu_usage(),
            "system_load": self.get_system_load(),
            "memory_usage": self.get_memory_usage(),
            "disk_usage": self.get_disk_usage(),
            "security_threats": self.check_security_threats()
        }
        
        logger.info(f"Collected metrics for {self.hostname}")
        return metrics
    
    # XML-RPC methods
    def ping(self) -> str:
        """Simple ping method for connectivity test"""
        return f"PONG from {self.hostname}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all system metrics"""
        return self.get_all_metrics()
    
    def get_temperature(self) -> Optional[float]:
        """Get only CPU temperature"""
        return self.get_cpu_temperature()
    
    def get_cpu(self) -> Dict[str, float]:
        """Get CPU-related metrics"""
        return {
            "usage": self.get_cpu_usage(),
            "load": self.get_system_load()
        }
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get security status"""
        return self.check_security_threats()


def main():
    """Main entry point for the agent server"""
    from xmlrpc.server import SimpleXMLRPCServer
    import signal
    import json
    
    # Load configuration
    agent = MonitorAgent()
    
    # Server configuration
    host = agent.config.get("host", "0.0.0.0")
    port = agent.config.get("port", 8000)
    
    # Create server
    server = SimpleXMLRPCServer((host, port), allow_none=True)
    server.register_instance(agent)
    
    logger.info(f"Starting XML-RPC Agent Server on {host}:{port}")
    logger.info(f"Agent accessible at: http://{host}:{port}")
    
    # Handle shutdown gracefully
    def signal_handler(signum, frame):
        logger.info("Shutting down agent server...")
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print(f"Agent Server running on {host}:{port}")
        print(f"Press Ctrl+C to stop")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        logger.info("Agent server stopped")


if __name__ == "__main__":
    main()