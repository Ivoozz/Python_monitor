# Python Monitoring System Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Adding Multiple Monitored Systems](#adding-multiple-monitored-systems)
7. [Storage Backends](#storage-backends)
8. [Visualization](#visualization)
9. [OS-Specific Limitations](#os-specific-limitations)
10. [Security Implications](#security-implications)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Configuration](#advanced-configuration)

## Overview

This Python monitoring system provides real-time monitoring of multiple system metrics across multiple remote systems using XML-RPC communication. The system consists of two main components:

- **Agent**: Runs on the system being monitored (System B)
- **Collector**: Runs on the central monitoring system (System A)

### Key Features

- **Real-time monitoring** with configurable polling intervals
- **Multiple metrics**: CPU temperature, system load, CPU usage, security threats
- **Threshold monitoring** with configurable warning and critical levels
- **Flexible storage**: File-based (with rotation) or MySQL database
- **Visualization**: Generate graphs using Matplotlib and Seaborn
- **Concurrent monitoring** of multiple systems
- **Thread-safe operations** for reliable data collection

## System Architecture

```
┌─────────────────┐         XML-RPC          ┌─────────────────┐
│   System A      │◄────────────────────────►│   System B      │
│  (Collector)    │                           │    (Agent)      │
├─────────────────┤                           ├─────────────────┤
│ - Polls agents  │                           │ - Exposes       │
│ - Stores data   │                           │   metrics       │
│ - Generates     │                           │ - CPU temp      │
│   graphs        │                           │ - CPU usage     │
│ - Checks alerts │                           │ - Load avg      │
└─────────────────┘                           └─────────────────┘
```

### Components

1. **Agent (`src/monitoring/agent.py`)**
   - XML-RPC server exposing system metrics
   - Cross-platform metric collection
   - Security threat detection
   - Graceful handling of missing sensors

2. **Collector (`src/monitoring/collector.py`)**
   - Manages multiple agents concurrently
   - Threshold monitoring and alerting
   - Data storage and retrieval
   - Configurable polling intervals

3. **Storage (`src/monitoring/storage.py`)**
   - Abstract storage layer
   - Support for log files, SQLite, and MySQL
   - Automatic data rotation
   - Thread-safe operations

4. **Visualization (`src/monitoring/visualization.py`)**
   - Generate graphs from collected data
   - Comparison across multiple agents
   - Customizable graph formats
   - Support for various time ranges

## Installation

### Prerequisites

- Python 3.7 or higher
- psutil (for system metrics)
- Optional: MySQL server for database storage
- Optional: matplotlib and seaborn for graphs

### Step 1: Install Dependencies

```bash
# Clone or download the monitoring system
cd /path/to/monitoring-system

# Install required dependencies
pip install -r requirements.txt

# Or install individually:
pip install psutil matplotlib seaborn pymysql
```

### Step 2: Set Up Directory Structure

```bash
# Create required directories
sudo mkdir -p /var/log/monitoring/{data,graphs}

# Set appropriate permissions (run as non-root user)
sudo chown -R monitor:monitor /var/log/monitoring
sudo chmod 755 /var/log/monitoring
sudo chmod 755 /var/log/monitoring/{data,graphs}
```

### Step 3: Set Up MySQL Database (Optional)

If using MySQL storage backend:

```bash
# Log in to MySQL as root
mysql -u root -p

# Run the initialization script
SOURCE sql/init_db.sql;

# Create dedicated user (optional but recommended)
CREATE USER 'monitor'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON monitoring.* TO 'monitor'@'localhost';
FLUSH PRIVILEGES;
```

## Configuration

The system uses a configuration file (default: `config/config.ini`) to manage settings.

### Example Configuration

```ini
[general]
log_level = INFO
poll_interval = 10

[storage]
backend = log

[logging]
log_file = /var/log/monitoring/collector.log
max_log_size = 10
backup_count = 5

[mysql]
host = localhost
port = 3306
user = monitor
password = changeme
database = monitoring

[agents]
agent1 = localhost:9000
agent2 = 192.168.1.100:9000
server3 = 192.168.1.101:9000

[thresholds]
cpu_temp_warning = 70
cpu_temp_critical = 85
load_warning = 2.0
load_critical = 4.0
cpu_usage_warning = 80
cpu_usage_critical = 95

[visualization]
output_dir = /var/log/monitoring/graphs
graph_width = 12
graph_height = 8
```

### Configuration Options

#### General Section
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `poll_interval`: How often to poll agents (seconds)

#### Storage Section
- `backend`: Storage backend ('log', 'mysql', 'sqlite')
- `retention_days`: How long to keep data

#### Logging Section
- `log_file`: Path to collector log file
- `max_log_size`: Maximum size in MB before rotation
- `backup_count`: Number of backup log files

#### MySQL Section
- `host`: MySQL server hostname
- `port`: MySQL port
- `user`: Database username
- `password`: Database password
- `database`: Database name

#### Agents Section
- Add entries in format: `name = host:port`
- name: Friendly name for the agent
- host: IP address or hostname
- port: Agent listening port

#### Thresholds Section
- `cpu_temp_warning`: Warning threshold in Celsius
- `cpu_temp_critical`: Critical threshold in Celsius
- `load_warning`: System load warning threshold
- `load_critical`: System load critical threshold
- `cpu_usage_warning`: CPU usage warning percentage
- `cpu_usage_critical`: CPU usage critical percentage

#### Visualization Section
- `output_dir`: Directory to save graphs
- `graph_width`: Graph width in inches
- `graph_height`: Graph height in inches

## Usage

### Starting the Agent

On each system you want to monitor:

```bash
# Using the startup script
chmod +x scripts/start_agent.sh
./scripts/start_agent.sh --host 0.0.0.0 --port 9000

# Or directly with Python
python3 -m src.monitoring.agent --host 0.0.0.0 --port 9000
```

**Agent Options:**
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to listen on (default: 9000)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Starting the Collector

On the central monitoring system:

```bash
# Using the startup script
chmod +x scripts/start_collector.sh
./scripts/start_collector.sh --config config/config.ini

# Or directly with Python
python3 -m src.monitoring.collector --config config/config.ini
```

**Collector Options:**
- `--config`: Path to configuration file
- `--log-level`: Logging level

### Running as a Service

For production use, run the collector and agents as systemd services:

#### Agent Service (on each monitored system)

Create `/etc/systemd/system/monitoring-agent.service`:

```ini
[Unit]
Description=Monitoring Agent
After=network.target

[Service]
Type=simple
User=monitor
Group=monitor
WorkingDirectory=/path/to/monitoring-system
ExecStart=/usr/bin/python3 -m src.monitoring.agent --host 0.0.0.0 --port 9000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable monitoring-agent
sudo systemctl start monitoring-agent
sudo systemctl status monitoring-agent
```

#### Collector Service (on monitoring system)

Create `/etc/systemd/system/monitoring-collector.service`:

```ini
[Unit]
Description=Monitoring Collector
After=network.target

[Service]
Type=simple
User=monitor
Group=monitor
WorkingDirectory=/path/to/monitoring-system
ExecStart=/usr/bin/python3 -m src.monitoring.collector --config config/config.ini
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable monitoring-collector
sudo systemctl start monitoring-collector
sudo systemctl status monitoring-collector
```

## Adding Multiple Monitored Systems

### Step 1: Deploy Agent to Each System

1. Copy the monitoring system files to each system you want to monitor
2. Install dependencies: `pip install -r requirements.txt`
3. Start the agent on each system:

```bash
# On each monitored system
./scripts/start_agent.sh --host 0.0.0.0 --port 9000
```

### Step 2: Configure Agents in Collector

Edit `config/config.ini` on the monitoring system:

```ini
[agents]
web_server1 = 192.168.1.100:9000
web_server2 = 192.168.1.101:9000
db_server = 192.168.1.102:9000
mail_server = 192.168.1.103:9000
```

### Step 3: Restart the Collector

```bash
# Stop the collector
sudo systemctl stop monitoring-collector

# Start it again
sudo systemctl start monitoring-collector
```

### Step 4: Verify Monitoring

Check the collector logs:

```bash
tail -f /var/log/monitoring/collector.log
```

You should see entries like:
```
INFO - Collector started
INFO - Monitoring 4 agent(s)
INFO - Loaded agent: web_server1 at 192.168.1.100:9000
INFO - Collected metrics from 4 agent(s)
```

### Automated Deployment Script

You can create a script to automate agent deployment:

```bash
#!/bin/bash
# deploy_agents.sh

AGENTS=("192.168.1.100" "192.168.1.101" "192.168.1.102")

for agent in "${AGENTS[@]}"; do
    echo "Deploying agent to $agent..."
    scp -r /path/to/monitoring-system user@$agent:/tmp/
    ssh user@$agent "cd /tmp/monitoring-system && pip install -r requirements.txt"
    ssh user@$agent "sudo systemctl enable monitoring-agent"
    ssh user@$agent "sudo systemctl start monitoring-agent"
done
```

## Storage Backends

### File-Based Storage (Default)

The system stores metrics in JSONL format with automatic rotation:

- **Storage location**: `/var/log/monitoring/data/metrics.jsonl`
- **Format**: One JSON object per line
- **Rotation**: When file exceeds 10MB (configurable)
- **Retention**: Automatic cleanup recommended via cron

**Advantages:**
- Simple setup, no database required
- Good for small deployments
- Easy to parse with standard tools

**Disadvantages:**
- Limited querying capabilities
- Can become slow with large datasets

### SQLite Storage (Recommended for Medium Deployments)

SQLite provides better performance and querying:

**Configuration:**
```ini
[storage]
backend = sqlite
```

SQLite files are stored in `/var/log/monitoring/metrics.db`

**Advantages:**
- Better performance than file storage
- Built-in Python, no additional setup
- Good for medium-sized deployments

**Disadvantages:**
- Single writer at a time (though our implementation handles this)

### MySQL Storage (Recommended for Large Deployments)

For production environments with multiple collectors or high data volumes:

**Configuration:**
```ini
[storage]
backend = mysql

[mysql]
host = localhost
port = 3306
user = monitor
password = your_secure_password
database = monitoring
```

**Advantages:**
- Multi-user access
- High performance with proper indexing
- Advanced querying and reporting
- Supports multiple collectors

**Disadvantages:**
- Requires MySQL setup
- Additional complexity

**MySQL Setup:**
1. Install MySQL server
2. Run `sql/init_db.sql`
3. Create dedicated user
4. Configure in `config/config.ini`

## Visualization

### Generating Graphs

Use the visualization script to generate graphs:

```bash
# Generate all graphs for all agents (last 24 hours)
chmod +x scripts/generate_graphs.sh
./scripts/generate_graphs.sh

# Generate graphs for specific agent
./scripts/generate_graphs.sh --agent web_server1

# Generate graphs with custom time range
./scripts/generate_graphs.sh --hours 48

# Compare multiple agents
./scripts/generate_graphs.sh --compare web_server1 web_server2 db_server

# Compare specific metric
./scripts/generate_graphs.sh --compare web_server1 web_server2 --metric cpu_temperature

# Save to custom directory
./scripts/generate_graphs.sh --output-dir /var/www/html/monitoring
```

### Generated Graphs

The system generates several types of graphs:

1. **CPU Temperature** - Shows temperature trends with warning/critical thresholds
2. **CPU Usage** - Displays CPU utilization over time
3. **System Load** - Shows 1, 5, and 15-minute load averages
4. **Overview** - Combined view of all metrics
5. **Comparison** - Compare same metric across multiple agents

### Automated Graph Generation

Set up a cron job to generate graphs regularly:

```bash
# Edit crontab
crontab -e

# Add lines for hourly graphs
0 * * * * /path/to/monitoring-system/scripts/generate_graphs.sh
```

### Web Dashboard

For a web-based dashboard, you can:

1. Generate graphs and save to web-accessible directory
2. Create HTML page that displays the graphs
3. Set up automatic refresh or manual reload

Example HTML dashboard:

```html
<!DOCTYPE html>
<html>
<head>
    <title>System Monitoring Dashboard</title>
    <meta http-equiv="refresh" content="300">
</head>
<body>
    <h1>Monitoring Dashboard</h1>
    <h2>CPU Usage - web_server1</h2>
    <img src="graphs/web_server1_cpu_usage.png">
    
    <h2>CPU Temperature - web_server1</h2>
    <img src="graphs/web_server1_cpu_temp.png">
    
    <h2>System Load - web_server1</h2>
    <img src="graphs/web_server1_system_load.png">
</body>
</html>
```

## OS-Specific Limitations

### Linux

**Fully Supported:**
- CPU temperature via `/sys/class/thermal/` and `psutil`
- System load via `os.getloadavg()`
- CPU usage via `psutil.cpu_percent()`
- Security checks (SSH login attempts, suspicious processes)

**Limitations:**
- Temperature sensors may not be available on all hardware
- Some `/sys` paths require root access
- Temperature cache duration may vary by kernel version

**Security Checks Available:**
- Failed SSH login detection (via `/var/log/auth.log` or `/var/log/secure`)
- Suspicious process detection
- Unusual port monitoring

### Windows

**Fully Supported:**
- CPU usage via `psutil`
- Memory and disk usage
- Basic security checks

**Limitations:**
- CPU temperature: Requires WMI (may not be available on all systems)
- System load: Windows doesn't have traditional load average
- Security checks: Limited compared to Linux

**Workarounds:**
- For CPU temperature, ensure WMI is installed and accessible
- Use CPU usage as primary metric instead of system load
- Consider integrating with Windows Event Log for security

### macOS

**Fully Supported:**
- CPU temperature via IOKit (through `psutil`)
- CPU usage via `psutil`
- Memory and disk usage

**Limitations:**
- System load: macOS doesn't provide traditional load average
- Security checks: Limited (no `/var/log/auth.log`)
- Some temperature sensors may be unavailable

**Workarounds:**
- Use CPU usage and memory pressure as alternatives to system load
- For security checks, consider integrating with macOS security tools

### Cross-Platform Considerations

1. **Testing**: Test on each target platform
2. **Dependencies**: Different packages may be needed per OS
3. **Logging**: Log paths vary by OS
4. **Services**: systemd vs launchd vs services.msc

### Virtual Machines and Containers

**Cloud VMs:**
- CPU temperature may not be available (virtual sensors)
- Host-level metrics aggregated
- Container-based temperature sensors can be unreliable

**Containers:**
- Limited access to host system metrics
- CPU usage is relative to container limits
- Temperature sensors unavailable
- Requires privileged mode for full access

**Recommendations:**
- Use CPU usage and memory as primary metrics for VMs/containers
- Monitor host system for physical temperature
- Consider host-level monitoring for hypervisor

## Security Implications

### XML-RPC Security Considerations

**WARNING**: XML-RPC is not encrypted by default and should only be used in trusted networks.

#### Risks

1. **Unencrypted Communication**: All data transmitted in plain text
2. **No Authentication**: Default XML-RPC has no built-in authentication
3. **Command Injection**: Malicious clients could potentially exploit vulnerabilities
4. **Information Disclosure**: System details exposed to anyone who can reach the port

#### Mitigation Strategies

**1. Network Isolation**
```bash
# Use firewall to restrict access
sudo ufw allow from 192.168.1.0/24 to any port 9000

# Or use SSH tunnel for secure access
ssh -L 9000:localhost:9000 user@monitored-system
```

**2. VPN or Private Network**
- Deploy on internal network only
- Use VPN for remote access
- Never expose agents to public internet

**3. XML-RPC Authentication (Basic Implementation)**

Create a custom XML-RPC server with authentication:

```python
import base64

class AuthenticatedAgent:
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def _authenticate(self, auth_header):
        if not auth_header:
            return False
        try:
            encoded = auth_header.split(' ')[1]
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
            return username == self.username and password == self.password
        except:
            return False
    
    def get_metrics(self, auth_header=""):
        if not self._authenticate(auth_header):
            raise Exception("Authentication required")
        return self._get_metrics()
```

**4. Connection Limiting**
```python
# Limit concurrent connections
self.server = ThreadedXMLRPCServer(
    (self.host, self.port), 
    requestHandler=self.limit_connections
)
```

**5. IP Whitelisting**

Modify the collector to only connect to approved IPs:

```python
def connect(self):
    allowed_ips = ["192.168.1.100", "192.168.1.101"]
    if self.host not in allowed_ips:
        raise SecurityError("IP not in whitelist")
```

### Data Security

**1. Log File Permissions**
```bash
# Restrict log file access
chmod 640 /var/log/monitoring/collector.log
chown monitor:monitor /var/log/monitoring/collector.log
```

**2. Database Security**
```sql
-- Use strong passwords
CREATE USER 'monitor'@'localhost' IDENTIFIED BY 'complex_random_password';

-- Grant minimal privileges
GRANT SELECT, INSERT, UPDATE ON monitoring.* TO 'monitor'@'localhost';

-- Encrypt database at rest
-- Enable MySQL SSL connections
```

**3. Configuration Security**
```bash
# Restrict config file access
chmod 640 config/config.ini
chown monitor:monitor config/config.ini
```

### Network Security

**1. Firewall Rules**
```bash
# Allow only collector to agent connections
sudo ufw allow from COLLECTOR_IP to any port 9000
sudo ufw deny 9000

# Log dropped packets
sudo ufw logging on
```

**2. SSH Tunneling**
```bash
# Create SSH tunnel for secure connection
ssh -L 9000:localhost:9000 agent-user@agent-server

# Update config to use localhost
agent1 = localhost:9000
```

**3. VPN Setup**
- Deploy on internal VLAN
- Use VPN for remote monitoring
- Isolate monitoring network

### Production Recommendations

1. **Never expose agents to public internet**
2. **Use VPN or SSH tunnels for remote access**
3. **Implement authentication if network cannot be secured**
4. **Regularly update system and dependencies**
5. **Monitor agent logs for suspicious activity**
6. **Use TLS/SSL certificates if using HTTP proxies**
7. **Implement rate limiting on agent connections**
8. **Keep detailed audit logs**

### Security Monitoring

Add security monitoring for the monitoring system itself:

```python
# Monitor for brute force attempts
def check_agent_access_log():
    with open("/var/log/monitoring/collector.log") as f:
        for line in f:
            if "Failed to connect" in line:
                # Alert on repeated failures
                pass
```

## Troubleshooting

### Common Issues

**1. Agent Not Connecting**

```bash
# Check if agent is running
ps aux | grep monitoring.agent

# Check network connectivity
telnet AGENT_IP 9000

# Check agent logs
tail -f /var/log/monitoring/agent.log
```

**2. Temperature Sensors Not Available**

```bash
# Check thermal zones (Linux)
ls -la /sys/class/thermal/

# Check if sensors are enabled (Linux)
sensors-detect

# Check psutil temperature support
python3 -c "import psutil; print(psutil.sensors_temperatures())"
```

**3. MySQL Connection Failures**

```bash
# Test MySQL connection
mysql -u monitor -p -h localhost monitoring

# Check MySQL service
sudo systemctl status mysql

# Check network connectivity
netstat -an | grep 3306
```

**4. Permission Issues**

```bash
# Fix log directory permissions
sudo chown -R monitor:monitor /var/log/monitoring
sudo chmod -R 755 /var/log/monitoring

# Fix configuration file
chmod 640 config/config.ini
```

**5. Graphs Not Generated**

```bash
# Check matplotlib backend
python3 -c "import matplotlib; print(matplotlib.get_backend())"

# Install missing dependencies
pip install matplotlib seaborn

# Check output directory permissions
ls -la /var/log/monitoring/graphs/
```

### Debugging Steps

**1. Enable Debug Logging**
```ini
[general]
log_level = DEBUG
```

**2. Test Agent Manually**
```bash
# Test XML-RPC connection
python3 -c "
import xmlrpc.client
proxy = xmlrpc.client.ServerProxy('http://localhost:9000/')
print(proxy.ping())
print(proxy.get_metrics())
"
```

**3. Test Collector Configuration**
```bash
# Validate config file
python3 -c "
import configparser
c = configparser.ConfigParser()
c.read('config/config.ini')
print('Agents:', c.items('agents'))
"

# List known agents
python3 -c "
from src.monitoring.storage import create_storage
s = create_storage('log')
print('Known agents:', s.get_agents())
"
```

**4. Check System Resources**
```bash
# Check disk space
df -h /var/log/monitoring

# Check memory usage
free -h

# Check CPU usage
top
```

### Log Analysis

**Common Log Patterns:**

```
INFO - Collector started
INFO - Monitoring 3 agent(s)
INFO - Loaded agent: server1 at 192.168.1.100:9000
WARNING - ALERT [warning]: CPU temperature high: 75°C
ERROR - Failed to connect to server1: Connection refused
```

**Alert Patterns:**
- `ALERT [warning]`: Threshold exceeded
- `ALERT [critical]`: Critical threshold exceeded
- `Failed to connect`: Agent unreachable
- `Failed to get metrics`: Agent response error

### Performance Tuning

**1. Adjust Polling Interval**
```ini
[general]
poll_interval = 30  # Increase to reduce load
```

**2. Optimize Database**
```sql
-- Add indexes if missing
CREATE INDEX idx_metric_type_time ON metrics(metric_type, timestamp);
```

**3. Archive Old Data**
```bash
# Archive and delete old metrics
find /var/log/monitoring/data -name "*.jsonl" -mtime +30 -exec gzip {} \;
```

**4. Reduce Graph Detail**
```ini
[visualization]
graph_width = 8
graph_height = 6
```

## Advanced Configuration

### Custom Metrics

Extend the agent to collect custom metrics:

```python
def get_custom_metric(self):
    # Your custom metric collection logic
    return value

# Register the method in XML-RPC
class Agent:
    # ... existing code ...
    
    def get_all_metrics(self):
        metrics = self.metrics_collector.get_all_metrics()
        metrics['custom_metric'] = self.get_custom_metric()
        return metrics
```

### Custom Threshold Checks

Extend threshold monitoring:

```python
class CustomThresholdMonitor(ThresholdMonitor):
    def check_disk_usage(self, metrics, agent_name):
        alerts = []
        disk = metrics.get('disk', {})
        if disk.get('percent', 0) > 90:
            alerts.append({
                'agent': agent_name,
                'type': 'disk_usage',
                'severity': 'critical',
                'message': f'Disk usage critical: {disk["percent"]}%'
            })
        return alerts
```

### Database Replication

For high availability, set up MySQL replication:

```sql
-- Master configuration
-- Add to my.cnf:
-- server-id=1
-- log-bin=mysql-bin
-- binlog-do-db=monitoring

-- Create replication user
CREATE USER 'repl'@'%' IDENTIFIED BY 'replicate_password';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
```

### Distributed Collectors

Run multiple collectors for redundancy:

```bash
# Collector 1 - monitors agents 1-5
[agents]
agent1 = 192.168.1.100:9000
agent2 = 192.168.1.101:9000

# Collector 2 - monitors agents 6-10
[agents]
agent6 = 192.168.1.105:9000
agent7 = 192.168.1.106:9000
```

### Alert Integration

Integrate with external alerting systems:

```python
def send_slack_alert(self, alert):
    webhook_url = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    message = f"Alert: {alert['message']}"
    # Send to Slack
```

### API Endpoints

Expose metrics via web API:

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/metrics/<agent_name>')
def get_agent_metrics(agent_name):
    metrics = storage.get_metrics(agent_name)
    return jsonify(metrics)

@app.route('/api/alerts')
def get_alerts():
    # Return current alerts
    return jsonify(current_alerts)
```

## Conclusion

This monitoring system provides a flexible, scalable solution for monitoring multiple systems. While XML-RPC provides simplicity, always consider security implications and use appropriate network protections.

For production deployments:
- Use network isolation and VPN
- Implement proper authentication
- Regular security audits
- Monitor system performance
- Keep dependencies updated

The modular design allows for easy extension and customization based on specific monitoring needs.