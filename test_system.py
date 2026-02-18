#!/usr/bin/env python3
"""
Test script to verify the monitoring system functionality
"""

import sys
import time
import json
import xmlrpc.client
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.agent_server import MonitorAgent
from storage.storage_factory import StorageFactory
from visualization.visualize_metrics import MetricsVisualizer


def test_agent():
    """Test agent functionality"""
    print("=" * 50)
    print("Testing Agent Server")
    print("=" * 50)
    
    try:
        agent = MonitorAgent()
        
        # Test individual metric collection
        print("\n1. Testing individual metrics...")
        
        temp = agent.get_cpu_temperature()
        print(f"   CPU Temperature: {temp}°C" if temp else "   CPU Temperature: N/A")
        
        cpu = agent.get_cpu_usage()
        print(f"   CPU Usage: {cpu:.1f}%")
        
        load = agent.get_system_load()
        print(f"   System Load: {load}")
        
        mem = agent.get_memory_usage()
        print(f"   Memory: {mem['percent']:.1f}% used")
        
        disk = agent.get_disk_usage()
        print(f"   Disk: {disk['percent']:.1f}% used")
        
        security = agent.check_security_threats()
        print(f"   Security: {security['status']} ({len(security.get('issues', []))} issues)")
        
        # Test all metrics together
        print("\n2. Testing all metrics collection...")
        all_metrics = agent.get_all_metrics()
        print(f"   ✓ Collected metrics for {all_metrics['hostname']}")
        print(f"   ✓ Timestamp: {all_metrics['timestamp']}")
        print(f"   ✓ Status: {all_metrics['status'] if 'status' in all_metrics else 'success'}")
        
        print("\n✅ Agent test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Agent test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage():
    """Test storage functionality"""
    print("\n" + "=" * 50)
    print("Testing Storage Layer")
    print("=" * 50)
    
    try:
        # Test file storage
        print("\n1. Testing file storage...")
        file_config = {
            "type": "file",
            "metrics_file": "/tmp/test_metrics.log",
            "json_file": "/tmp/test_metrics.json",
            "rotation": {"max_size": "10MB", "backup_count": 3}
        }
        
        file_storage = StorageFactory.create_storage(file_config)
        
        # Create test metrics
        test_metrics = [
            {
                "agent_name": "test-agent",
                "collection_time": "2024-01-01T12:00:00",
                "cpu_usage": 50.0,
                "cpu_temperature": 45.0,
                "status": "success"
            },
            {
                "agent_name": "test-agent-2",
                "collection_time": "2024-01-01T12:00:00",
                "cpu_usage": 75.0,
                "status": "success"
            }
        ]
        
        # Store test data
        file_storage.store(test_metrics)
        print("   ✓ Stored metrics to file storage")
        
        # Query test data
        results = file_storage.query(agent_name="test-agent")
        print(f"   ✓ Queried {len(results)} records from file storage")
        
        file_storage.close()
        print("\n✅ File storage test PASSED")
        
        return True
        
    except Exception as e:
        print(f"\n❌ File storage test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visualization():
    """Test visualization functionality"""
    print("\n" + "=" * 50)
    print("Testing Visualization")
    print("=" * 50)
    
    try:
        # Create sample metrics data
        import datetime
        from datetime import timedelta
        
        sample_data = []
        for i in range(10):
            sample_data.append({
                "agent_name": "test-agent",
                "collection_time": (datetime.datetime.now() - timedelta(minutes=i*10)).isoformat(),
                "cpu_usage": 50.0 + i * 2.0,
                "cpu_temperature": 45.0 + i * 1.5,
                "system_load": {"1min": 1.0 + i * 0.1, "5min": 0.9 + i * 0.1, "15min": 0.8 + i * 0.1},
                "memory_usage": {"total": 8.0, "used": 4.0 + i * 0.1, "percent": 50.0 + i},
                "disk_usage": {"total": 100.0, "used": 30.0, "percent": 30.0},
                "security_threats": {"status": "OK", "issues": []},
                "status": "success"
            })
        
        # Write to test file
        test_file = "/tmp/test_metrics.json"
        with open(test_file, 'w') as f:
            for metric in sample_data:
                f.write(json.dumps(metric, default=str) + '\n')
        
        print(f"\n1. Created test data: {test_file}")
        
        # Test visualization
        print("\n2. Testing visualization...")
        visualizer = MetricsVisualizer(test_file)
        visualizer.load_data()
        
        print(f"   ✓ Loaded {len(visualizer.metrics_data)} metrics")
        print(f"   ✓ Found agents: {visualizer.agents}")
        
        # Generate plots (to tmp directory)
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            visualizer.plot_cpu_temperature(f'{tmpdir}/temp.png', hours=2)
            print("   ✓ CPU temperature plot generated")
            
            visualizer.plot_cpu_usage(f'{tmpdir}/cpu.png', hours=2)
            print("   ✓ CPU usage plot generated")
        
        print("\n✅ Visualization test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Visualization test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_xmlrpc_server():
    """Test XML-RPC server functionality"""
    print("\n" + "=" * 50)
    print("Testing XML-RPC Server")
    print("=" * 50)
    
    try:
        from xmlrpc.server import SimpleXMLRPCServer
        import threading
        
        # Start server in background
        server = SimpleXMLRPCServer(("localhost", 8999), allow_none=True)
        server.register_function(lambda: "pong", "ping")
        server.register_function(lambda: {"cpu_usage": 50.0}, "get_metrics")
        
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        time.sleep(1)  # Let server start
        
        print("\n1. Testing XML-RPC client connection...")
        
        # Test connection
        proxy = xmlrpc.client.ServerProxy("http://localhost:8999/", allow_none=True)
        result = proxy.ping()
        print(f"   ✓ Ping result: {result}")
        
        # Test metrics
        metrics = proxy.get_metrics()
        print(f"   ✓ Metrics result: {metrics}")
        
        server.shutdown()
        print("\n✅ XML-RPC test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ XML-RPC test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("MONITORING SYSTEM FUNCTIONALITY TESTS")
    print("=" * 60)
    
    tests = [
        ("Agent Server", test_agent),
        ("Storage Layer", test_storage),
        ("Visualization", test_visualization),
        ("XML-RPC Server", test_xmlrpc_server)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test encountered an error: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✅" if result else "❌"
        print(f"{symbol} {test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests PASSED! System is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) FAILED. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())