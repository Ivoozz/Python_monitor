#
# One-line cross-platform installer for Python Monitoring System
# Usage: Invoke-Expression (Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/Ivoozz/Python_monitor/main/install.ps1').Content
#
#Requires -Version 5.1

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet("Agent", "Monitor", "")]
    [string]$InstallType = ""
)

# Configuration
$RepoUrl = "https://github.com/Ivoozz/Python_monitor.git"
$InstallDir = "$env:LOCALAPPDATA\PythonMonitor"
$VenvDir = "$InstallDir\venv"
$ConfigDir = "$env:LOCALAPPDATA\PythonMonitor\Config"

# Colors for output
function Write-Success($message) {
    Write-Host "[✓] $message" -ForegroundColor Green
}

function Write-ErrorMsg($message) {
    Write-Host "[✗] $message" -ForegroundColor Red
}

function Write-Info($message) {
    Write-Host "[ℹ] $message" -ForegroundColor Cyan
}

function Write-WarningMsg($message) {
    Write-Host "[!] $message" -ForegroundColor Yellow
}

function Show-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║         Python Monitoring System Installer                   ║" -ForegroundColor Blue
    Write-Host "║         Cross-Platform: Windows (PowerShell)                 ║" -ForegroundColor Blue
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""
}

function Test-Python {
    Write-Info "Checking Python 3 installation..."
    
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    
    if ($pythonCmd) {
        $pythonVersion = & $pythonCmd.Source --version 2>&1
        Write-Success "Python found: $pythonVersion"
        
        # Check version (need 3.7+)
        $versionString = $pythonVersion -replace "Python "
        $version = [System.Version]$versionString
        
        if ($version.Major -lt 3 -or ($version.Major -eq 3 -and $version.Minor -lt 7)) {
            Write-ErrorMsg "Python 3.7+ is required"
            exit 1
        }
        
        return $pythonCmd.Source
    } else {
        Write-ErrorMsg "Python 3 is not installed"
        Write-Host ""
        Write-Host "Please install Python 3.7 or higher:"
        Write-Host "  1. Download from: https://www.python.org/downloads/"
        Write-Host "  2. Run the installer and check 'Add Python to PATH'"
        Write-Host "  3. Reopen PowerShell and run this script again"
        Write-Host ""
        exit 1
    }
}

function Install-Git {
    Write-Info "Checking Git installation..."
    
    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitCmd) {
        Write-WarningMsg "Git not found. Installing via winget..."
        
        # Check if winget is available
        $wingetCmd = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetCmd) {
            try {
                & winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
                # Refresh environment
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                Write-Success "Git installed successfully"
            } catch {
                Write-ErrorMsg "Failed to install Git via winget"
                Write-Host "Please install Git manually from: https://git-scm.com/download/win"
                exit 1
            }
        } else {
            Write-ErrorMsg "winget not available. Please install Git manually:"
            Write-Host "  https://git-scm.com/download/win"
            exit 1
        }
    } else {
        Write-Success "Git is already installed"
    }
}

function Clone-Or-UpdateRepo {
    Write-Info "Setting up installation directory..."
    
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }
    
    if (Test-Path "$InstallDir\.git") {
        Write-Info "Existing installation found. Updating..."
        Push-Location $InstallDir
        & git pull --quiet
        Pop-Location
    } else {
        Write-Info "Cloning repository..."
        if (Test-Path $InstallDir) {
            Remove-Item -Recurse -Force $InstallDir
        }
        & git clone --depth 1 --quiet $RepoUrl $InstallDir
    }
    
    Write-Success "Repository ready at $InstallDir"
}

function New-VirtualEnvironment {
    param([string]$PythonPath)
    
    Write-Info "Creating Python virtual environment..."
    
    if (Test-Path $VenvDir) {
        Write-Info "Removing existing virtual environment..."
        Remove-Item -Recurse -Force $VenvDir
    }
    
    & $PythonPath -m venv $VenvDir
    Write-Success "Virtual environment created"
    
    Write-Info "Installing Python packages..."
    & "$VenvDir\Scripts\pip.exe" install --upgrade pip --quiet
    & "$VenvDir\Scripts\pip.exe" install -r "$InstallDir\requirements.txt" --quiet
    Write-Success "Python packages installed"
}

function Read-InstallationType {
    if ($InstallType) {
        Write-Info "Installation type specified via parameter: $InstallType"
        return $InstallType.ToLower()
    }
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Select installation type:"
    Write-Host ""
    Write-Host "  [A] System A - Monitor + Dashboard (Central monitoring server)" -ForegroundColor Green
    Write-Host "      Includes: Flask dashboard, metrics collector, web UI"
    Write-Host "      Use this for the main monitoring machine"
    Write-Host ""
    Write-Host "  [B] System B - Agent only (System to be monitored)" -ForegroundColor Yellow
    Write-Host "      Includes: XML-RPC agent that reports metrics"
    Write-Host "      Install this on each machine you want to monitor"
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host ""
    
    do {
        $choice = Read-Host "Enter your choice (A/B)"
        switch ($choice.ToUpper()) {
            "A" { 
                Write-Info "Selected: System A (Monitor + Dashboard)"
                return "agent"
            }
            "B" { 
                Write-Info "Selected: System B (Agent only)"
                return "monitor"
            }
            default { Write-WarningMsg "Please enter A or B" }
        }
    } while ($true)
}

