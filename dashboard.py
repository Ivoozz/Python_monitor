#!/usr/bin/env python3
"""
Flask Web Dashboard for System Monitoring
Provides auto-refreshing UI, device management, and live metrics/graphs
"""

import os
import json
import logging
import xmlrpc.client
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, render_template, request, jsonify
from threading import Lock

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Dashboard')

app = Flask(__name__)

# Configuration - use environment variables or defaults
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICES_FILE = os.environ.get('DEVICES_FILE', os.path.join(PROJECT_DIR, 'config', 'dashboard_devices.json'))
METRICS_FILE = os.environ.get('METRICS_FILE', os.path.join(PROJECT_DIR, 'storage', 'latest_metrics.json'))
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '5'))  # seconds
AGENT_TIMEOUT = int(os.environ.get('AGENT_TIMEOUT', '10'))  # seconds

# Ensure directories exist
os.makedirs(os.path.dirname(DEVICES_FILE), exist_ok=True)
os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)

# Thread-safe device storage
devices_lock = Lock()
devices: List[Dict[str, Any]] = []
metrics_cache: Dict[str, Any] = {}
metrics_cache_lock = Lock()


class DeviceManager:
    """Manages monitored devices configuration"""

    def __init__(self, devices_file: str):
        self.devices_file = devices_file
        self.devices = []
        self.load_devices()

    def load_devices(self):
        """Load devices from JSON file"""
        with devices_lock:
            try:
                if os.path.exists(self.devices_file):
                    with open(self.devices_file, 'r') as f:
                        self.devices = json.load(f)
                    logger.info(f"Loaded {len(self.devices)} devices from {self.devices_file}")
                else:
                    self.devices = []
                    self.save_devices()
            except Exception as e:
                logger.error(f"Error loading devices: {e}")
                self.devices = []

    def save_devices(self):
        """Save devices to JSON file"""
        try:
            # Atomic write
            temp_file = self.devices_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
            os.rename(temp_file, self.devices_file)
            logger.info(f"Saved {len(self.devices)} devices to {self.devices_file}")
        except Exception as e:
            logger.error(f"Error saving devices: {e}")

    def add_device(self, name: str, host: str, port: int) -> bool:
        """Add a new device to monitor"""
        with devices_lock:
            # Check for duplicates
            for device in self.devices:
                if device['host'] == host and device['port'] == port:
                    logger.warning(f"Device {host}:{port} already exists")
                    return False
                if device['name'] == name:
                    logger.warning(f"Device name '{name}' already exists")
                    return False

            self.devices.append({
                'name': name,
                'host': host,
                'port': port,
                'added_at': datetime.now().isoformat(),
                'enabled': True
            })
            self.save_devices()
            logger.info(f"Added device: {name} ({host}:{port})")
            return True

    def remove_device(self, name: str) -> bool:
        """Remove a device from monitoring"""
        with devices_lock:
            original_length = len(self.devices)
            self.devices = [d for d in self.devices if d['name'] != name]
            if len(self.devices) < original_length:
                self.save_devices()
                logger.info(f"Removed device: {name}")
                return True
            return False

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices"""
        with devices_lock:
            return self.devices.copy()

    def update_device(self, name: str, enabled: bool) -> bool:
        """Enable/disable a device"""
        with devices_lock:
            for device in self.devices:
                if device['name'] == name:
                    device['enabled'] = enabled
                    self.save_devices()
                    logger.info(f"Updated device {name}: enabled={enabled}")
                    return True
            return False


class MetricsCollector:
    """Collects metrics from monitored devices"""

    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self.timeout = AGENT_TIMEOUT

    def collect_from_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics from a single device"""
        if not device.get('enabled', True):
            return {
                'name': device['name'],
                'status': 'disabled',
                'error': 'Device is disabled'
            }

        try:
            url = f"http://{device['host']}:{device['port']}"
            proxy = xmlrpc.client.ServerProxy(url, allow_none=True)
            
            # Test connection
            ping_result = proxy.ping()
            
            # Get metrics
            metrics = proxy.get_metrics()
            
            # Add metadata
            metrics['device_name'] = device['name']
            metrics['status'] = 'success'
            metrics['collection_time'] = datetime.now().isoformat()
            
            return metrics
            
        except xmlrpc.client.Fault as e:
            return {
                'name': device['name'],
                'status': 'error',
                'error': f"XML-RPC fault: {e.faultString}",
                'collection_time': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'name': device['name'],
                'status': 'error',
                'error': str(e),
                'collection_time': datetime.now().isoformat()
            }

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all enabled devices"""
        devices = self.device_manager.get_devices()
        results = {
            'timestamp': datetime.now().isoformat(),
            'devices': [],
            'summary': {
                'total': len(devices),
                'success': 0,
                'error': 0,
                'disabled': 0
            }
        }

        for device in devices:
            result = self.collect_from_device(device)
            results['devices'].append(result)
            
            if result.get('status') == 'success':
                results['summary']['success'] += 1
            elif result.get('status') == 'error':
                results['summary']['error'] += 1
            else:
                results['summary']['disabled'] += 1

        # Update cache
        with metrics_cache_lock:
            metrics_cache.update(results)
        
        # Persist latest metrics
        self.save_metrics(results)
        
        return results

    def save_metrics(self, metrics: Dict[str, Any]):
        """Save latest metrics to file for persistence"""
        try:
            temp_file = METRICS_FILE + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            os.rename(temp_file, METRICS_FILE)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")


# Initialize managers
device_manager = DeviceManager(DEVICES_FILE)
metrics_collector = MetricsCollector(device_manager)


# Flask Routes

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html', 
                         poll_interval=POLL_INTERVAL,
                         devices=device_manager.get_devices())


@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get list of all devices"""
    devices = device_manager.get_devices()
    return jsonify({'devices': devices})


