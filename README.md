# Python Monitoring System

A cross-platform Python-only monitoring solution with Flask dashboard, auto-refresh, device management UI, and XML-RPC agents.

## Features

- 📊 **Flask Dashboard**: Web-based monitoring interface with auto-refresh
- ➕ **Device Management**: Add/remove monitored systems via web UI
- 📈 **Live Graphs**: Real-time CPU, memory, disk, and load visualization
- 🔄 **Auto-Refresh**: 5-second polling intervals for live updates
- 🔌 **XML-RPC Agents**: Lightweight agents for systems being monitored
- 🌐 **Cross-Platform**: Works on Windows, Ubuntu, and Debian
- 📱 **Responsive Design**: Mobile-friendly dashboard interface

## Quick Install (One-Liner)

### Linux (Ubuntu/Debian)

```bash
curl -sSL https://raw.githubusercontent.com/Ivoozz/Python_monitor/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
Invoke-Expression (Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/Ivoozz/Python_monitor/main/install.ps1').Content
```

> **Note for Windows users**: If you encounter execution policy errors, first run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

> **pip behaviour**: The Windows installer creates a fresh virtual environment and installs
> requirements directly — it does **not** upgrade pip inside the venv, so you will never
> see pip self-upgrade prompts or warnings during installation.

## Installation Types

The installer will prompt you to choose between:

### System A - Monitor + Dashboard
Install this on your central monitoring server. Includes:
- Flask web dashboard with auto-refresh
- Device management UI
- Metrics collection from agents
- Live graphs and alerting

### System B - Agent Only
Install this on each machine you want to monitor. Includes:
- XML-RPC agent service
- System metrics collection (CPU, memory, disk, temperature)
- Security threat detection
- Automatic reporting to dashboard

## Manual Installation

If you prefer manual installation:

### 1. Clone the Repository

```bash
git clone https://github.com/Ivoozz/Python_monitor.git
cd Python_monitor
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Dashboard (System A)

```bash
python dashboard.py
```

Access the dashboard at: http://localhost:5000

### 5. Run Agent (System B)

```bash
python agent/agent_server.py
```

## Usage

### Starting the Dashboard

After installation:

```bash
# Linux
monitor-dashboard

# Windows
monitor-dashboard.bat
```

Environment variables:
- `DASHBOARD_HOST`: Bind address (default: 0.0.0.0)
- `DASHBOARD_PORT`: Port number (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: false)

### Starting the Agent

After installation:

```bash
# Linux
monitor-agent

# Windows
monitor-agent.bat
```

Environment variables:
- `AGENT_HOST`: Bind address (default: 0.0.0.0)
- `AGENT_PORT`: Port number (default: 8000)
- `AGENT_LOG_LEVEL`: Logging level (default: INFO)

### Adding Devices

1. Open the dashboard in your browser
2. Use the "Add Monitored Device" form
3. Enter:
   - **Name**: A friendly name for the device
   - **IP Address**: The IP of the agent machine
   - **Port**: The agent port (default: 8000)
4. Click "Add Device"

The dashboard will automatically start collecting metrics from the new device.

## API Endpoints

### Dashboard API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard HTML interface |
| GET | `/api/devices` | List all monitored devices |
| POST | `/api/devices` | Add a new device |
| DELETE | `/api/devices/<name>` | Remove a device |
| POST | `/api/devices/<name>/toggle` | Enable/disable a device |
| GET | `/api/metrics` | Get current metrics from all devices |
| GET | `/api/metrics/cache` | Get cached metrics |
| GET | `/api/health` | Health check |

### Agent API (XML-RPC)

Methods available at `http://<agent-ip>:<port>/`

- `ping()` - Test connectivity
- `get_metrics()` - Get all system metrics
- `get_temperature()` - Get CPU temperature
- `get_cpu()` - Get CPU usage and load
- `get_security_status()` - Get security threat status

## Configuration

### Dashboard Configuration

Configuration files are stored in:
- Linux: `~/.config/python-monitor/`
- Windows: `%LOCALAPPDATA%\PythonMonitor\Config\`

Key files:
- `dashboard.env` - Environment variables
- `devices.json` - Monitored devices list
- `metrics.json` - Latest collected metrics

### Agent Configuration

- `agent.env` - Environment variables
- `agent.json` - Agent settings (port, interval, etc.)

## Project Structure

```
Python_monitor/
├── dashboard.py              # Flask dashboard application
├── agent/
│   └── agent_server.py       # XML-RPC agent
├── templates/
│   └── dashboard.html        # Dashboard HTML template
├── static/
│   ├── css/
│   │   └── styles.css        # Dashboard styles
│   └── js/
│       └── dashboard.js      # Auto-refresh and graphs
├── config/
│   ├── config.ini            # Main configuration
│   ├── agent_config.json     # Agent defaults
│   └── dashboard_devices.json # Devices list
├── scripts/
│   ├── start_agent.sh        # Agent startup script
│   ├── start_dashboard.sh    # Dashboard startup script
│   └── start_collector.sh    # Collector startup script
├── install.sh                # Linux installer
├── install.ps1               # Windows installer
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Systemd Services (Linux)

To run as a systemd service:

### Dashboard Service

```bash
sudo cp ~/.config/python-monitor/systemd/monitor-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable monitor-dashboard
sudo systemctl start monitor-dashboard
```

### Agent Service

```bash
sudo cp ~/.config/python-monitor/systemd/monitor-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable monitor-agent
sudo systemctl start monitor-agent
```

## Windows Services

To run as a Windows service, use [NSSM](https://nssm.cc/):

```powershell
# Download and extract NSSM, then:
nssm install PythonMonitorDashboard
# Set Path: %LOCALAPPDATA%\PythonMonitor\venv\Scripts\python.exe
# Set Arguments: %LOCALAPPDATA%\PythonMonitor\dashboard.py
```

Or use the provided service install script after running the main installer.

## Security Notes

⚠️ **Important Security Considerations:**

- XML-RPC communication is NOT encrypted
- Use only on trusted networks (LAN/VPN)
- Never expose agents directly to the public internet
- Use firewall rules to restrict access to agent ports
- Consider SSH tunnels or VPN for remote monitoring

## Troubleshooting

### Dashboard won't start

```bash
# Check if port is in use
lsof -i :5000

# Use a different port
DASHBOARD_PORT=8080 monitor-dashboard
```

### Agent connection failed

```bash
# Test connectivity
telnet <agent-ip> 8000

# Check agent is running
curl http://<agent-ip>:8000
```

### Python module not found

```bash
# Reinstall in virtual environment
cd ~/.local/share/python-monitor
source venv/bin/activate
pip install -r requirements.txt
```

## Requirements

- Python 3.7+
- psutil
- Flask 3.0+
- (Optional) matplotlib, seaborn for graph generation

## Development

### Running Tests

```bash
python test_system.py
```

### Demo Mode

```bash
python demo.py
```

## License

MIT License - See repository for details.

## Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- Tests pass
- Documentation is updated

---

**Quick Links:**
- [Issues](https://github.com/Ivoozz/Python_monitor/issues)
- [Releases](https://github.com/Ivoozz/Python_monitor/releases)