function Write-Configuration {
    param([string]$Type)
    
    Write-Info "Writing configuration..."
    
    if (-not (Test-Path $ConfigDir)) {
        New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    }
    
    # Create installation config
    $installConfig = @{
        install_type = $Type
        install_dir = $InstallDir
        venv_dir = $VenvDir
        installed_at = (Get-Date -Format "o")
        version = "1.0.0"
    } | ConvertTo-Json -Depth 2
    
    $installConfig | Out-File "$ConfigDir\install.json" -Encoding utf8
    
    if ($Type -eq "agent") {
        # Dashboard + Monitor config
        @"
# Python Monitor Dashboard Environment
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
FLASK_DEBUG=false
DEVICES_FILE=$ConfigDir\devices.json
METRICS_FILE=$ConfigDir\metrics.json
"@ | Out-File "$ConfigDir\dashboard.env" -Encoding utf8
        
        # Create empty devices file
        "[]" | Out-File "$ConfigDir\devices.json" -Encoding utf8
        
        Write-Success "Dashboard configuration created"
    } else {
        # Agent config
        @"
# Python Monitor Agent Environment
AGENT_HOST=0.0.0.0
AGENT_PORT=8000
AGENT_LOG_LEVEL=INFO
AGENT_CONFIG=$ConfigDir\agent.json
"@ | Out-File "$ConfigDir\agent.env" -Encoding utf8
        
        # Create agent config
        $agentConfig = @{
            host = "0.0.0.0"
            port = 8000
            check_interval = 30
            log_file = "$ConfigDir\agent.log"
        } | ConvertTo-Json -Depth 2
        
        $agentConfig | Out-File "$ConfigDir\agent.json" -Encoding utf8
        
        Write-Success "Agent configuration created"
    }
}

