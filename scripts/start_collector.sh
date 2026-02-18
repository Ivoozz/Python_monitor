#!/bin/bash

# Collector startup script
# This script starts the monitoring collector on the central monitoring system

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
CONFIG="config/config.ini"
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
    echo "  -c, --config FILE    Config file path (default: config/config.ini)"
    echo "  -l, --log-level LVL  Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)"
    echo "  --help               Show this help message"
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
    REQUIRED_PACKAGES=("xmlrpc" "logging" "configparser" "concurrent.futures")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            echo -e "${RED}Error: Python package '$package' is not installed${NC}"
            exit 1
        fi
    done
    
    # Optional packages
    OPTIONAL_PACKAGES=("psutil" "pymysql" "matplotlib" "seaborn")
    for package in "${OPTIONAL_PACKAGES[@]}"; do
        if python3 -c "import $package" &> /dev/null; then
            echo -e "${GREEN}[✓]${NC} $package"
        else
            echo -e "${YELLOW}[!]${NC} $package (optional)"
        fi
    done
    
    echo -e "${GREEN}Dependencies checked${NC}"
}

create_directories() {
    echo -e "${YELLOW}Creating required directories...${NC}"
    
    # Create log directory
    mkdir -p /var/log/monitoring
    
    # Create data directory
    mkdir -p /var/log/monitoring/data
    
    # Create graphs directory
    mkdir -p /var/log/monitoring/graphs
    
    echo -e "${GREEN}Directories created${NC}"
}

start_collector() {
    echo -e "${GREEN}Starting Monitoring Collector...${NC}"
    echo "Config: $CONFIG"
    echo "Log Level: $LOG_LEVEL"
    echo "Press Ctrl+C to stop"
    echo ""
    
    # Change to project directory
    cd "$PROJECT_ROOT"
    
    # Start the collector
    python3 -m src.monitoring.collector \
        --config "$CONFIG" \
        --log-level "$LOG_LEVEL"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG="$2"
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

# Validate config file exists
if [[ ! -f "$CONFIG" ]]; then
    # Try relative to project root
    ALT_CONFIG="$PROJECT_ROOT/$CONFIG"
    if [[ -f "$ALT_CONFIG" ]]; then
        CONFIG="$ALT_CONFIG"
    else
        echo -e "${RED}Error: Config file not found: $CONFIG${NC}"
        exit 1
    fi
fi

# Check if running as root (not recommended for security)
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}Warning: Running as root. This is not recommended.${NC}"
    echo "Consider creating a dedicated user for the monitoring collector."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check dependencies
check_dependencies

# Create directories
create_directories

# Start the collector
start_collector