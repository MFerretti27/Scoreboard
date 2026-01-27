# Root Application Installation Guide

This guide explains how to install and automatically run your application (either a compiled binary `.elf` or Python script `.py`) as **root** on a Linux system (Raspberry Pi, Ubuntu, etc.).

---

## Quick Start

### Prerequisites
- Root/sudo access on the target machine
- The `install.sh` script from `.github/scripts/`
- Your application file (either `app.elf` or `main.py`)

### Installation (One Command)

```bash
sudo ./.github/scripts/install.sh <your_app.elf or your_app.py>
```

**Examples:**
```bash
# For compiled binary
sudo ./.github/scripts/install.sh myapp.elf

# For Python script
sudo ./.github/scripts/install.sh main.py
```

---

## How It Works

### Installation Steps

When you run `install.sh`, it automatically:

1. **Updates System** – Ensures all packages are current
2. **Installs Dependencies** – Installs Python 3, venv, pip, and system utilities
3. **Prepares Executable**
   - For `.elf` files: Sets execute permissions
   - For `.py` files: Creates virtual environment and installs packages from `requirements.txt`
4. **Creates systemd Service** – Registers your app as a system service that:
   - Runs as **root** (User=root, Group=root)
   - Auto-restarts on crashes
   - Auto-starts on system boot
5. **Enables & Starts Service** – Service is now running
6. **Verification** – Confirms service is active and shows status

### Root Execution

The systemd service is configured to run as root via:

```ini
[Service]
User=root
Group=root
```

This ensures your application has full system permissions.

---

## Detailed Setup Instructions

### Step 1: Prepare Your Application

#### Option A: Python Application (.py)

Ensure you have:
- `main.py` (or your entry point script)
- `requirements.txt` (in the same directory)

Example directory structure:
```
/home/pi/app/
├── main.py
├── requirements.txt
└── .github/
    └── scripts/
        └── install.sh
```

#### Option B: Compiled Binary (.elf)

Ensure your compiled binary:
- Has execute permissions locally (not required, script will set it)
- Is in the same directory as `install.sh`

```
/home/pi/app/
├── myapp.elf
└── .github/
    └── scripts/
        └── install.sh
```

### Step 2: Run the Installer

Navigate to your app directory and run:

```bash
cd /path/to/your/app
sudo ./.github/scripts/install.sh main.py
```

Or for a binary:
```bash
sudo ./.github/scripts/install.sh myapp.elf
```

### Step 3: Monitor Installation

The script will show progress:
```
============= Installing Root Application =============
Application: main.py
Type: py
Location: .
Service Name: main
Run As: root

[1/5] Updating system packages...
[2/5] Installing dependencies...
[3/5] Preparing executable (type: py)...
[4/5] Creating systemd service (runs as root)...
[5/5] Enabling and starting service...

✓ Installation Successful!

Service Status:
● main.service - main (Root Service)
   Loaded: loaded (/etc/systemd/system/main.service; enabled; preset: enabled)
   Active: active (running)
   ...
```

### Step 4: Reboot (Optional)

When prompted, choose to reboot now or later:
```
Reboot now? (y/n)
```

The application will auto-start on next boot.

---

## Managing Your Service

Once installed, use these commands to manage your application:

### View Live Logs
```bash
sudo journalctl -u main -f
```

### Check Service Status
```bash
sudo systemctl status main
```

### Stop the Application
```bash
sudo systemctl stop main
```

### Start the Application
```bash
sudo systemctl start main
```

### Restart the Application
```bash
sudo systemctl restart main
```

### View Recent Log Entries (Last 20 lines)
```bash
sudo journalctl -u main -n 20
```

### View Full Journal Output
```bash
sudo journalctl -u main --no-pager
```

### Disable Auto-Start (but keep installed)
```bash
sudo systemctl disable main
```

### Re-Enable Auto-Start
```bash
sudo systemctl enable main
```

---

## Troubleshooting

### Service Failed to Start

Check the logs for errors:
```bash
sudo journalctl -u main -n 50
```

Common issues:
- **Missing dependencies** – Ensure `requirements.txt` exists for Python apps
- **Permission issues** – Try running the installer again with `sudo`
- **Path issues** – Make sure the application file path is correct

### Application Crashes on Startup

View extended logs:
```bash
sudo journalctl -u main --no-pager | tail -100
```

Check if the app works manually:
```bash
# For Python
cd /home/pi/app
./venv/bin/python main.py

# For binary
/home/pi/app/myapp.elf
```

### Application Keeps Restarting

This is intentional (systemd is set to `Restart=always`). Logs show why:
```bash
sudo journalctl -u main -f  # Follow logs to see the issue
```

### Port Already in Use

If your app uses a port that's already in use:
```bash
# Find what's using the port
sudo lsof -i :8000  # Replace 8000 with your port

# Kill the process
sudo kill -9 <PID>
```

---

## Advanced Options

### Reinstall/Update Application

To reinstall with a new version of your app:

1. Stop the service:
   ```bash
   sudo systemctl stop main
   ```

2. Replace your application file (`.py` or `.elf`)

3. Restart:
   ```bash
   sudo systemctl restart main
   ```

Or run the installer again to rebuild everything:
```bash
sudo ./.github/scripts/install.sh main.py
```

### Change Application Location

If you need to move your app, reinstall from the new location:
```bash
cd /new/location
sudo /path/to/original/install.sh main.py
```

### Customize Service Behavior

Edit the service file directly:
```bash
sudo nano /etc/systemd/system/main.service
```

After editing, reload systemd:
```bash
sudo systemctl daemon-reload
sudo systemctl restart main
```

---

## Service File Reference

Your service is created at `/etc/systemd/system/<app_name>.service`:

```ini
[Unit]
Description=<app_name> (Root Service)
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/home/pi/app
ExecStart=/home/pi/app/venv/bin/python /home/pi/app/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Key settings:
- `User=root` – Runs with root privileges
- `Restart=always` – Auto-restarts on failure
- `RestartSec=5` – Waits 5 seconds between restarts
- `After=network.target` – Waits for network before starting

---

## Security Notes

⚠️ **Running as root is powerful but risky:**

- The application has full system access
- Be careful with what code runs in this context
- Regularly update system and dependencies
- Monitor logs for suspicious activity
- Use strong file permissions on config files

---

## For Raspberry Pi Specific

On Raspberry Pi OS, you may also want to:

1. **Disable auto-login to console** (already handled by installer)
2. **Disable VNC/SSH if not needed** – Reduces attack surface
3. **Use read-only filesystem** – Advanced setup for embedded systems
4. **Enable automatic backups** – Protect your application data

---

## Examples

### Example 1: Install Scoreboard App (Python)

```bash
cd ~/scoreboard
sudo ./.github/scripts/install.sh main.py
# Watch for the success message
sudo journalctl -u main -f  # Monitor logs
```

### Example 2: Install Compiled Game (Binary)

```bash
cd ~/game-app
sudo ./.github/scripts/install.sh game.elf
# Monitor service
sudo systemctl status game
```

### Example 3: Update Installed App

```bash
# Replace main.py with new version
cp ~/new-main.py ~/app/main.py

# Restart to run new version
sudo systemctl restart main

# Check it's running
sudo systemctl status main
```

---

## Support

For issues:
1. Check logs: `sudo journalctl -u <service_name> -n 50`
2. Verify file exists: `ls -la /path/to/app/file.py`
3. Test manually: Run app directly to see errors
4. Review systemd service: `cat /etc/systemd/system/<service_name>.service`

---

**Last Updated:** January 2026