function New-LauncherScripts {
    param([string]$Type)
    
    Write-Info "Creating launcher scripts..."
    
    # Ensure Scripts directory exists
    $scriptsDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
    if (-not (Test-Path $scriptsDir)) {
        $scriptsDir = "$env:USERPROFILE\Scripts"
        New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    }
    
    if ($Type -eq "agent") {
        # Dashboard launcher
        @"
@echo off
:: Python Monitor Dashboard Launcher
call "$VenvDir\Scripts\activate.bat"
set "DEVICES_FILE=$ConfigDir\devices.json"
set "METRICS_FILE=$ConfigDir\metrics.json"
cd /d "$InstallDir"
python dashboard.py %*
"@ | Out-File "$scriptsDir\monitor-dashboard.bat" -Encoding ascii
        
        # PowerShell launcher
        @"
# Python Monitor Dashboard Launcher
& "$VenvDir\Scripts\Activate.ps1"
`$env:DEVICES_FILE = "$ConfigDir\devices.json"
`$env:METRICS_FILE = "$ConfigDir\metrics.json"
Set-Location "$InstallDir"
python dashboard.py `@args
"@ | Out-File "$scriptsDir\monitor-dashboard.ps1" -Encoding utf8
        
        # Create Windows service registration script
        @"
#Requires -RunAsAdministrator
# Register Python Monitor Dashboard as Windows Service

`$serviceName = "PythonMonitorDashboard"
`$displayName = "Python Monitor Dashboard"
`$description = "Flask-based monitoring dashboard with auto-refresh"

# Create service using nssm (Non-Sucking Service Manager)
if (Get-Command nssm -ErrorAction SilentlyContinue) {
    nssm install `$serviceName `"$VenvDir\Scripts\python.exe`" `"$InstallDir\dashboard.py`"
    nssm set `$serviceName DisplayName `$displayName
    nssm set `$serviceName Description `$description
    nssm set `$serviceName AppEnvironmentExtra DEVICES_FILE=$ConfigDir\devices.json
    nssm set `$serviceName AppEnvironmentExtra METRICS_FILE=$ConfigDir\metrics.json
    nssm start `$serviceName
    Write-Host "Service installed and started"
} else {
    Write-Host "nssm not found. To install as service:"
    Write-Host "1. Download nssm from https://nssm.cc/"
    Write-Host "2. Run: nssm install $serviceName"
    Write-Host "3. Set Path: $VenvDir\Scripts\python.exe"
    Write-Host "4. Set Arguments: $InstallDir\dashboard.py"
}
"@ | Out-File "$ConfigDir\install-service.ps1" -Encoding utf8
        
        Write-Success "Dashboard launcher created: monitor-dashboard.bat"
    } else {
        # Agent launcher
        @"
@echo off
:: Python Monitor Agent Launcher
call "$VenvDir\Scripts\activate.bat"
set "AGENT_CONFIG=$ConfigDir\agent.json"
cd /d "$InstallDir"
python agent\agent_server.py %*
"@ | Out-File "$scriptsDir\monitor-agent.bat" -Encoding ascii
        
        # PowerShell launcher
        @"
# Python Monitor Agent Launcher
& "$VenvDir\Scripts\Activate.ps1"
`$env:AGENT_CONFIG = "$ConfigDir\agent.json"
Set-Location "$InstallDir"
python agent\agent_server.py `@args
"@ | Out-File "$scriptsDir\monitor-agent.ps1" -Encoding utf8
        
        # Create Windows service registration script
        @"
#Requires -RunAsAdministrator
# Register Python Monitor Agent as Windows Service

`$serviceName = "PythonMonitorAgent"
`$displayName = "Python Monitor Agent"
`$description = "System monitoring agent that reports metrics to dashboard"

# Create service using nssm (Non-Sucking Service Manager)
if (Get-Command nssm -ErrorAction SilentlyContinue) {
    nssm install `$serviceName `"$VenvDir\Scripts\python.exe`" `"$InstallDir\agent\agent_server.py`"
    nssm set `$serviceName DisplayName `$displayName
    nssm set `$serviceName Description `$description
    nssm set `$serviceName AppEnvironmentExtra AGENT_CONFIG=$ConfigDir\agent.json
    nssm start `$serviceName
    Write-Host "Service installed and started"
} else {
    Write-Host "nssm not found. To install as service:"
    Write-Host "1. Download nssm from https://nssm.cc/"
    Write-Host "2. Run: nssm install $serviceName"
    Write-Host "3. Set Path: $VenvDir\Scripts\python.exe"
    Write-Host "4. Set Arguments: $InstallDir\agent\agent_server.py"
}
"@ | Out-File "$ConfigDir\install-service.ps1" -Encoding utf8
        
        Write-Success "Agent launcher created: monitor-agent.bat"
    }
}

function Show-NextSteps {
    param([string]$Type)
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "               Installation Complete!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    
    if ($Type -eq "agent") {
        Write-Host "System A (Monitor + Dashboard) installed" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Quick Start:"
        Write-Host "  1. Start the dashboard:"
        Write-Host "     monitor-dashboard" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  2. Open your browser to:"
        Write-Host "     http://localhost:5000" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  3. Add agents using the web UI or API"
        Write-Host ""
        Write-Host "Windows Service (optional):"
        Write-Host "  1. Download nssm from https://nssm.cc/"
        Write-Host "  2. Run the service install script:"
        Write-Host "     $ConfigDir\install-service.ps1" -ForegroundColor Yellow
    } else {
        Write-Host "System B (Agent) installed" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Quick Start:"
        Write-Host "  1. Start the agent:"
        Write-Host "     monitor-agent" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  2. The agent will listen on port 8000"
        Write-Host ""
        Write-Host "  3. Add this machine to your dashboard:"
        
        # Get IP addresses
        $ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | 
            Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
            Select-Object -ExpandProperty IPAddress -First 1
        
        if ($ipAddresses) {
            Write-Host "     IP: $ipAddresses, Port: 8000" -ForegroundColor Yellow
        } else {
            Write-Host "     Use 'ipconfig' to find your IP address"
        }
        Write-Host ""
        Write-Host "Windows Service (optional):"
        Write-Host "  1. Download nssm from https://nssm.cc/"
        Write-Host "  2. Run the service install script:"
        Write-Host "     $ConfigDir\install-service.ps1" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Configuration files:"
    Write-Host "  Install config: $ConfigDir\install.json"
    if ($Type -eq "agent") {
        Write-Host "  Dashboard env:  $ConfigDir\dashboard.env"
        Write-Host "  Devices:        $ConfigDir\devices.json"
    } else {
        Write-Host "  Agent env:      $ConfigDir\agent.env"
        Write-Host "  Agent config:   $ConfigDir\agent.json"
    }
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
}

function Main {
    Show-Banner
    
    $pythonPath = Test-Python
    Install-Git
    Clone-Or-UpdateRepo
    New-VirtualEnvironment -PythonPath $pythonPath
    
    $type = Read-InstallationType
    Write-Configuration -Type $type
    New-LauncherScripts -Type $type
    Show-NextSteps -Type $type
}

# Handle execution policy notice
$executionPolicy = Get-ExecutionPolicy
if ($executionPolicy -eq "Restricted") {
    Write-WarningMsg "PowerShell execution policy is Restricted"
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
    Write-Host ""
}

# Run main
Main
