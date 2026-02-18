#!/usr/bin/env python3
"""
Metrics Visualization Script
Generates graphs from collected metrics using Matplotlib and Seaborn
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
import os

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class MetricsVisualizer:
    """Generate visualizations from metrics data"""
    
    def __init__(self, data_source: str = '/var/log/metrics_data.json'):
        """Initialize visualizer"""
        self.data_source = data_source
        self.metrics_data = []
        self.agents = set()
        
    def load_data(self, start_time: Optional[str] = None, 
                  end_time: Optional[str] = None,
                  agent_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load metrics data from JSON file"""
        if not os.path.exists(self.data_source):
            print(f"Warning: Data file {self.data_source} not found")
            return []
        
        metrics = []
        
        try:
            with open(self.data_source, 'r') as f:
                for line in f:
                    try:
                        metric = json.loads(line.strip())
                        
                        # Apply filters
                        if agent_filter and metric.get('agent_name') != agent_filter:
                            continue
                        
                        if start_time and metric.get('collection_time', '') < start_time:
                            continue
                        
                        if end_time and metric.get('collection_time', '') > end_time:
                            continue
                        
                        metrics.append(metric)
                    except json.JSONDecodeError:
                        continue
            
            self.metrics_data = metrics
            self.agents = set(m.get('agent_name', 'unknown') for m in metrics)
            
            print(f"Loaded {len(metrics)} metric records from {len(self.agents)} agents")
            return metrics
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def plot_cpu_temperature(self, output_file: str = '/tmp/cpu_temperature.png', 
                           agent_filter: Optional[str] = None,
                           hours: int = 24):
        """Plot CPU temperature over time"""
        if not self.metrics_data:
            self.load_data()
        
        # Filter data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        filtered_data = []
        for metric in self.metrics_data:
            try:
                dt = datetime.fromisoformat(metric.get('collection_time', ''))
                if start_time <= dt <= end_time:
                    filtered_data.append(metric)
            except:
                continue
        
        if not filtered_data:
            print("No data to plot")
            return
        
        # Prepare data
        df_data = []
        for metric in filtered_data:
            temp = metric.get('cpu_temperature')
            if temp is not None:
                df_data.append({
                    'timestamp': datetime.fromisoformat(metric['collection_time']),
                    'agent': metric['agent_name'],
                    'temperature': temp
                })
        
        if not df_data:
            print("No temperature data to plot")
            return
        
        df = pd.DataFrame(df_data)
        
        # Create plot
        plt.figure(figsize=(12, 6))
        
        for agent in df['agent'].unique():
            agent_data = df[df['agent'] == agent]
            plt.plot(agent_data['timestamp'], agent_data['temperature'], 
                    marker='o', markersize=3, label=agent, linewidth=2)
        
        plt.title(f'CPU Temperature Over Time (Last {hours} hours)', fontsize=16, fontweight='bold')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Temperature (°C)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add threshold line
        plt.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Warning (70°C)')
        plt.axhline(y=85, color='darkred', linestyle='--', alpha=0.7, label='Critical (85°C)')
        
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, hours//6)))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"CPU temperature plot saved to {output_file}")
        plt.close()
    
    def plot_cpu_usage(self, output_file: str = '/tmp/cpu_usage.png',
                      agent_filter: Optional[str] = None,
                      hours: int = 24):
        """Plot CPU usage over time"""
        if not self.metrics_data:
            self.load_data()
        
        # Filter data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df_data = []
        for metric in self.metrics_data:
            try:
                dt = datetime.fromisoformat(metric.get('collection_time', ''))
                if start_time <= dt <= end_time and metric.get('status') == 'success':
                    df_data.append({
                        'timestamp': datetime.fromisoformat(metric['collection_time']),
                        'agent': metric['agent_name'],
                        'usage': metric.get('cpu_usage', 0)
                    })
            except:
                continue
        
        if not df_data:
            print("No CPU usage data to plot")
            return
        
        df = pd.DataFrame(df_data)
        
        # Create plot
        plt.figure(figsize=(12, 6))
        
        for agent in df['agent'].unique():
            agent_data = df[df['agent'] == agent]
            plt.plot(agent_data['timestamp'], agent_data['usage'], 
                    marker='o', markersize=3, label=agent, linewidth=2)
        
        plt.title(f'CPU Usage Over Time (Last {hours} hours)', fontsize=16, fontweight='bold')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('CPU Usage (%)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add threshold lines
        plt.axhline(y=80, color='orange', linestyle='--', alpha=0.7, label='Warning (80%)')
        plt.axhline(y=95, color='red', linestyle='--', alpha=0.7, label='Critical (95%)')
        
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, hours//6)))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"CPU usage plot saved to {output_file}")
        plt.close()
    
    def plot_system_load(self, output_file: str = '/tmp/system_load.png',
                        agent_filter: Optional[str] = None,
                        hours: int = 24):
        """Plot system load averages over time"""
        if not self.metrics_data:
            self.load_data()
        
        # Filter data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df_data = []
        for metric in self.metrics_data:
            try:
                dt = datetime.fromisoformat(metric.get('collection_time', ''))
                if start_time <= dt <= end_time and metric.get('status') == 'success':
                    load = metric.get('system_load', {})
                    df_data.append({
                        'timestamp': datetime.fromisoformat(metric['collection_time']),
                        'agent': metric['agent_name'],
                        'load_1min': load.get('1min', 0),
                        'load_5min': load.get('5min', 0),
                        'load_15min': load.get('15min', 0)
                    })
            except:
                continue
        
        if not df_data:
            print("No system load data to plot")
            return
        
        df = pd.DataFrame(df_data)
        
        # Create subplot
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        
        load_periods = ['load_1min', 'load_5min', 'load_15min']
        titles = ['1 Minute Load', '5 Minute Load', '15 Minute Load']
        
        for i, (period, title) in enumerate(zip(load_periods, titles)):
            for agent in df['agent'].unique():
                agent_data = df[df['agent'] == agent]
                axes[i].plot(agent_data['timestamp'], agent_data[period], 
                           marker='o', markersize=2, label=agent, linewidth=1.5)
            
            axes[i].set_title(title, fontsize=12, fontweight='bold')
            axes[i].set_ylabel('Load Average', fontsize=10)
            axes[i].grid(True, alpha=0.3)
            axes[i].legend()
            
            # Add threshold line
            axes[i].axhline(y=2.0, color='red', linestyle='--', alpha=0.7)
        
        axes[-1].set_xlabel('Time', fontsize=12)
        
        plt.suptitle(f'System Load Over Time (Last {hours} hours)', fontsize=16, fontweight='bold')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, hours//6)))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"System load plot saved to {output_file}")
        plt.close()
    
    def plot_memory_usage(self, output_file: str = '/tmp/memory_usage.png',
                         agent_filter: Optional[str] = None,
                         hours: int = 24):
        """Plot memory usage over time"""
        if not self.metrics_data:
            self.load_data()
        
        # Filter data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df_data = []
        for metric in self.metrics_data:
            try:
                dt = datetime.fromisoformat(metric.get('collection_time', ''))
                if start_time <= dt <= end_time and metric.get('status') == 'success':
                    mem = metric.get('memory_usage', {})
                    df_data.append({
                        'timestamp': datetime.fromisoformat(metric['collection_time']),
                        'agent': metric['agent_name'],
                        'total': mem.get('total', 0),
                        'used': mem.get('used', 0),
                        'percent': mem.get('percent', 0)
                    })
            except:
                continue
        
        if not df_data:
            print("No memory data to plot")
            return
        
        df = pd.DataFrame(df_data)
        
        # Create subplot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot percentage
        for agent in df['agent'].unique():
            agent_data = df[df['agent'] == agent]
            ax1.plot(agent_data['timestamp'], agent_data['percent'], 
                    marker='o', markersize=3, label=agent, linewidth=2)
        
        ax1.set_title('Memory Usage Percentage', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Usage (%)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=85, color='orange', linestyle='--', alpha=0.7, label='Warning (85%)')
        ax1.axhline(y=95, color='red', linestyle='--', alpha=0.7, label='Critical (95%)')
        
        # Plot absolute usage
        for agent in df['agent'].unique():
            agent_data = df[df['agent'] == agent]
            ax2.plot(agent_data['timestamp'], agent_data['used'], 
                    marker='o', markersize=3, label=agent, linewidth=2)
        
        ax2.set_title('Memory Usage (Absolute)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Used (GB)', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle(f'Memory Usage Over Time (Last {hours} hours)', fontsize=16, fontweight='bold')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, hours//6)))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Memory usage plot saved to {output_file}")
        plt.close()
    
    def plot_security_status(self, output_file: str = '/tmp/security_status.png',
                           agent_filter: Optional[str] = None,
                           hours: int = 24):
        """Plot security status over time"""
        if not self.metrics_data:
            self.load_data()
        
        # Filter data
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df_data = []
        for metric in self.metrics_data:
            try:
                dt = datetime.fromisoformat(metric.get('collection_time', ''))
                if start_time <= dt <= end_time:
                    sec = metric.get('security_threats', {})
                    df_data.append({
                        'timestamp': datetime.fromisoformat(metric['collection_time']),
                        'agent': metric['agent_name'],
                        'status': sec.get('status', 'UNKNOWN'),
                        'issues_count': len(sec.get('issues', []))
                    })
            except:
                continue
        
        if not df_data:
            print("No security data to plot")
            return
        
        df = pd.DataFrame(df_data)
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot security status counts
        status_counts = df.groupby(['timestamp', 'status']).size().unstack(fill_value=0)
        if not status_counts.empty:
            status_counts.plot(kind='area', ax=ax1, alpha=0.7)
            ax1.set_title('Security Status Over Time', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Count', fontsize=12)
            ax1.legend(title='Status')
            ax1.grid(True, alpha=0.3)
        
        # Plot issue counts
        for agent in df['agent'].unique():
            agent_data = df[df['agent'] == agent]
            ax2.plot(agent_data['timestamp'], agent_data['issues_count'], 
                    marker='o', markersize=3, label=agent, linewidth=2)
        
        ax2.set_title('Security Issues Count', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time', fontsize=12)
        ax2.set_ylabel('Number of Issues', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle(f'Security Status Over Time (Last {hours} hours)', fontsize=16, fontweight='bold')
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=max(1, hours//6)))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Security status plot saved to {output_file}")
        plt.close()
    
    def generate_dashboard(self, output_dir: str = '/tmp/dashboard', 
                          hours: int = 24):
        """Generate a complete dashboard with all metrics"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"Generating dashboard for last {hours} hours...")
        
        # Generate all plots
        self.plot_cpu_temperature(f'{output_dir}/cpu_temperature.png', hours=hours)
        self.plot_cpu_usage(f'{output_dir}/cpu_usage.png', hours=hours)
        self.plot_system_load(f'{output_dir}/system_load.png', hours=hours)
        self.plot_memory_usage(f'{output_dir}/memory_usage.png', hours=hours)
        self.plot_security_status(f'{output_dir}/security_status.png', hours=hours)
        
        # Generate HTML summary
        self._generate_html_summary(output_dir, hours)
        
        print(f"Dashboard generated in {output_dir}")
    
    def _generate_html_summary(self, output_dir: str, hours: int):
        """Generate HTML summary page"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>System Monitoring Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .plot {{ margin: 20px 0; text-align: center; }}
        .plot img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
        .info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>System Monitoring Dashboard</h1>
        <div class="info">
            <p><strong>Dashboard Period:</strong> Last {hours} hours</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Agents:</strong> {', '.join(self.agents)}</p>
        </div>
        
        <div class="plot">
            <h2>CPU Temperature</h2>
            <img src="cpu_temperature.png" alt="CPU Temperature">
        </div>
        
        <div class="plot">
            <h2>CPU Usage</h2>
            <img src="cpu_usage.png" alt="CPU Usage">
        </div>
        
        <div class="plot">
            <h2>System Load</h2>
            <img src="system_load.png" alt="System Load">
        </div>
        
        <div class="plot">
            <h2>Memory Usage</h2>
            <img src="memory_usage.png" alt="Memory Usage">
        </div>
        
        <div class="plot">
            <h2>Security Status</h2>
            <img src="security_status.png" alt="Security Status">
        </div>
    </div>
</body>
</html>
"""
        
        with open(f'{output_dir}/index.html', 'w') as f:
            f.write(html)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate metrics visualizations')
    parser.add_argument('--data-source', default='/var/log/metrics_data.json',
                       help='Path to metrics data file')
    parser.add_argument('--output-dir', default='/tmp/dashboard',
                       help='Output directory for dashboard')
    parser.add_argument('--hours', type=int, default=24,
                       help='Hours of data to include in plots')
    parser.add_argument('--plot', choices=['all', 'temperature', 'cpu', 'load', 'memory', 'security'],
                       default='all',
                       help='Which plot(s) to generate')
    parser.add_argument('--agent', help='Filter by specific agent')
    
    args = parser.parse_args()
    
    # Initialize visualizer
    visualizer = MetricsVisualizer(args.data_source)
    
    # Load data
    visualizer.load_data()
    
    if not visualizer.metrics_data:
        print("No data loaded. Please check the data source.")
        return
    
    # Generate plots
    if args.plot in ['all', 'temperature']:
        visualizer.plot_cpu_temperature(f'{args.output_dir}/cpu_temperature.png', 
                                       agent_filter=args.agent, hours=args.hours)
    
    if args.plot in ['all', 'cpu']:
        visualizer.plot_cpu_usage(f'{args.output_dir}/cpu_usage.png',
                                 agent_filter=args.agent, hours=args.hours)
    
    if args.plot in ['all', 'load']:
        visualizer.plot_system_load(f'{args.output_dir}/system_load.png',
                                   agent_filter=args.agent, hours=args.hours)
    
    if args.plot in ['all', 'memory']:
        visualizer.plot_memory_usage(f'{args.output_dir}/memory_usage.png',
                                    agent_filter=args.agent, hours=args.hours)
    
    if args.plot in ['all', 'security']:
        visualizer.plot_security_status(f'{args.output_dir}/security_status.png',
                                       agent_filter=args.agent, hours=args.hours)
    
    # Generate HTML summary for all plots
    if args.plot == 'all':
        visualizer.generate_dashboard(args.output_dir, hours=args.hours)


if __name__ == "__main__":
    main()