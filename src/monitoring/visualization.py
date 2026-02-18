"""
Visualization module for monitoring data.
Generates graphs using Matplotlib and Seaborn.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.monitoring.storage import create_storage, LogStorage


class Visualizer:
    """Generates visualizations from monitoring data."""

    def __init__(self, config_path: str = "config/config.ini"):
        self.config = self._load_config(config_path)
        self.output_dir = self.config.get("visualization", "output_dir", 
                                          fallback="/var/log/monitoring/graphs")
        self.graph_width = float(self.config.get("visualization", "graph_width", fallback=12))
        self.graph_height = float(self.config.get("visualization", "graph_height", fallback=8))
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (self.graph_width, self.graph_height)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_config(self, config_path: str):
        """Load configuration."""
        import configparser
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            config.read(config_path)
        else:
            alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_path)
            if os.path.exists(alt_path):
                config.read(alt_path)
        return config

    def _init_storage(self):
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
            log_dir = os.path.dirname(log_dir) if log_dir else "/var/log/monitoring"
            return create_storage("log", log_dir=f"{log_dir}/data")

    def generate_all_graphs(self, hours: int = 24):
        """Generate all graphs for all agents."""
        storage = self._init_storage()
        
        # Get all known agents
        agents = storage.get_agents()
        
        if not agents:
            logging.warning("No agents found in storage")
            return

        logging.info(f"Generating graphs for {len(agents)} agent(s)")

        for agent in agents:
            try:
                self.generate_agent_graphs(agent, hours)
            except Exception as e:
                logging.error(f"Failed to generate graphs for {agent}: {e}")

    def generate_agent_graphs(self, agent_name: str, hours: int = 24):
        """Generate all graphs for a specific agent."""
        storage = self._init_storage()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Get metrics for each type
        cpu_temp = storage.get_metrics(agent_name, "cpu_temperature", start_time, end_time)
        cpu_usage = storage.get_metrics(agent_name, "cpu_usage", start_time, end_time)
        system_load = storage.get_metrics(agent_name, "system_load", start_time, end_time)
        
        # Generate individual graphs
        if cpu_temp:
            self._plot_cpu_temperature(cpu_temp, agent_name)
        
        if cpu_usage:
            self._plot_cpu_usage(cpu_usage, agent_name)
        
        if system_load:
            self._plot_system_load(system_load, agent_name)
        
        # Generate combined overview
        if cpu_temp or cpu_usage or system_load:
            self._plot_overview(cpu_temp, cpu_usage, system_load, agent_name)

    def _parse_timestamps(self, metrics: List[Dict]) -> tuple:
        """Parse timestamps from metrics."""
        timestamps = []
        values = []
        
        for m in metrics:
            try:
                ts = datetime.fromisoformat(m.get("timestamp", ""))
                val = float(m.get("value", 0))
                timestamps.append(ts)
                values.append(val)
            except (ValueError, TypeError) as e:
                logging.debug(f"Skipping invalid metric: {e}")
                continue
        
        return timestamps, values

    def _plot_cpu_temperature(self, metrics: List[Dict], agent_name: str):
        """Plot CPU temperature over time."""
        timestamps, values = self._parse_timestamps(metrics)
        
        if not timestamps:
            return
        
        fig, ax = plt.subplots(figsize=(self.graph_width, self.graph_height))
        
        ax.plot(timestamps, values, 'r-', linewidth=2, label='CPU Temperature', marker='o', markersize=3)
        
        # Add threshold lines
        warning_temp = float(self.config.get("thresholds", "cpu_temp_warning", fallback=70))
        critical_temp = float(self.config.get("thresholds", "cpu_temp_critical", fallback=85))
        
        ax.axhline(y=warning_temp, color='orange', linestyle='--', linewidth=2, label=f'Warning ({warning_temp}°C)')
        ax.axhline(y=critical_temp, color='red', linestyle='--', linewidth=2, label=f'Critical ({critical_temp}°C)')
        
        ax.fill_between(timestamps, values, warning_temp, where=[v >= warning_temp for v in values], 
                       color='red', alpha=0.3, interpolate=True)
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Temperature (°C)', fontsize=12)
        ax.set_title(f'CPU Temperature - {agent_name}', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, f"{agent_name}_cpu_temp.png")
        plt.savefig(output_path, dpi=100)
        plt.close()
        
        logging.info(f"Saved CPU temperature graph: {output_path}")

    def _plot_cpu_usage(self, metrics: List[Dict], agent_name: str):
        """Plot CPU usage over time."""
        timestamps, values = self._parse_timestamps(metrics)
        
        if not timestamps:
            return
        
        fig, ax = plt.subplots(figsize=(self.graph_width, self.graph_height))
        
        ax.plot(timestamps, values, 'b-', linewidth=2, label='CPU Usage', marker='o', markersize=3)
        ax.fill_between(timestamps, values, 0, alpha=0.3, color='blue')
        
        # Add threshold lines
        warning_usage = float(self.config.get("thresholds", "cpu_usage_warning", fallback=80))
        critical_usage = float(self.config.get("thresholds", "cpu_usage_critical", fallback=95))
        
        ax.axhline(y=warning_usage, color='orange', linestyle='--', linewidth=2, label=f'Warning ({warning_usage}%)')
        ax.axhline(y=critical_usage, color='red', linestyle='--', linewidth=2, label=f'Critical ({critical_usage}%)')
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('CPU Usage (%)', fontsize=12)
        ax.set_title(f'CPU Usage - {agent_name}', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.legend(loc='upper right')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, f"{agent_name}_cpu_usage.png")
        plt.savefig(output_path, dpi=100)
        plt.close()
        
        logging.info(f"Saved CPU usage graph: {output_path}")

    def _plot_system_load(self, metrics: List[Dict], agent_name: str):
        """Plot system load over time."""
        # Parse load values from JSON
        timestamps = []
        load_1min = []
        load_5min = []
        load_15min = []
        
        for m in metrics:
            try:
                ts = datetime.fromisoformat(m.get("timestamp", ""))
                load_data = json.loads(m.get("value", "{}"))
                timestamps.append(ts)
                load_1min.append(float(load_data.get("1min", 0)))
                load_5min.append(float(load_data.get("5min", 0)))
                load_15min.append(float(load_data.get("15min", 0)))
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logging.debug(f"Skipping invalid load metric: {e}")
                continue
        
        if not timestamps:
            return
        
        fig, ax = plt.subplots(figsize=(self.graph_width, self.graph_height))
        
        ax.plot(timestamps, load_1min, 'g-', linewidth=2, label='1 min', marker='o', markersize=3)
        ax.plot(timestamps, load_5min, 'b-', linewidth=2, label='5 min', marker='s', markersize=3)
        ax.plot(timestamps, load_15min, 'm-', linewidth=2, label='15 min', marker='^', markersize=3)
        
        # Add threshold lines
        warning_load = float(self.config.get("thresholds", "load_warning", fallback=2.0))
        critical_load = float(self.config.get("thresholds", "load_critical", fallback=4.0))
        
        ax.axhline(y=warning_load, color='orange', linestyle='--', linewidth=2, label=f'Warning ({warning_load})')
        ax.axhline(y=critical_load, color='red', linestyle='--', linewidth=2, label=f'Critical ({critical_load})')
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Load Average', fontsize=12)
        ax.set_title(f'System Load - {agent_name}', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, f"{agent_name}_system_load.png")
        plt.savefig(output_path, dpi=100)
        plt.close()
        
        logging.info(f"Saved system load graph: {output_path}")

    def _plot_overview(self, cpu_temp: List[Dict], cpu_usage: List[Dict], 
                       system_load: List[Dict], agent_name: str):
        """Generate an overview with all metrics in one plot."""
        fig, axes = plt.subplots(3, 1, figsize=(self.graph_width, self.graph_height * 1.5))
        
        # CPU Temperature
        if cpu_temp:
            timestamps, values = self._parse_timestamps(cpu_temp)
            if timestamps:
                warning_temp = float(self.config.get("thresholds", "cpu_temp_warning", fallback=70))
                axes[0].plot(timestamps, values, 'r-', linewidth=2, label='CPU Temp')
                axes[0].axhline(y=warning_temp, color='orange', linestyle='--', alpha=0.7)
                axes[0].set_ylabel('°C')
                axes[0].set_title('CPU Temperature')
                axes[0].legend()
        
        # CPU Usage
        if cpu_usage:
            timestamps, values = self._parse_timestamps(cpu_usage)
            if timestamps:
                axes[1].plot(timestamps, values, 'b-', linewidth=2, label='CPU Usage')
                axes[1].fill_between(timestamps, values, 0, alpha=0.3, color='blue')
                axes[1].set_ylabel('%')
                axes[1].set_title('CPU Usage')
                axes[1].set_ylim(0, 100)
                axes[1].legend()
        
        # System Load
        if system_load:
            timestamps = []
            load_1min = []
            
            for m in system_load:
                try:
                    ts = datetime.fromisoformat(m.get("timestamp", ""))
                    load_data = json.loads(m.get("value", "{}"))
                    timestamps.append(ts)
                    load_1min.append(float(load_data.get("1min", 0)))
                except (ValueError, TypeError, json.JSONDecodeError):
                    continue
            
            if timestamps:
                axes[2].plot(timestamps, load_1min, 'g-', linewidth=2, label='1 min')
                axes[2].set_ylabel('Load')
                axes[2].set_title('System Load')
                axes[2].legend()
        
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        axes[-1].set_xlabel('Time')
        
        plt.suptitle(f'Monitoring Overview - {agent_name}', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, f"{agent_name}_overview.png")
        plt.savefig(output_path, dpi=100)
        plt.close()
        
        logging.info(f"Saved overview graph: {output_path}")

    def generate_comparison_graph(self, agents: List[str], hours: int = 24, metric: str = "cpu_usage"):
        """Generate a comparison graph across multiple agents."""
        storage = self._init_storage()
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        fig, ax = plt.subplots(figsize=(self.graph_width, self.graph_height))
        
        colors = sns.color_palette("husl", len(agents))
        
        for i, agent in enumerate(agents):
            metrics = storage.get_metrics(agent, metric, start_time, end_time)
            if metrics:
                timestamps, values = self._parse_timestamps(metrics)
                if timestamps:
                    ax.plot(timestamps, values, color=colors[i], linewidth=2, 
                           label=agent, alpha=0.8)
        
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel(self._get_metric_label(metric), fontsize=12)
        ax.set_title(f'{self._get_metric_title(metric)} Comparison', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, f"comparison_{metric}.png")
        plt.savefig(output_path, dpi=100)
        plt.close()
        
        logging.info(f"Saved comparison graph: {output_path}")

    def _get_metric_label(self, metric: str) -> str:
        """Get y-axis label for metric."""
        labels = {
            "cpu_temperature": "Temperature (°C)",
            "cpu_usage": "CPU Usage (%)",
            "system_load": "Load Average"
        }
        return labels.get(metric, metric)

    def _get_metric_title(self, metric: str) -> str:
        """Get title for metric."""
        titles = {
            "cpu_temperature": "CPU Temperature",
            "cpu_usage": "CPU Usage",
            "system_load": "System Load"
        }
        return titles.get(metric, metric)


def main():
    """Main entry point for visualization."""
    import argparse
    import configparser

    parser = argparse.ArgumentParser(description="Monitoring Visualization")
    parser.add_argument("--config", default="config/config.ini",
                        help="Path to config file")
    parser.add_argument("--agent", help="Generate graphs for specific agent")
    parser.add_argument("--hours", type=int, default=24, 
                        help="Hours of history to graph")
    parser.add_argument("--compare", nargs="+", 
                        help="Compare multiple agents")
    parser.add_argument("--metric", default="cpu_usage",
                        choices=["cpu_temperature", "cpu_usage", "system_load"],
                        help="Metric to compare")
    parser.add_argument("--output-dir", help="Output directory for graphs")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        visualizer = Visualizer(config_path=args.config)
        
        if args.output_dir:
            visualizer.output_dir = args.output_dir
            os.makedirs(args.output_dir, exist_ok=True)
        
        if args.compare:
            visualizer.generate_comparison_graph(args.compare, args.hours, args.metric)
        elif args.agent:
            visualizer.generate_agent_graphs(args.agent, args.hours)
        else:
            visualizer.generate_all_graphs(args.hours)
            
    except Exception as e:
        logging.error(f"Visualization error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
