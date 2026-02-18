# Python System Monitoring via XML-RPC

A comprehensive Python-based monitoring system that allows System A to monitor multiple System B agents in near real-time using XML-RPC communication.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [OS-Specific Limitations](#os-specific-limitations)
- [Security Considerations](#security-considerations)
- [Storage Options](#storage-options)
- [Visualization](#visualization)
- [Troubleshooting](#troubleshooting)

## Overview

This monitoring system consists of:
- **Agent Server** (runs on System B): Collects system metrics and exposes them via XML-RPC
- **Collector** (runs on System A): Polls multiple agents and stores metrics
- **Storage Layer**: Abstracts storage between file logging and MySQL database
- **Visualization**: Generates graphs and dashboards from collected data

## Architecture

```
┌─────────────────┐         XML-RPC          ┌─────────────────┐
│   Collector     │◄────────────────────────►│  Agent Server   │
│   (System A)    │   (HTTP/XML-RPC)         │   (System B)    │
└─────────┬───────┘                          └─────────┬───────┘
          │                                            │
          │                                            ▼
          │                                   ┌─────────────────┐
          │                                   │  System Metrics │
          │                                   │  • CPU Temp     │
          │                                   │  • CPU Usage    │
          │                                   │  • Load Avg     │
          │                                   │  • Memory       │
          │                                   │  • Disk         │
          │                                   │  • Security     │
          │                                   └─────────────────┘
          │
          ▼
┌─────────────────┐
│  Storage Layer  │
│  • File (LOG)   │
│  • MySQL        │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ Visualization   │
│  • Graphs       │
│  • Dashboard    │
└─────────────────┘
```

## Features

### Required Metrics (All Mandatory)
- ✅ **CPU Temperature** - Gracefully handles missing sensors
- ✅ **High System Load** - 1, 5, and 15-minute averages
- ✅ **High CPU Usage** - Real-time CPU percentage
- ✅ **Security Threats** - Suspicious processes, SSH attempts, network activity

### Additional Features
- ✅ **Near Real-Time Monitoring** - Configurable polling intervals
- ✅ **Multiple Agent Support** - Monitor unlimited System B instances
- ✅ **Logging with Rotation** - Automatic log rotation and management
- ✅ **Optional MySQL Storage** - Scalable database storage
- ✅ **Graph Visualization** - Matplotlib/Seaborn graphs
- ✅ **Alert System** - Threshold-based alerting
- ✅ **Thread-Safe Operations** - Concurrent agent polling

## Prerequisites

### System Requirements
- Python 3.7 or higher
- Linux, macOS, or Windows
- Network connectivity between System A and System B

### Python Dependencies
```
psutil>=5.8.0
matplotlib>=3.3.0
seaborn>=0.11.0
pandas>=1.3.0
numpy>=1.20.0
pymysql>=1.0.0 (for MySQL storage)
```

## Installation

### 1. Clone and Setup

```bash
git clone <repository>
cd python-monitor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Required Directories

```bash
sudo mkdir -p /var/log
sudo mkdir -p /tmp/dashboard
```

### 4. Setup Database (Optional)

```bash
mysql -u root -p < db/init_database.sql
```

## Quick Start

### Method 1: Quick Local Test

#### Terminal 1 - Start Agent (System B)
```bash
# Start the agent server on localhost
python3 /home/engine/project/agent/agent_server.py
```

#### Terminal 2 - Start Collector (System A)
```bash
# Update config to monitor localhost
echo '{"host": "localhost", "port": 8000, "name": "local-agent"}' > /tmp/agent.json

# Start collector
python3 /home/engine/project/collector/collector.py
```

### Method 2: Production Setup

#### System B - Install Agent

1. **Install Agent Script**
```bash
sudo cp agent/agent_server.py /usr/local/bin/monitor-agent
sudo chmod +x /usr/local/bin/monitor-agent
sudo cp config/agent_config.json /etc/monitor/
```

2. **Configure Firewall** (if needed)
```bash
sudo ufw allow 8000/tcp
# or
sudo firewall-cmd --add-port=8000/tcp --permanent
```

3. **Create Systemd Service**
```bash
sudo tee /etc/systemd/system/monitor-agent.service > /dev/null <<EOF
[Unit]
Description=Monitor Agent
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /usr/local/bin/monitor-agent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable monitor-agent
sudo systemctl start monitor-agent
```

#### System A - Install Collector

1. **Install Collector**
```bash
sudo cp collector/collector.py /usr/local/bin/monitor-collector
sudo cp config/collector_config.json /etc/monitor/
sudo chmod +x /usr/local/bin/monitor-collector
```

2. **Configure Agents**
```bash
sudo nano /etc/monitor/collector_config.json
# Add your agent IPs
```

3. **Create Systemd Service**
```bash
sudo tee /etc/systemd/system/monitor-collector.service > /dev/null <<EOF
[Unit]
Description=Monitor Collector
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/monitor-collector
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable monitor-collector
sudo systemctl start monitor-collector
```

## Configuration

### Agent Configuration (`/home/engine/project/config/agent_config.json`)

```json
{
    "host": "0.0.0.0",              # Listen address
    "port": 8000,                   # XML-RPC port
    "check_interval": 30,           # Internal check interval
    "log_level": "INFO",            # Logging level
    "log_file": "/var/log/monitor_agent.log",
    "metrics": {
        "enable_temperature": true,
        "enable_cpu": true,
        "enable_memory": true,
        "enable_disk": true,
        "enable_security": true
    },
    "security": {
        "allowed_ips": ["127.0.0.1", "192.168.1.0/24"],
        "require_auth": false
    }
}
```

### Collector Configuration (`/home/engine/project/config/collector_config.json`)

```json
{
    "agents": [
        {
            "name": "server-01",
            "host": "192.168.1.101",
            "port": 8000
        },
        {
            "name": "server-02", 
            "host": "192.168.1.102",
            "port": 8000
        }
    ],
    "poll_interval": 30,            # Polling frequency (seconds)
    "timeout": 10,                  # XML-RPC timeout
    "storage": {
        "type": "file",             # "file" or "mysql"
        "log_file": "/var/log/metrics_collector.log",
        "metrics_file": "/var/log/metrics_data.log",
        "json_file": "/var.log/metrics_data.json",
        "rotation": {
            "max_size": "10MB",
            "backup_count": 5
        }
    },
    "thresholds": {
        "cpu_usage": 80,            # Alert thresholds
        "cpu_temperature": 70,
        "system_load": 2.0,
        "memory_usage": 85,
        "disk_usage": 90
    }
}
```

### MySQL Storage Configuration

To use MySQL storage, update the collector config:

```json
{
    "storage": {
        "type": "mysql",
        "mysql_host": "localhost",
        "mysql_port": 3306,
        "mysql_user": "monitor",
        "mysql_password": "your_password",
        "mysql_database": "monitoring"
    }
}
```

## Usage

### Testing Connectivity

```bash
# Test agent connectivity
python3 -c "
import xmlrpc.client
proxy = xmlrc.client.ServerProxy('http://192.168.1.101:8000')
print(proxy.ping())
"
```

### Generating Visualizations

```bash
# Generate all graphs for last 24 hours
python3 /home/engine/project/visualization/visualize_metrics.py --plot all --hours 24

# Generate specific graphs
python3 /home/engine/project/visualization/visualize_metrics.py --plot temperature --hours 12

# Generate for specific agent
python3 /home/engine/project/visualization/visualize_metrics.py --plot cpu --agent server-01

# Generate custom dashboard
python3 /home/engine/project/visualization/visualize_metrics.py \
    --output-dir /var/www/dashboard \
    --hours 48 \
    --plot all
```

### Querying Stored Data

```bash
# Check recent metrics in log file
tail -f /var/log/metrics_data.log

# Query JSON data
python3 -c "
import json
with open('/var/log/metrics_data.json', 'r') as f:
    for line in f:
        if 'server-01' in line:
            print(json.loads(line))
"
```

## OS-Specific Limitations

### Linux
✅ **Fully Supported**
- CPU Temperature: `/sys/class/thermal/`, `/sys/class/hwmon/`
- CPU Usage: `psutil`, `/proc/stat`
- System Load: `getloadavg()`, `uptime`
- Memory: `/proc/meminfo`, `psutil`
- Security: `/var/log/auth.log`, `psutil`

### macOS
⚠️ **Partially Supported**
- CPU Temperature: ❌ Not available via standard APIs
- CPU Usage: ✅ `psutil`
- System Load: ✅ `getloadavg()`
- Memory: ✅ `psutil`
- Security: ✅ Limited (process checking only)

**Note:** macOS thermal sensors require third-party tools or IOKit.

### Windows
⚠️ **Partially Supported**
- CPU Temperature: ❌ Requires WMI or third-party tools
- CPU Usage: ✅ `psutil`
- System Load: ❌ No load average (returns 0.0)
- Memory: ✅ `psutil`
- Security: ✅ Limited process checking

**Note:** Windows thermal zones require additional drivers or software.

### Handling Missing Temperature Sensors

The system gracefully handles missing temperature sensors:

```python
# Agent returns None for unavailable temperatures
cpu_temperature = get_cpu_temperature()  # None if not available

# Collector handles gracefully
if temp is not None:
    alert_if_above_threshold(temp)
else:
    log.info("Temperature sensor not available on this system")
```

## Security Considerations

### XML-RPC Security Implications

⚠️ **Important Security Notes:**

1. **Unencrypted Communication**
   - XML-RPC uses plain HTTP (not HTTPS)
   - Data transmitted in clear text
   - Use only on trusted networks

2. **No Built-in Authentication**
   - Anyone with network access can query metrics
   - Implement additional security measures

3. **DoS Vulnerabilities**
   - XML-RPC is susceptible to XML bomb attacks
   - Implement rate limiting and firewalls

### Recommended Security Practices

#### 1. Network Isolation
```bash
# Use private networks only
# Never expose agents to public internet

# Firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw deny 8000
```

#### 2. IP Whitelisting
Update agent config:
```json
{
    "security": {
        "allowed_ips": ["192.168.1.10", "192.168.1.20"],
        "require_auth": true
    }
}
```

#### 3. VPN/Tunneling
```bash
# Use SSH tunneling for encrypted communication
ssh -L 8000:localhost:8000 user@system-b

# Then connect to localhost:8000
```

#### 4. Reverse Proxy with SSL
```bash
# Use nginx with SSL termination
location /xmlrpc/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

#### 5. Rate Limiting
```bash
# Limit XML-RPC connections via iptables
sudo iptables -A INPUT -p tcp --dport 8000 -m limit --limit 10/minute --limit-burst 5 -j ACCEPT
```

### Security Threat Detection

The agent monitors for:
- ✅ **Suspicious Processes** - Processes in `/tmp/`, `/var/tmp/`
- ✅ **SSH Brute Force** - Failed login attempts in logs
- ✅ **Unusual Network Activity** - Suspicious port connections
- ✅ **Unauthorized Executables** - Processes without executable paths

## Storage Options

### File Storage (Default)

**Advantages:**
- ✅ No additional dependencies
- ✅ Simple setup and maintenance
- ✅ Good for small deployments
- ✅ Easy log rotation

**Disadvantages:**
- ❌ Limited querying capabilities
- ❌ No advanced analytics
- ❌ Manual data cleanup needed

**Configuration:**
```json
{
    "storage": {
        "type": "file",
        "log_file": "/var/log/metrics_collector.log",
        "metrics_file": "/var/log/metrics_data.log",
        "json_file": "/var/log/metrics_data.json",
        "rotation": {
            "max_size": "10MB",
            "backup_count": 5
        }
    }
}
```

### MySQL Storage

**Advantages:**
- ✅ Advanced querying and filtering
- ✅ Historical analysis and reporting
- ✅ Concurrent access support
- ✅ Backup and replication capabilities
- ✅ Performance optimization via indexing

**Disadvantages:**
- ❌ Requires MySQL server
- ❌ Additional dependency and setup
- ❌ More complex troubleshooting

**Setup:**
```bash
# Install MySQL
sudo apt-get install mysql-server

# Initialize database
mysql -u root -p < db/init_database.sql

# Update collector config for MySQL
{
    "storage": {
        "type": "mysql",
        "mysql_host": "localhost",
        "mysql_user": "monitor",
        "mysql_password": "secure_password",
        "mysql_database": "monitoring"
    }
}
```

## Visualization

### Available Graphs

1. **CPU Temperature** - Temperature trends with threshold warnings
2. **CPU Usage** - Usage percentage over time
3. **System Load** - 1, 5, and 15-minute load averages
4. **Memory Usage** - Memory consumption and percentages
5. **Security Status** - Security threat levels and issue counts

### Dashboard Generation

```bash
# Generate complete dashboard
python3 /home/engine/project/visualization/visualize_metrics.py \
    --output-dir /var/www/html/monitoring \
    --hours 24 \
    --plot all

# Access dashboard
firefox http://localhost/monitoring/index.html
```

### Graph Customization

```python
# Modify visualization/visualize_metrics.py
# Custom time ranges
--hours 168  # Last week
--hours 720  # Last month

# Filter by agent
--agent server-01

# Custom output directory
--output-dir /tmp/custom-dashboard
```

## Adding Multiple Monitored Systems

### Step 1: Configure New Agent (on System B)

```bash
# Copy agent files
scp -r agent/ user@system-b:/tmp/monitor/

# Install on new system
ssh user@system-b
sudo cp -r /tmp/monitor/agent /usr/local/
sudo cp /tmp/monitor/config/agent_config.json /etc/monitor/
sudo chmod +x /usr/local/agent/agent_server.py
```

### Step 2: Configure Firewall

```bash
# On System B
sudo ufw allow from 192.168.1.0/24 to any port 8000

# Or specific collector IP
sudo ufw allow from 192.168.1.100 to any port 8000
```

### Step 3: Start Agent

```bash
# Test run
python3 /usr/local/agent/agent_server.py

# Install as service (see Quick Start section)
```

### Step 4: Add to Collector Configuration

```bash
# Edit collector config
sudo nano /etc/monitor/collector_config.json

# Add new agent
{
    "agents": [
        {
            "name": "server-01",
            "host": "192.168.1.101",
            "port": 8000
        },
        {
            "name": "server-02",
            "host": "192.168.1.102",
            "port": 8000
        },
        {
            "name": "new-server",
            "host": "192.168.1.103",  # New agent
            "port": 8000
        }
    ],
    "poll_interval": 30
}
```

### Step 5: Restart Collector

```bash
sudo systemctl restart monitor-collector

# Verify new agent is being monitored
tail -f /var/log/metrics_collector.log
```

### Step 6: Test Connectivity

```bash
# From System A, test new agent
python3 -c "
import xmlrpc.client
proxy = xmlrpc.client.ServerProxy('http://192.168.1.103:8000')
try:
    print('Agent response:', proxy.ping())
    metrics = proxy.get_metrics()
    print('Metrics collected successfully')
except Exception as e:
    print('Connection failed:', e)
"
```

### Bulk Deployment Script

Create a deployment script for multiple agents:

```bash
#!/bin/bash
# deploy_agents.sh

AGENTS=(
    "192.168.1.101:server-01"
    "192.168.1.102:server-02"
    "192.168.1.103:server-03"
    "192.168.1.104:server-04"
)

for agent in "${AGENTS[@]}"; do
    ip=$(echo $agent | cut -d: -f1)
    name=$(echo $agent | cut -d: -f2)
    
    echo "Deploying agent $name at $ip"
    
    # Copy files
    scp -r agent/ user@$ip:/tmp/monitor/
    scp config/agent_config.json user@$ip:/tmp/monitor/
    
    # Install
    ssh user@$ip "
        sudo mkdir -p /etc/monitor
        sudo cp /tmp/monitor/agent/agent_server.py /usr/local/bin/monitor-agent-$name
        sudo cp /tmp/monitor/config/agent_config.json /etc/monitor/agent_$name.json
        sudo chmod +x /usr/local/bin/monitor-agent-$name
    "
done

echo "All agents deployed. Start them manually."
```

## Troubleshooting

### Common Issues

#### Agent Not Responding

```bash
# Check if agent is running
ps aux | grep agent_server

# Check port
netstat -tlnp | grep 8000

# Check logs
tail -f /var/log/monitor_agent.log

# Test manually
python3 -c "import xmlrpc.client; print(xmlrpc.client.ServerProxy('http://localhost:8000').ping())"
```

#### Connection Timeout

```bash
# Check network connectivity
ping 192.168.1.101

# Check firewall
sudo ufw status

# Test with telnet
telnet 192.168.1.101 8000
```

#### Permission Errors

```bash
# Create log directories
sudo mkdir -p /var/log
sudo chmod 777 /var/log

# Or run as user with home directory
# Edit paths in config to use ~/logs/
```

#### Temperature Not Available

```bash
# Check available sensors on Linux
ls /sys/class/thermal/
cat /sys/class/thermal/thermal_zone0/temp

# Install lm-sensors
sudo apt-get install lm-sensors
sensors
```

#### MySQL Connection Failed

```bash
# Test MySQL connection
mysql -u monitor -p monitoring

# Check MySQL service
sudo systemctl status mysql

# Verify user permissions
mysql -u root -p
SELECT User, Host FROM mysql.user WHERE User = 'monitor';
SHOW GRANTS FOR 'monitor'@'localhost';
```

### Log Locations

- **Agent logs**: `/var/log/monitor_agent.log`
- **Collector logs**: `/var/log/metrics_collector.log`
- **Metrics data**: `/var/log/metrics_data.log` and `/var/log/metrics_data.json`
- **System logs**: `/var/log/syslog` or `/var/log/messages`

### Debug Mode

```bash
# Run agent in debug mode
export PYTHONPATH=/home/engine/project:$PYTHONPATH
python3 agent/agent_server.py

# Run collector with verbose logging
python3 collector/collector.py
```

### Performance Tuning

```bash
# Increase poll interval for large deployments
"poll_interval": 60  # 1 minute instead of 30 seconds

# Reduce log verbosity
"log_level": "WARNING"

# Limit concurrent connections
"max_workers": 5
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
1. Check logs for error messages
2. Verify network connectivity
3. Test agents individually
4. Review configuration files
5. Check OS-specific limitations

## Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

---

**Note**: This is a prototype system for educational and small-scale production use. For enterprise deployments, consider using mature monitoring solutions like Prometheus, Zabbix, or Nagios.