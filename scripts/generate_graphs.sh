#!/bin/bash

# Visualization script
# This script generates graphs from monitoring data

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
CONFIG="config/config.ini"
HOURS=24
AGENT=""
COMPARE=""
METRIC="cpu_usage"
OUTPUT_DIR=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --config FILE      Config file path (default: config/config.ini)"
    echo "  -h, --hours HOURS      Hours of history (default: 24)"
    echo "  -a, --agent NAME       Generate graphs for specific agent"
    echo "  --compare AGENTS       Compare multiple agents (space-separated list)"
    echo "  -m, --metric TYPE      Metric to compare (cpu_usage, cpu_temperature, system_load)"
    echo "  -o, --output-dir DIR   Output directory for graphs"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -a server1                    # Generate graphs for agent 'server1'"
    echo "  $0 --compare server1 server2     # Compare server1 and server2"
    echo "  $0 -o /tmp/graphs                # Save graphs to /tmp/graphs"
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi
    
    # Check required Python packages
    REQUIRED_PACKAGES=("matplotlib" "seaborn" "numpy")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            echo -e "${RED}Error: Python package '$package' is not installed${NC}"
            echo "Please install with: pip install $package"
            exit 1
        fi
        echo -e "${GREEN}[✓]${NC} $package"
    done
    
    echo -e "${GREEN}All dependencies satisfied${NC}"
}

generate_visualizations() {
    echo -e "${GREEN}Generating visualizations...${NC}"
    
    # Change to project directory
    cd "$PROJECT_ROOT"
    
    # Build command
    CMD="python3 -m src.monitoring.visualization --config $CONFIG --hours $HOURS"
    
    if [[ -n "$AGENT" ]]; then
        CMD="$CMD --agent $AGENT"
    fi
    
    if [[ -n "$COMPARE" ]]; then
        CMD="$CMD --compare $COMPARE"
    fi
    
    if [[ -n "$METRIC" ]]; then
        CMD="$CMD --metric $METRIC"
    fi
    
    if [[ -n "$OUTPUT_DIR" ]]; then
        CMD="$CMD --output-dir $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi
    
    echo "Running: $CMD"
    echo ""
    
    # Execute command
    $CMD
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG="$2"
            shift 2
            ;;
        -h|--hours)
            HOURS="$2"
            shift 2
            ;;
        -a|--agent)
            AGENT="$2"
            shift 2
            ;;
        --compare)
            shift
            COMPARE=""
            while [[ $# -gt 0 && ! $1 =~ ^-- ]]; do
                COMPARE="$COMPARE $1"
                shift
            done
            COMPARE=$(echo $COMPARE | tr -s ' ')
            continue
            ;;
        -m|--metric)
            METRIC="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
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

# Validate config file
if [[ ! -f "$CONFIG" ]]; then
    ALT_CONFIG="$PROJECT_ROOT/$CONFIG"
    if [[ -f "$ALT_CONFIG" ]]; then
        CONFIG="$ALT_CONFIG"
    else
        echo -e "${YELLOW}Warning: Config file not found: $CONFIG${NC}"
        echo "Using default settings..."
    fi
fi

# Validate metric type
VALID_METRICS=("cpu_usage" "cpu_temperature" "system_load")
if [[ -n "$METRIC" && ! " ${VALID_METRICS[@]} " =~ " ${METRIC} " ]]; then
    echo -e "${RED}Error: Invalid metric: $METRIC${NC}"
    echo "Valid metrics: ${VALID_METRICS[*]}"
    exit 1
fi

# Check dependencies
check_dependencies

# Generate visualizations
generate_visualizations