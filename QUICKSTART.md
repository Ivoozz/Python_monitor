# Monitoring System Quick Start Guide

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- psutil (system metrics)
- matplotlib (graphing)
- seaborn (graph styling)
- numpy (numerical operations)
- pymysql (optional, for MySQL storage)
- flask (web dashboard)

### 2. Set Up Configuration

Copy the example configuration:

```bash
cp config/config.ini.example config/config.ini
```

Edit `config/config.ini` to add your agents:

```ini
[agents]
web_server = 192.168.1.100:9000
db_server = 192.168.1.101:9000
```

## Basic Usage

### Start Agent on Each System to Monitor

On each system you want to monitor:

```bash
chmod +x scripts/start_agent.sh
./scripts/start_agent.sh
```

The agent will start on port 9000 by default.

### Start Collector on Monitoring System

On your monitoring server:

```bash
chmod +x scripts/start_collector.sh
./scripts/start_collector.sh
```

The collector will start polling configured agents.

### Start Web Dashboard

The web dashboard provides a real-time, auto-refreshing interface for monitoring your systems:

```bash
chmod +x scripts/start_dashboard.sh
./scripts/start_dashboard.sh
```

The dashboard will start on port 5000 by default. Access it at:
- `http://localhost:5000` (local access)
- `http://<your-server-ip>:5000` (remote access)

**Dashboard Features:**
- 📊 Real-time metrics with auto-refresh (5-second intervals)
- ➕ Add/remove monitored devices via web form
- 📈 Live graphs for CPU, memory, disk, and system load
- ⚠️ Alert notifications for threshold breaches
- 💾 Persistent device configuration (saved to JSON)
- 🎨 Responsive design for desktop and mobile

**Using the Dashboard:**
1. Open the dashboard in your browser
2. Use the "Add Monitored Device" form to add agents by IP/port
3. View live metrics and graphs that update automatically
4. Enable/disable devices or remove them from monitoring
5. Click "Refresh Now" to manually update metrics

**Custom Dashboard Port:**
```bash
DASHBOARD_PORT=8080 ./scripts/start_dashboard.sh
```

### Generate Graphs

```bash
chmod +x scripts/generate_graphs.sh
./scripts/generate_graphs.sh
```

Graphs will be saved to `/var/log/monitoring/graphs/`

## Testing

### Test a Single Agent

```bash
python3 -c "
import xmlrpc.client
proxy = xmlrpc.client.ServerProxy('http://localhost:9000/')
print('Ping:', proxy.ping())
metrics = proxy.get_metrics()
print('CPU Temperature:', metrics.get('cpu_temperature'))
print('CPU Usage:', metrics.get('cpu_usage'))
"
```

### Check Collector Logs

```bash
tail -f /var/log/monitoring/collector.log
```

## MySQL Setup (Optional)

If you want to use MySQL storage:

1. Install MySQL server
2. Create database and user:
   ```bash
   mysql -u root -p < sql/init_db.sql
   ```
3. Update `config/config.ini`:
   ```ini
   [storage]
   backend = mysql
   ```

## Common Tasks

### Add a New Monitored System

1. On the new system, run the agent:
   ```bash
   ./scripts/start_agent.sh
   ```
2. Add to `config/config.ini`:
   ```ini
   [agents]
   new_server = 192.168.1.102:9000
   ```
3. Restart collector:
   ```bash
   sudo systemctl restart monitoring-collector
   ```

### Check System Status

```bash
# Check if agents are running
ps aux | grep monitoring.agent

# Check collector status
sudo systemctl status monitoring-collector

# View recent logs
tail -50 /var/log/monitoring/collector.log
```

### Generate Specific Graphs

```bash
# Graphs for one agent
./scripts/generate_graphs.sh --agent web_server

# Last 48 hours
./scripts/generate_graphs.sh --hours 48

# Compare multiple agents
./scripts/generate_graphs.sh --compare web_server db_server
```

## Troubleshooting

### Agent Won't Start

```bash
# Check port availability
netstat -an | grep 9000

# Check if port is already in use
lsof -i :9000
```

### Collector Can't Connect

```bash
# Test connectivity
telnet 192.168.1.100 9000

# Check agent is running
curl http://192.168.1.100:9000
```

### No Graphs Generated

```bash
# Check if matplotlib works
python3 -c "import matplotlib; print('OK')"

# Check output directory
ls -la /var/log/monitoring/graphs/
```

### Temperature Not Available

This is normal on some systems:
- Virtual machines often lack temperature sensors
- Some hardware may not expose temperature data

The system will gracefully handle missing temperature readings.

## Next Steps

- Read full documentation: `docs/README.md`
- Configure threshold alerts
- Set up automated graph generation
- Deploy as systemd services
- Configure MySQL for production use
- Set up web dashboard for visualization

## Security Notes

⚠️ **Important Security Considerations:**

- XML-RPC is NOT encrypted - use only on trusted networks
- Never expose agents to public internet
- Use VPN or SSH tunnels for remote access
- Configure firewall rules to restrict access
- See `docs/README.md` section "Security Implications" for details