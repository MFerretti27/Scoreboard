"""Functions to Check Internet Connection and try to Reconnect."""

import platform
import shutil
import subprocess
import time


def is_connected() -> bool:
    """Check if there's an internet connection by pinging 8.8.8.8 (Google DNS)."""
    ping_cmd = shutil.which("ping")
    if not ping_cmd:
        msg = "ping command not found"
        raise RuntimeError(msg)

    system = platform.system()
    if system == "Windows":
        # Windows: -n is count, -w is timeout in milliseconds
        cmd = [ping_cmd, "-n", "1", "-w", "2000", "8.8.8.8"]
    # macOS and Linux: -c is count, -W is timeout (Linux), -t is timeout (macOS)
    elif system == "Darwin":  # macOS
        cmd = [ping_cmd, "-c", "1", "-t", "2", "8.8.8.8"]
    else:  # Assume Linux
        cmd = [ping_cmd, "-c", "1", "-W", "2", "8.8.8.8"]

    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False

    return True


def reconnect() -> None:
    """Attempt to reconnect internet based on OS by turning interface off and on."""
    try:
        if platform.system() == "Windows":
            netsh_path = shutil.which("netsh")
            if not netsh_path:
                msg = "netsh not found in PATH"
                raise RuntimeError(msg)

            subprocess.run([netsh_path, "interface", "set", "interface", "Wi-fi", "disable"], check=True)
            time.sleep(5)
            subprocess.run([netsh_path, "interface", "set", "interface", "Wi-fi", "enable"], check=True)

        elif platform.system() == "Darwin":
            network_setup_path = shutil.which("networksetup")
            if not network_setup_path:
                msg = "networksetup command not found"
                raise RuntimeError(msg)

            subprocess.run([network_setup_path, "-setairportpower", "en0", "off"], check=True)
            time.sleep(5)
            subprocess.run([network_setup_path, "-setairportpower", "en0", "on"], check=True)

        else:
            nmcli_path = shutil.which("nmcli")
            if not nmcli_path:
                msg = "nmcli not found in PATH"
                raise RuntimeError(msg)

            subprocess.run([nmcli_path, "radio", "wifi", "off"], check=True)
            time.sleep(5)
            subprocess.run([nmcli_path, "radio", "wifi", "on"], check=True)

    except subprocess.CalledProcessError as error:
        print(f"Error resetting the network interface : {error}")

    time.sleep(5)  # Wait for the network interface to come back up
