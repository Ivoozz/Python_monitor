#!/bin/bash

# Agent startup script
# This script starts the monitoring agent on a system being monitored

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
HOST="0.0.0.0"
PORT=9000
LOG_LEVEL="INFO"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --host HOST       Host to bind to (default: 0.0.0.0)"
    echo "  -p, --port PORT       Port to listen on (default: 9000)"
    echo "  -l, --log-level LVL   Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)"
    echo "  --help                Show this help message"
    echo ""
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi
    
    # Check required Python packages
    REQUIRED_PACKAGES=("psutil" "xmlrpc" "logging")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            echo -e "${RED}Error: Python package '$package' is not installed${NC}"
            echo "Please install required packages:"
            echo "  pip install psutil"
            exit 1
        fi
    done
    
    echo -e "${GREEN}All dependencies satisfied${NC}"
}

start_agent() {
    echo -e "${GREEN}Starting Monitoring Agent...${NC}"
    echo "Host: $HOST"
    echo "Port: $PORT"
    echo "Log Level: $LOG_LEVEL"
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Change to project directory
    cd "$PROJECT_ROOT"
    
    # Start the agent
    python3 -m src.monitoring.agent \
        --host "$HOST" \
        --port "$PORT" \
        --log-level "$LOG_LEVEL"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Validate port
if [[ ! "$PORT" =~ ^[0-9]+$ ]] || [[ "$PORT" -lt 1 ]] || [[ "$PORT" -gt 65535 ]]; then
    echo -e "${RED}Error: Invalid port number: $PORT${NC}"
    exit 1
fi

# Check if running as root (not recommended for security)
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}Warning: Running as root. This is not recommended.${NC}"
    echo "Consider creating a dedicated user for the monitoring agent."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check dependencies
check_dependencies

# Create log directory if it doesn't exist
mkdir -p /var/log/monitoring

# Start the agent
start_agent