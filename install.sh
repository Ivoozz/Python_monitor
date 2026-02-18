#!/bin/bash
#
# One-line cross-platform installer for Python Monitoring System
# Usage: curl -sSL https://raw.githubusercontent.com/Ivoozz/Python_monitor/main/install.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/Ivoozz/Python_monitor.git"
INSTALL_DIR="${HOME}/.local/share/python-monitor"
VENV_DIR="${INSTALL_DIR}/venv"
CONFIG_DIR="${HOME}/.config/python-monitor"

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║         Python Monitoring System Installer                   ║"
    echo "║         Cross-Platform: Linux (Ubuntu/Debian)                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_python() {
    print_info "Checking Python 3 installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3 found: $PYTHON_VERSION"
        
        # Check Python version (need 3.7+)
        MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 7 ]); then
            print_error "Python 3.7+ is required"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        echo ""
        echo "Please install Python 3.7 or higher:"
        echo "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install python3 python3-venv python3-pip"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_warning "pip3 not found. Attempting to install..."
        sudo apt-get update && sudo apt-get install -y python3-pip
    fi
}

install_system_dependencies() {
    print_info "Installing system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update -qq
        sudo apt-get install -y -qq python3-venv python3-pip git 2>/dev/null || {
            print_warning "Some dependencies may already be installed"
        }
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS/Fedora
        sudo yum install -y -q python3-venv python3-pip git 2>/dev/null || true
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -S --noconfirm python-virtualenv python-pip git 2>/dev/null || true
    else
        print_warning "Unknown package manager. Please ensure python3-venv and git are installed."
    fi
    
    print_success "System dependencies installed"
}

clone_or_update_repo() {
    print_info "Setting up installation directory..."
    
    mkdir -p "$(dirname "$INSTALL_DIR")"
    
    if [ -d "$INSTALL_DIR/.git" ]; then
        print_info "Existing installation found. Updating..."
        cd "$INSTALL_DIR"
        git pull --quiet
    else
        print_info "Cloning repository..."
        rm -rf "$INSTALL_DIR"
        git clone --depth 1 --quiet "$REPO_URL" "$INSTALL_DIR"
    fi
    
    print_success "Repository ready at $INSTALL_DIR"
}

create_virtualenv() {
    print_info "Creating Python virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        print_info "Existing virtual environment found. Updating..."
        rm -rf "$VENV_DIR"
    fi
    
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
    
    print_info "Installing Python packages..."
    "$VENV_DIR/bin/pip" install --upgrade pip --quiet
    "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" --quiet
    print_success "Python packages installed"
}

ask_installation_type() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Select installation type:"
    echo ""
    echo -e "  ${GREEN}[A]${NC} System A - Monitor + Dashboard (Central monitoring server)"
    echo "      Includes: Flask dashboard, metrics collector, web UI"
    echo "      Use this for the main monitoring machine"
    echo ""
    echo -e "  ${YELLOW}[B]${NC} System B - Agent only (System to be monitored)"
    echo "      Includes: XML-RPC agent that reports metrics"
    echo "      Install this on each machine you want to monitor"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    while true; do
        read -p "Enter your choice (A/B): " choice
        case $choice in
            [Aa]* )
                INSTALL_TYPE="agent"
                print_info "Selected: System A (Monitor + Dashboard)"
                return 0
                ;;
            [Bb]* )
                INSTALL_TYPE="monitor"
                print_info "Selected: System B (Agent only)"
                return 0
                ;;
            * )
                print_warning "Please enter A or B"
                ;;
        esac
    done
}

write_config() {
    print_info "Writing configuration..."
    
    mkdir -p "$CONFIG_DIR"
    
    # Create installation config
    cat > "$CONFIG_DIR/install.json" << EOF
{
    "install_type": "$INSTALL_TYPE",
    "install_dir": "$INSTALL_DIR",
    "venv_dir": "$VENV_DIR",
    "installed_at": "$(date -Iseconds)",
    "version": "1.0.0"
}
EOF
    
    if [ "$INSTALL_TYPE" = "agent" ]; then
        # Dashboard + Monitor config
        cat > "$CONFIG_DIR/dashboard.env" << EOF
# Python Monitor Dashboard Environment
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
FLASK_DEBUG=false
DEVICES_FILE=$CONFIG_DIR/devices.json
METRICS_FILE=$CONFIG_DIR/metrics.json
EOF
        
        # Copy default device list if not exists
        if [ ! -f "$CONFIG_DIR/devices.json" ]; then
            echo "[]" > "$CONFIG_DIR/devices.json"
        fi
        
        print_success "Dashboard configuration created"
    else
        # Agent config
        cat > "$CONFIG_DIR/agent.env" << EOF
# Python Monitor Agent Environment
AGENT_HOST=0.0.0.0
AGENT_PORT=8000
AGENT_LOG_LEVEL=INFO
AGENT_CONFIG=$CONFIG_DIR/agent.json
EOF
        
        # Copy default agent config if not exists
        if [ ! -f "$CONFIG_DIR/agent.json" ]; then
            cat > "$CONFIG_DIR/agent.json" << EOF
{
    "host": "0.0.0.0",
    "port": 8000,
    "check_interval": 30,
    "log_file": "$CONFIG_DIR/agent.log"
}
EOF
        fi
        
        print_success "Agent configuration created"
    fi
}

