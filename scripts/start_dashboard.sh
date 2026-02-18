#!/bin/bash
# Start the Flask monitoring dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check if Flask is installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Flask not installed. Installing..."
    pip install flask
fi

# Set default port if not specified
PORT=${DASHBOARD_PORT:-5000}
HOST=${DASHBOARD_HOST:-0.0.0.0}

echo "Starting monitoring dashboard..."
echo "Dashboard will be available at: http://$HOST:$PORT"
echo ""
echo "Press Ctrl+C to stop"

# Start the dashboard
python3 dashboard.py
