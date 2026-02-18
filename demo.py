#!/usr/bin/env python3
"""
Demo script for the monitoring system.
This script demonstrates all features without requiring actual agents.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.monitoring.storage import create_storage
from src.monitoring.agent import MetricsCollector
from src.monitoring.visualization import Visualizer
from src.monitoring.collector import ThresholdMonitor
import configparser


def demo_metrics_collection():
    """Demonstrate metrics collection."""
    print("\n" + "="*60)
    print("DEMO 1: Metrics Collection")
    print("="*60)
    
    collector = MetricsCollector()
    
    print("\nCollecting metrics from local system...")
    temp = collector.get_cpu_temperature()
    cpu = collector.get_cpu_usage()
    load = collector.get_system_load()
    memory = collector.get_memory_usage()
    disk = collector.get_disk_usage()
    threats = collector.get_security_threats()
    
    print(f"\nCPU Temperature: {temp}°C")
    print(f"CPU Usage: {cpu}%")
    print(f"System Load: {load}")
    print(f"Memory Usage: {memory.get('percent', 'N/A')}%")
    print(f"Disk Usage: {disk.get('percent', 'N/A')}%")
    print(f"Security Threats: {len(threats)} found")
    
    if threats:
        for threat in threats[:3]:  # Show first 3
            print(f"  - {threat.get('type', 'Unknown')}: {threat.get('description', 'N/A')}")
    
    return {
        "cpu_temperature": temp,
        "cpu_usage": cpu,
        "system_load": load,
        "memory": memory,
        "disk": disk,
        "security_threats": threats,
        "timestamp": datetime.now().isoformat()
    }


def demo_storage(metrics):
    """Demonstrate storage functionality."""
    print("\n" + "="*60)
    print("DEMO 2: Storage Backend")
    print("="*60)
    
    # Test log storage
    print("\nTesting Log Storage...")
    log_storage = create_storage('log')
    log_storage.save_metric("demo-agent", "cpu_temperature", metrics["cpu_temperature"])
    log_storage.save_metric("demo-agent", "cpu_usage", metrics["cpu_usage"])
    log_storage.save_metric("demo-agent", "system_load", 
                           {"1min": metrics["system_load"]["1min"]})
    
    retrieved = log_storage.get_metrics("demo-agent", "cpu_temperature")
    print(f"✓ Stored and retrieved {len(retrieved)} temperature metric(s)")
    
    # Test SQLite storage
    print("\nTesting SQLite Storage...")
    sqlite_storage = create_storage('sqlite')
    sqlite_storage.save_metric("demo-agent", "cpu_temperature", metrics["cpu_temperature"])
    sqlite_storage.save_metric("demo-agent", "cpu_usage", metrics["cpu_usage"])
    
    retrieved = sqlite_storage.get_metrics("demo-agent", "cpu_usage")
    print(f"✓ Stored and retrieved {len(retrieved)} CPU usage metric(s)")
    
    return log_storage, sqlite_storage


def demo_thresholds(metrics):
    """Demonstrate threshold monitoring."""
    print("\n" + "="*60)
    print("DEMO 3: Threshold Monitoring")
    print("="*60)
    
    config = configparser.ConfigParser()
    config['thresholds'] = {
        'cpu_temp_warning': '70',
        'cpu_temp_critical': '85',
        'load_warning': '2.0',
        'load_critical': '4.0',
        'cpu_usage_warning': '80',
        'cpu_usage_critical': '95'
    }
    
    monitor = ThresholdMonitor(config)
    alerts = monitor.check_metrics(metrics, "demo-agent")
    
    print(f"\nGenerated {len(alerts)} alert(s):")
    for alert in alerts:
        print(f"  [{alert['severity'].upper()}] {alert['message']}")
        print(f"    Type: {alert['type']}, Value: {alert['value']}")
    
    return alerts


def demo_visualization(storage):
    """Demonstrate visualization generation."""
    print("\n" + "="*60)
    print("DEMO 4: Visualization")
    print("="*60)
    
    # Create a config for visualization
    config = configparser.ConfigParser()
    config['visualization'] = {
        'output_dir': './graphs',
        'graph_width': '10',
        'graph_height': '6'
    }
    config['storage'] = {'backend': 'log'}
    
    visualizer = Visualizer.__new__(Visualizer)
    visualizer.config = config
    visualizer.output_dir = "./graphs"
    visualizer.graph_width = 10
    visualizer.graph_height = 6
    visualizer._init_storage = lambda: storage
    
    # Ensure graphs directory exists
    os.makedirs("./graphs", exist_ok=True)
    
    print("\nGenerating graphs for demo-agent...")
    
    # Create sample data points for demo
    now = datetime.now()
    for i in range(10):
        temp = 60 + (i * 0.5)
        cpu = 20 + (i * 2)
        load = 1.0 + (i * 0.1)
        
        timestamp = now - timedelta(minutes=i*10)
        
        storage.save_metric("demo-agent", "cpu_temperature", temp, timestamp)
        storage.save_metric("demo-agent", "cpu_usage", cpu, timestamp)
        storage.save_metric("demo-agent", "system_load", 
                           {"1min": load, "5min": load*0.8, "15min": load*0.6}, timestamp)
    
    # Generate overview graph
    try:
        # Note: We'll just simulate graph generation here as it requires matplotlib backend setup
        print("✓ Created sample metric data")
        print("✓ Note: Full graph generation requires matplotlib setup")
        print(f"✓ Graphs would be saved to: {visualizer.output_dir}")
    except Exception as e:
        print(f"Note: Graph generation demo (actual graphs require full matplotlib): {e}")


def demo_agent_simulation():
    """Simulate XML-RPC agent communication."""
    print("\n" + "="*60)
    print("DEMO 5: XML-RPC Communication Simulation")
    print("="*60)
    
    print("\nIn a real deployment:")
    print("1. Agent runs on System B: python -m src.monitoring.agent")
    print("2. Agent listens on XML-RPC port (default 9000)")
    print("3. Collector polls agent: xmlrpc.client.ServerProxy")
    print("\nSimulated XML-RPC call:")
    print("  proxy = xmlrpc.client.ServerProxy('http://localhost:9000/')")
    print("  metrics = proxy.get_metrics()")
    
    # Simulate what would happen
    collector = MetricsCollector()
    simulated_metrics = collector.get_all_metrics()
    
    print("\n✓ Simulated metrics received:")
    print(f"  - CPU Temperature: {simulated_metrics.get('cpu_temperature')}°C")
    print(f"  - CPU Usage: {simulated_metrics.get('cpu_usage')}%")
    print(f"  - System Load: {simulated_metrics.get('system_load', {}).get('1min', 'N/A')}")
    print(f"  - Platform: {simulated_metrics.get('platform')}")
    print(f"  - Hostname: {simulated_metrics.get('hostname')}")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("PYTHON MONITORING SYSTEM - DEMONSTRATION")
    print("="*60)
    print("\nThis demo shows all major features of the monitoring system.")
    print("No external dependencies or network connections required.")
    
    try:
        # Demo 1: Collect metrics
        metrics = demo_metrics_collection()
        
        # Demo 2: Storage
        log_storage, sqlite_storage = demo_storage(metrics)
        
        # Demo 3: Threshold monitoring
        alerts = demo_thresholds(metrics)
        
        # Demo 4: Visualization
        demo_visualization(log_storage)
        
        # Demo 5: Agent simulation
        demo_agent_simulation()
        
        # Summary
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("✓ Multi-platform metrics collection")
        print("✓ Flexible storage backends (Log, SQLite)")
        print("✓ Configurable threshold monitoring")
        print("✓ Alert generation")
        print("✓ XML-RPC communication")
        print("✓ Visualization preparation")
        
        print("\nNext Steps:")
        print("1. Set up agents on systems you want to monitor")
        print("2. Configure agents in config/config.ini")
        print("3. Start the collector: python -m src.monitoring.collector")
        print("4. Generate graphs: python -m src.monitoring.visualization")
        print("5. Read docs/README.md for full documentation")
        
        # Cleanup
        print("\nCleaning up demo data...")
        import shutil
        if os.path.exists("./data"):
            shutil.rmtree("./data")
        if os.path.exists("./metrics.db"):
            os.remove("./metrics.db")
        if os.path.exists("./graphs"):
            shutil.rmtree("./graphs")
        print("✓ Demo complete!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())