create_launcher_scripts() {
    print_info "Creating launcher scripts..."
    
    mkdir -p "$HOME/.local/bin"
    
    if [ "$INSTALL_TYPE" = "agent" ]; then
        # Dashboard launcher
        cat > "$HOME/.local/bin/monitor-dashboard" << EOF
#!/bin/bash
# Python Monitor Dashboard Launcher

source "$VENV_DIR/bin/activate"
export \$(grep -v '^#' "$CONFIG_DIR/dashboard.env" | xargs)
cd "$INSTALL_DIR"
python3 dashboard.py "\$@"
EOF
        chmod +x "$HOME/.local/bin/monitor-dashboard"
        
        # Create systemd service file
        mkdir -p "$CONFIG_DIR/systemd"
        cat > "$CONFIG_DIR/systemd/monitor-dashboard.service" << EOF
[Unit]
Description=Python Monitor Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$CONFIG_DIR/dashboard.env
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        print_success "Dashboard launcher created: monitor-dashboard"
    else
        # Agent launcher
        cat > "$HOME/.local/bin/monitor-agent" << EOF
#!/bin/bash
# Python Monitor Agent Launcher

source "$VENV_DIR/bin/activate"
export \$(grep -v '^#' "$CONFIG_DIR/agent.env" | xargs)
cd "$INSTALL_DIR"
python3 agent/agent_server.py "\$@"
EOF
        chmod +x "$HOME/.local/bin/monitor-agent"
        
        # Create systemd service file
        mkdir -p "$CONFIG_DIR/systemd"
        cat > "$CONFIG_DIR/systemd/monitor-agent.service" << EOF
[Unit]
Description=Python Monitor Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$CONFIG_DIR/agent.env
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/agent/agent_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        print_success "Agent launcher created: monitor-agent"
    fi
}

print_next_steps() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}               Installation Complete!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ "$INSTALL_TYPE" = "agent" ]; then
        echo -e "${BLUE}System A (Monitor + Dashboard) installed${NC}"
        echo ""
        echo "Quick Start:"
        echo "  1. Start the dashboard:"
        echo -e "     ${YELLOW}monitor-dashboard${NC}"
        echo ""
        echo "  2. Open your browser to:"
        echo -e "     ${YELLOW}http://localhost:5000${NC}"
        echo ""
        echo "  3. Add agents using the web UI or API"
        echo ""
        echo "Systemd Service (optional):"
        echo "  Copy service file:"
        echo -e "     ${YELLOW}sudo cp $CONFIG_DIR/systemd/monitor-dashboard.service /etc/systemd/system/${NC}"
        echo -e "     ${YELLOW}sudo systemctl enable --now monitor-dashboard${NC}"
    else
        echo -e "${BLUE}System B (Agent) installed${NC}"
        echo ""
        echo "Quick Start:"
        echo "  1. Start the agent:"
        echo -e "     ${YELLOW}monitor-agent${NC}"
        echo ""
        echo "  2. The agent will listen on port 8000"
        echo ""
        echo "  3. Add this machine to your dashboard:"
        echo -e "     IP: ${YELLOW}$(hostname -I | awk '{print $1}')${NC}, Port: ${YELLOW}8000${NC}"
        echo ""
        echo "Systemd Service (optional):"
        echo "  Copy service file:"
        echo -e "     ${YELLOW}sudo cp $CONFIG_DIR/systemd/monitor-agent.service /etc/systemd/system/${NC}"
        echo -e "     ${YELLOW}sudo systemctl enable --now monitor-agent${NC}"
    fi
    
    echo ""
    echo "Configuration files:"
    echo "  Install config: $CONFIG_DIR/install.json"
    if [ "$INSTALL_TYPE" = "agent" ]; then
        echo "  Dashboard env:  $CONFIG_DIR/dashboard.env"
        echo "  Devices:        $CONFIG_DIR/devices.json"
    else
        echo "  Agent env:      $CONFIG_DIR/agent.env"
        echo "  Agent config:   $CONFIG_DIR/agent.json"
    fi
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

main() {
    print_banner
    
    # Check if running interactively
    if [ -t 0 ]; then
        INTERACTIVE=true
    else
        INTERACTIVE=false
        print_warning "Running non-interactively. Please run with: curl ... | bash -s -- -i"
        # Default to agent for non-interactive
        INSTALL_TYPE="agent"
    fi
    
    check_python
    install_system_dependencies
    clone_or_update_repo
    create_virtualenv
    
    if [ "$INTERACTIVE" = true ]; then
        ask_installation_type
    fi
    
    write_config
    create_launcher_scripts
    print_next_steps
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)
            INSTALL_TYPE="agent"
            shift
            ;;
        --monitor)
            INSTALL_TYPE="monitor"
            shift
            ;;
        -h|--help)
            echo "Python Monitor Installer"
            echo ""
            echo "Usage:"
            echo "  curl -sSL https://raw.githubusercontent.com/Ivoozz/Python_monitor/main/install.sh | bash"
            echo ""
            echo "Options (for direct execution):"
            echo "  --agent      Install System A (Monitor + Dashboard)"
            echo "  --monitor    Install System B (Agent only)"
            echo "  -h, --help   Show this help"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

main
