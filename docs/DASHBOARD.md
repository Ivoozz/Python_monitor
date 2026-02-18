# Monitoring Dashboard

A Flask-based web dashboard for the Python monitoring system with real-time metrics, auto-refreshing UI, and device management.

## Features

- **Real-time Monitoring**: Auto-refreshing metrics every 5 seconds
- **Device Management**: Add/remove monitored devices via web interface
- **Live Graphs**: Canvas-based graphs for CPU, memory, disk, and system load
- **Alert System**: Visual notifications for threshold breaches
- **Persistent Configuration**: Device settings saved to JSON
- **Responsive Design**: Works on desktop and mobile devices
- **Pure Python/JavaScript**: No external JavaScript dependencies

## Quick Start

### 1. Install Dependencies

```bash
pip install flask
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Start the Dashboard

```bash
chmod +x scripts/start_dashboard.sh
./scripts/start_dashboard.sh
```

The dashboard will be available at `http://localhost:5000`

### 3. Add Devices

Use the web form to add devices:
- **Name**: A friendly name (e.g., "web-server-01")
- **IP Address**: The agent's IP address (e.g., "192.168.1.100")
- **Port**: The agent's port (default: 8000)

## API Endpoints

### Devices

- `GET /api/devices` - List all devices
- `POST /api/devices` - Add a new device
  ```json
  {
    "name": "web-server-01",
    "host": "192.168.1.100",
    "port": 8000
  }
  ```
- `DELETE /api/devices/<name>` - Remove a device
- `POST /api/devices/<name>/toggle` - Enable/disable a device
  ```json
  {
    "enabled": false
  }
  ```

### Metrics

- `GET /api/metrics` - Collect and return latest metrics from all devices
- `GET /api/metrics/cache` - Return cached metrics without collecting

### Health

- `GET /api/health` - Health check endpoint

## Configuration

### Environment Variables

- `DASHBOARD_HOST` - Host to bind to (default: 0.0.0.0)
- `DASHBOARD_PORT` - Port to listen on (default: 5000)
- `FLASK_DEBUG` - Enable debug mode (default: false)

Example:
```bash
DASHBOARD_PORT=8080 DASHBOARD_HOST=127.0.0.1 ./scripts/start_dashboard.sh
```

### Device Configuration

Devices are stored in `config/dashboard_devices.json`:
```json
[
  {
    "name": "server-01",
    "host": "192.168.1.100",
    "port": 8000,
    "added_at": "2024-02-18T12:00:00",
    "enabled": true
  }
]
```

### Metrics Cache

Latest metrics are cached in `storage/latest_metrics.json` for persistence.

## Metrics Display

The dashboard displays the following metrics for each device:

### System Metrics
- **CPU Usage**: Percentage of CPU utilization
- **Memory Usage**: Memory percentage and used GB
- **System Load**: 1-minute load average
- **Disk Usage**: Disk percentage and used GB
- **CPU Temperature**: Temperature in Celsius (if available)

### Graphs
Live graphs show the average of all online devices:
- CPU Usage over time
- Memory Usage over time
- System Load over time
- Disk Usage over time

Each graph displays the last 20 data points.

### Alerts
Alerts are shown when metrics exceed thresholds:
- CPU Usage > 80%
- CPU Temperature > 70°C
- System Load (1min) > 2.0
- Memory Usage > 85%
- Disk Usage > 90%

## Architecture

### Components

1. **Flask Application** (`dashboard.py`)
   - Routes and API endpoints
   - Device management
   - Metrics collection

2. **Device Manager**
   - Loads/saves device configuration
   - Validates device entries
   - Prevents duplicates

3. **Metrics Collector**
   - Queries XML-RPC agents
   - Caches metrics in memory
   - Persists to JSON file

4. **Frontend**
   - HTML template (`templates/dashboard.html`)
   - JavaScript (`static/js/dashboard.js`)
   - Styles (`static/css/styles.css`)

### Data Flow

```
Browser → Flask App → XML-RPC Agent → Metrics
                ↓
            Device Manager
                ↓
            Metrics Cache
                ↓
            JSON Storage
```

## Security Considerations

- The dashboard uses XML-RPC which is NOT encrypted
- Only expose on trusted networks
- Use firewall rules to restrict access
- Consider adding authentication for production use
- Never expose agents to public internet

## Troubleshooting

### Dashboard Won't Start

```bash
# Check if port is available
netstat -an | grep 5000

# Check Flask installation
python3 -c "import flask; print('OK')"

# Check logs
tail -f logs/monitor_agent.log
```

### Devices Show as Offline

```bash
# Test agent connection manually
python3 -c "
import xmlrpc.client
proxy = xmlrpc.client.ServerProxy('http://192.168.1.100:8000/')
print(proxy.ping())
"

# Check if agent is running
ps aux | grep agent_server.py
```

### Graphs Not Updating

- Check browser console for JavaScript errors
- Verify `/api/metrics` endpoint returns data
- Ensure devices are online and reporting metrics

### Permission Errors

```bash
# Create storage directory with proper permissions
sudo mkdir -p /home/engine/project/storage
sudo chown $USER:$USER /home/engine/project/storage
```

## Integration with Existing System

The dashboard integrates with the existing monitoring system:

1. **Agents**: Uses existing XML-RPC agents (same API)
2. **Collector**: Can run alongside the collector
3. **Storage**: Uses JSON storage (independent of collector storage)
4. **Configuration**: Separate device management (can sync with collector config)

You can run both the collector and dashboard simultaneously:

```bash
# Terminal 1 - Collector
./scripts/start_collector.sh

# Terminal 2 - Dashboard
./scripts/start_dashboard.sh
```

## Development

### Running in Debug Mode

```bash
FLASK_DEBUG=true python3 dashboard.py
```

### File Structure

```
dashboard.py              # Flask application
templates/
  └── dashboard.html      # Main template
static/
  ├── css/
  │   └── styles.css      # Stylesheet
  └── js/
      └── dashboard.js    # JavaScript logic
config/
  └── dashboard_devices.json  # Device configuration
storage/
  └── latest_metrics.json     # Metrics cache
scripts/
  └── start_dashboard.sh     # Startup script
```

## Future Enhancements

Potential improvements:
- User authentication and authorization
- Historical data graphs
- Export metrics to CSV/JSON
- Email/SMS alerts
- Custom threshold configuration
- Dark mode theme
- WebSocket support for real-time updates
- Integration with Prometheus/Grafana

## License

Same as the main monitoring system.