@app.route('/api/devices', methods=['POST'])
def add_device():
    """Add a new device"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'host' not in data or 'port' not in data:
        return jsonify({'error': 'Missing required fields: name, host, port'}), 400
    
    try:
        name = data['name'].strip()
        host = data['host'].strip()
        port = int(data['port'])
        
        if port < 1 or port > 65535:
            return jsonify({'error': 'Port must be between 1 and 65535'}), 400
        
        if not name or not host:
            return jsonify({'error': 'Name and host cannot be empty'}), 400
        
        success = device_manager.add_device(name, host, port)
        if success:
            return jsonify({'success': True, 'message': f'Device {name} added successfully'})
        else:
            return jsonify({'error': 'Device already exists'}), 400
    
    except ValueError:
        return jsonify({'error': 'Port must be a number'}), 400
    except Exception as e:
        logger.error(f"Error adding device: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/devices/<name>', methods=['DELETE'])
def remove_device(name):
    """Remove a device"""
    success = device_manager.remove_device(name)
    if success:
        return jsonify({'success': True, 'message': f'Device {name} removed successfully'})
    else:
        return jsonify({'error': 'Device not found'}), 404


@app.route('/api/devices/<name>/toggle', methods=['POST'])
def toggle_device(name):
    """Enable/disable a device"""
    data = request.get_json() or {}
    enabled = data.get('enabled', True)
    success = device_manager.update_device(name, enabled)
    if success:
        return jsonify({'success': True, 'message': f'Device {name} updated'})
    else:
        return jsonify({'error': 'Device not found'}), 404


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get latest metrics from all devices"""
    metrics = metrics_collector.collect_all_metrics()
    return jsonify(metrics)


@app.route('/api/metrics/cache', methods=['GET'])
def get_cached_metrics():
    """Get cached metrics without collecting"""
    with metrics_cache_lock:
        if not metrics_cache:
            return jsonify({'error': 'No metrics available yet'}), 404
        return jsonify(metrics_cache.copy())


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'devices_count': len(device_manager.get_devices())
    })


def main():
    """Main entry point"""
    # Load any existing devices
    device_manager.load_devices()
    
    # Initial metrics collection
    logger.info("Performing initial metrics collection...")
    metrics_collector.collect_all_metrics()
    
    # Start Flask app
    host = os.environ.get('DASHBOARD_HOST', '0.0.0.0')
    port = int(os.environ.get('DASHBOARD_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Flask dashboard on {host}:{port}")
    logger.info(f"Dashboard URL: http://{host}:{port}")
    
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
