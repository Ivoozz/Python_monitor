#!/usr/bin/env python3
"""
Quick demo of the monitoring system functionality
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("PYTHON MONITORING SYSTEM - QUICK DEMO")
print("=" * 70)

# Test 1: Agent
print("\n[1/4] Testing Agent Server...")
try:
    from agent.agent_server import MonitorAgent
    agent = MonitorAgent()
    
    # Collect metrics
    metrics = agent.get_all_metrics()
    print(f"  ✓ Agent initialized successfully")
    print(f"  ✓ Hostname: {metrics['hostname']}")
    print(f"  ✓ CPU Temperature: {metrics.get('cpu_temperature', 'N/A')}")
    print(f"  ✓ CPU Usage: {metrics.get('cpu_usage', 0):.1f}%")
    print(f"  ✓ System Load: {metrics.get('system_load', {})}")
    print(f"  ✓ Security Status: {metrics.get('security_threats', {}).get('status', 'UNKNOWN')}")
except Exception as e:
    print(f"  ✗ Agent test failed: {e}")

# Test 2: Storage
print("\n[2/4] Testing Storage Layer...")
try:
    from storage.storage_factory import StorageFactory
    
    config = {
        "type": "file",
        "metrics_file": "/tmp/demo_metrics.log",
        "json_file": "/tmp/demo_metrics.json"
    }
    
    storage = StorageFactory.create_storage(config)
    
    # Store sample data
    sample_data = [
        {
            "agent_name": "demo-agent",
            "collection_time": "2024-01-01T12:00:00",
            "cpu_usage": 50.0,
            "cpu_temperature": 45.0,
            "status": "success"
        }
    ]
    
    storage.store(sample_data)
    print(f"  ✓ File storage working")
    print(f"  ✓ Sample data stored")
    
    storage.close()
except Exception as e:
    print(f"  ✗ Storage test failed: {e}")

# Test 3: XML-RPC
print("\n[3/4] Testing XML-RPC Server...")
try:
    from xmlrpc.server import SimpleXMLRPCServer
    import threading
    
    server = SimpleXMLRPCServer(("localhost", 8998), allow_none=True)
    server.register_function(lambda: "PONG", "ping")
    server.register_function(lambda: {"status": "ok"}, "get_status")
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    time.sleep(0.5)  # Let server start
    
    import xmlrpc.client
    proxy = xmlrpc.client.ServerProxy("http://localhost:8998/", allow_none=True)
    
    result = proxy.ping()
    print(f"  ✓ XML-RPC server started")
    print(f"  ✓ Ping response: {result}")
    
    status = proxy.get_status()
    print(f"  ✓ Status response: {status}")
    
    server.shutdown()
    print(f"  ✓ XML-RPC test passed")
    
except Exception as e:
    print(f"  ✗ XML-RPC test failed: {e}")

# Test 4: Visualization
print("\n[4/4] Testing Visualization...")
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    # Create a simple test plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([1, 2, 3, 4, 5], [1, 4, 2, 5, 3])
    ax.set_title('Test Plot')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    
    plt.savefig('/tmp/test_plot.png', dpi=100, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Matplotlib available")
    print(f"  ✓ Test plot created: /tmp/test_plot.png")
    
except Exception as e:
    print(f"  ✗ Visualization test failed: {e}")

print("\n" + "=" * 70)
print("DEMO COMPLETE")
print("=" * 70)
print("\nTo start the actual system:")
print("1. Terminal 1: python3 agent/agent_server.py")
print("2. Terminal 2: python3 collector/collector.py")
print("3. Terminal 3: python3 visualization/visualize_metrics.py --plot all")
print("\nFor full documentation, see: docs/README.md")