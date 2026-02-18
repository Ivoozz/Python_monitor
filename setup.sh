#!/bin/bash
# Setup script for monitoring system

set -e

echo "=== Python Monitoring System Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Running as root. Installing system-wide..."
    SYSTEM_WIDE=true
else
    echo "Running as user. Installing locally..."
    SYSTEM_WIDE=false
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Create directories
if [ "$SYSTEM_WIDE" = true ]; then
    mkdir -p /var/log/monitor
    mkdir -p /etc/monitor
    mkdir -p /usr/local/bin
else
    mkdir -p ~/logs/monitor
    mkdir -p ~/config/monitor
fi

# Copy files
echo "Copying files..."

if [ "$SYSTEM_WIDE" = true ]; then
    cp agent/agent_server.py /usr/local/bin/monitor-agent
    cp collector/collector.py /usr/local/bin/monitor-collector
    cp config/agent_config.json /etc/monitor/
    cp config/collector_config.json /etc/monitor/
    
    chmod +x /usr/local/bin/monitor-agent
    chmod +x /usr/local/bin/monitor-collector
else
    cp agent/agent_server.py ~/bin/monitor-agent
    cp collector/collector.py ~/bin/monitor-collector
    cp config/agent_config.json ~/config/monitor/
    cp config/collector_config.json ~/config/monitor/
    
    chmod +x ~/bin/monitor-agent
    chmod +x ~/bin/monitor-collector
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start monitoring:"
echo ""
echo "1. Start agent on System B:"
echo "   monitor-agent"
echo ""
echo "2. Start collector on System A:"
echo "   monitor-collector"
echo ""
echo "3. Generate visualizations:"
echo "   python3 visualization/visualize_metrics.py --plot all"
echo ""
echo "For production deployment, see docs/README.md"