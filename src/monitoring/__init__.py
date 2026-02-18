"""
Monitoring System Package

This package provides a complete monitoring solution using XML-RPC to collect
and visualize system metrics from remote agents.

Components:
- agent: Runs on monitored systems and exposes metrics via XML-RPC
- collector: Runs on monitoring system and polls agents
- storage: Abstract storage layer supporting file and MySQL backends
- visualization: Generates graphs from collected metrics

Usage:
    # Start agent on monitored system
    python -m src.monitoring.agent --host 0.0.0.0 --port 9000
    
    # Start collector on monitoring system
    python -m src.monitoring.collector --config config/config.ini
    
    # Generate visualizations
    python -m src.monitoring.visualization --config config/config.ini
"""

__version__ = "1.0.0"
__author__ = "Monitoring System"

from .storage import (
    StorageBackend,
    LogStorage,
    MySQLStorage,
    SQLiteStorage,
    create_storage
)

from .agent import Agent, MetricsCollector
from .collector import Collector, AgentConnection, ThresholdMonitor
from .visualization import Visualizer

__all__ = [
    "Agent",
    "MetricsCollector", 
    "Collector",
    "AgentConnection",
    "ThresholdMonitor",
    "StorageBackend",
    "LogStorage",
    "MySQLStorage",
    "SQLiteStorage",
    "Visualizer",
    "create_storage"
]