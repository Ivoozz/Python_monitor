#!/usr/bin/env python3
"""
File-based Storage with Log Rotation
Stores metrics in log files with automatic rotation
"""

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import List, Dict, Any
import threading


class FileStorage:
    """Storage implementation using rotating log files"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize file storage"""
        self.config = config
        
        # Setup main log file for storage operations
        log_file = config.get('metrics_file', '/var/log/metrics_data.log')
        
        # Parse rotation settings
        max_size_str = config.get('rotation', {}).get('max_size', '10MB')
        backup_count = config.get('rotation', {}).get('backup_count', 5)
        
        # Convert size string to bytes
        max_bytes = self._parse_size(max_size_str)
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create log directory: {e}")
                log_file = './metrics_data.log'  # Fallback to current directory
        
        # Setup rotating file handler
        self.logger = logging.getLogger('FileStorage')
        self.handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        self.handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.INFO)
        
        # Also create a JSON file for machine-readable storage
        self.json_file = config.get('json_file', '/var/log/metrics_data.json')
        self.json_dir = os.path.dirname(self.json_file)
        if self.json_dir and not os.path.exists(self.json_dir):
            try:
                os.makedirs(self.json_dir, exist_ok=True)
            except:
                self.json_file = './metrics_data.json'
        
        # Thread safety
        self._lock = threading.Lock()
        
        self.logger.info(f"File storage initialized: {log_file}, max size: {max_size_str}")
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper().strip()
        
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3
        }
        
        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                try:
                    value = float(size_str[:-len(unit)])
                    return int(value * multiplier)
                except ValueError:
                    break
        
        return 10 * 1024 * 1024  # Default: 10MB
    
    def store(self, metrics_list: List[Dict[str, Any]]):
        """Store metrics to file"""
        with self._lock:
            for metrics in metrics_list:
                # Format for human-readable log
                self._store_human_readable(metrics)
                
                # Store in JSON format
                self._store_json(metrics)
    
    def _store_human_readable(self, metrics: Dict[str, Any]):
        """Store metrics in human-readable format"""
        agent_name = metrics.get('agent_name', 'unknown')
        timestamp = metrics.get('collection_time', datetime.now().isoformat())
        status = metrics.get('status', 'unknown')
        
        if status == 'error':
            error = metrics.get('error', 'Unknown error')
            self.logger.warning(f"[{agent_name}] ERROR: {error}")
            return
        
        # Build metric string
        lines = [f"Agent: {agent_name} | Time: {timestamp}"]
        
        if 'cpu_temperature' in metrics:
            temp = metrics['cpu_temperature']
            if temp is None:
                lines.append("  CPU Temperature: N/A (sensor not available)")
            else:
                lines.append(f"  CPU Temperature: {temp:.1f}°C")
        
        if 'cpu_usage' in metrics:
            lines.append(f"  CPU Usage: {metrics['cpu_usage']:.1f}%")
        
        if 'system_load' in metrics:
            load = metrics['system_load']
            lines.append(f"  System Load: 1min={load['1min']:.2f}, 5min={load['5min']:.2f}, 15min={load['15min']:.2f}")
        
        if 'memory_usage' in metrics:
            mem = metrics['memory_usage']
            lines.append(f"  Memory: {mem['used']:.1f}GB / {mem['total']:.1f}GB ({mem['percent']:.1f}%)")
        
        if 'disk_usage' in metrics:
            disk = metrics['disk_usage']
            lines.append(f"  Disk: {disk['used']:.1f}GB / {disk['total']:.1f}GB ({disk['percent']:.1f}%)")
        
        if 'security_threats' in metrics:
            sec = metrics['security_threats']
            lines.append(f"  Security: {sec.get('status', 'UNKNOWN')}")
            if sec.get('issues'):
                for issue in sec['issues'][:3]:  # Limit to first 3 issues
                    lines.append(f"    - {issue}")
        
        if 'alerts' in metrics and metrics['alerts']:
            lines.append(f"  ALERTS ({len(metrics['alerts'])}):")
            for alert in metrics['alerts']:
                lines.append(f"    [{alert['severity']}] {alert['message']}")
        
        # Write to log
        for line in lines:
            self.logger.info(line)
    
    def _store_json(self, metrics: Dict[str, Any]):
        """Store metrics in JSON format for machine parsing"""
        try:
            with open(self.json_file, 'a') as f:
                # Write each metric as a separate JSON line (JSON Lines format)
                json_line = json.dumps(metrics, default=str)
                f.write(json_line + '\n')
        except Exception as e:
            self.logger.error(f"Error writing JSON: {e}")
    
    def query(self, agent_name: str = None, start_time: str = None, end_time: str = None) -> List[Dict[str, Any]]:
        """Query stored metrics (for future use)"""
        # This is a placeholder for more advanced querying
        results = []
        
        if not os.path.exists(self.json_file):
            return results
        
        try:
            with open(self.json_file, 'r') as f:
                for line in f:
                    try:
                        metric = json.loads(line.strip())
                        
                        # Apply filters
                        if agent_name and metric.get('agent_name') != agent_name:
                            continue
                        
                        if start_time and metric.get('collection_time', '') < start_time:
                            continue
                        
                        if end_time and metric.get('collection_time', '') > end_time:
                            continue
                        
                        results.append(metric)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            self.logger.error(f"Error querying metrics: {e}")
        
        return results
    
    def close(self):
        """Close storage and cleanup"""
        if hasattr(self, 'handler'):
            self.handler.close()
            self.logger.removeHandler(self.handler)
