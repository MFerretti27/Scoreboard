#!/usr/bin/env bash
set -e

# ============================================================================
# ROOT APPLICATION INSTALLER
# ============================================================================
# Installs and runs .elf (compiled binary) or .py (Python) applications as
# root via systemd service. Handles all dependencies and auto-restart.
#
# Usage:
#   sudo ./install.sh <app.elf | app.py>
#
# Examples:
#   sudo ./install.sh myapp.elf
#   sudo ./install.sh main.py
# ============================================================================

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# VALIDATION
# ============================================================================

# Check root privilege
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
  echo "Example: sudo ./install.sh main.py"
  exit 1
fi

# Parse arguments
APP_FILE="$1"

if [ -z "$APP_FILE" ]; then
  echo -e "${RED}ERROR: No application file specified${NC}"
  echo ""
  echo "Usage: sudo ./install.sh <app.elf | app.py>"
  echo ""
  echo "Examples:"
  echo "  sudo ./install.sh myapp.elf"
  echo "  sudo ./install.sh main.py"
  exit 1
fi

# Configuration
APP_DIR="${2:-.}"  # Optional second argument for app directory (default: current)
APP_NAME="${APP_FILE%.*}"  # Remove extension for service name
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

# Validate file exists
if [ ! -f "$APP_DIR/$APP_FILE" ]; then
  echo -e "${RED}ERROR: File not found: $APP_DIR/$APP_FILE${NC}"
  exit 1
fi

# Get file extension
EXT="${APP_FILE##*.}"

echo -e "${GREEN}============= Installing Root Application =============${NC}"
echo "Application: $APP_FILE"
echo "Type: $EXT"
echo "Location: $APP_DIR"
echo "Service Name: $APP_NAME"
echo "Run As: root"
echo ""

# ============================================================================
# SYSTEM SETUP
# ============================================================================

echo -e "${YELLOW}[1/5] Updating system packages...${NC}"
apt-get update > /dev/null 2>&1
apt-get full-upgrade -y > /dev/null 2>&1

echo -e "${YELLOW}[2/5] Installing dependencies...${NC}"
apt-get install -y python3 python3-venv python3-pip curl watchdog > /dev/null 2>&1

# ============================================================================
# PREPARE EXECUTABLE
# ============================================================================

echo -e "${YELLOW}[3/5] Preparing executable (type: $EXT)...${NC}"

if [ "$EXT" = "elf" ]; then
  # Binary executable
  chmod +x "$APP_DIR/$APP_FILE"
  EXEC_CMD="$APP_DIR/$APP_FILE"
  echo "  → Set executable permission on binary"
  
elif [ "$EXT" = "py" ]; then
  # Python application
  cd "$APP_DIR"
  
  echo "  → Creating Python virtual environment..."
  python3 -m venv venv > /dev/null 2>&1
  
  echo "  → Installing Python dependencies..."
  source venv/bin/activate
  pip install --upgrade pip > /dev/null 2>&1
  
  if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
    echo "  → Installed packages from requirements.txt"
  else
    echo "  → Warning: requirements.txt not found (skipping package install)"
  fi
  
  deactivate
  EXEC_CMD="$APP_DIR/venv/bin/python $APP_DIR/$APP_FILE"
  
else
  echo -e "${RED}ERROR: Unsupported file type: .$EXT${NC}"
  echo "Supported types: .elf (binary), .py (Python script)"
  exit 1
fi

# ============================================================================
# CREATE SYSTEMD SERVICE (RUNS AS ROOT)
# ============================================================================

echo -e "${YELLOW}[4/5] Creating systemd service (runs as root)...${NC}"

tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=$APP_NAME (Root Service)
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$APP_DIR
ExecStart=$EXEC_CMD
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "  → Service file created: $SERVICE_FILE"
echo "  → Running as: root (UID 0)"

# ============================================================================
# ENABLE & START SERVICE
# ============================================================================

echo -e "${YELLOW}[5/5] Enabling and starting service...${NC}"

systemctl daemon-reload
systemctl enable ${APP_NAME}.service
systemctl restart ${APP_NAME}.service

echo "  → Service enabled and started"

# ============================================================================
# VERIFICATION
# ============================================================================

sleep 2

if systemctl is-active --quiet ${APP_NAME}.service; then
  echo ""
  echo -e "${GREEN}✓ Installation Successful!${NC}"
  echo ""
  echo "Service Status:"
  systemctl status ${APP_NAME}.service --no-pager
  echo ""
  echo "Useful Commands:"
  echo "  View logs:    journalctl -u ${APP_NAME} -f"
  echo "  Stop app:     sudo systemctl stop ${APP_NAME}"
  echo "  Start app:    sudo systemctl start ${APP_NAME}"
  echo "  Restart app:  sudo systemctl restart ${APP_NAME}"
  echo "  Status:       sudo systemctl status ${APP_NAME}"
else
  echo ""
  echo -e "${RED}✗ Service failed to start${NC}"
  echo "Check logs: sudo journalctl -u ${APP_NAME} -n 20"
  exit 1
fi

echo ""
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "Rebooting in 5 seconds..."
  sleep 5
  reboot
else
  echo "Skipped reboot. Run 'sudo reboot' when ready."
fi
