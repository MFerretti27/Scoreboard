"""Functions to Check Internet Connection and try to Reconnect."""
from __future__ import annotations

import platform
import shutil
import subprocess
import time

from helper_functions.logging.logger_config import logger


def is_connected() -> bool:
    """Check if there's an internet connection by pinging 8.8.8.8 (Google DNS)."""
    try:
        ping_cmd = shutil.which("ping")
        if not ping_cmd:
            logger.warning("ping command not found in PATH")
            return False

        system = platform.system()
        if system == "Windows":
            # Windows: -n is count, -w is timeout in milliseconds
            cmd = [ping_cmd, "-n", "1", "-w", "2000", "8.8.8.8"]
        # macOS and Linux: -c is count, -W is timeout (Linux), -t is timeout (macOS)
        elif system == "Darwin":  # macOS
            cmd = [ping_cmd, "-c", "1", "-t", "2", "8.8.8.8"]
        else:  # Assume Linux
            cmd = [ping_cmd, "-c", "1", "-W", "2", "8.8.8.8"]

        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False
    except Exception:
        logger.exception("Error checking internet connection", exc_info=True)
        return False

    return True


def reconnect() -> None:
    """Attempt to reconnect internet based on OS by turning interface off and on."""
    try:
        if platform.system() == "Windows":
            netsh_path = shutil.which("netsh")
            if not netsh_path:
                logger.warning("netsh command not found, cannot reconnect on Windows")
                return

            try:
                subprocess.run(
                    [netsh_path, "interface", "set", "interface", "Wi-fi", "disable"],
                    check=True,
                    timeout=10,
                )
                time.sleep(5)
                subprocess.run(
                    [netsh_path, "interface", "set", "interface", "Wi-fi", "enable"],
                    check=True,
                    timeout=10,
                )
            except subprocess.TimeoutExpired:
                logger.warning("Network command timed out on Windows")

        elif platform.system() == "Darwin":
            network_setup_path = shutil.which("networksetup")
            if not network_setup_path:
                logger.warning("networksetup command not found, cannot reconnect on macOS")
                return

            try:
                subprocess.run([network_setup_path, "-setairportpower", "en0", "off"], check=True, timeout=10)
                time.sleep(5)
                subprocess.run([network_setup_path, "-setairportpower", "en0", "on"], check=True, timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Network command timed out on macOS")

        else:
            nmcli_path = shutil.which("nmcli")
            if not nmcli_path:
                logger.warning("nmcli command not found, cannot reconnect on Linux")
                return

            try:
                subprocess.run([nmcli_path, "radio", "wifi", "off"], check=True, timeout=10)
                time.sleep(5)
                subprocess.run([nmcli_path, "radio", "wifi", "on"], check=True, timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Network command timed out on Linux")

    except subprocess.CalledProcessError:
        logger.exception("Error resetting the network interface", exc_info=True)
    except Exception:
        logger.exception("Unexpected error during network reconnection", exc_info=True)

    time.sleep(5)  # Wait for the network interface to come back up


def connect_to_wifi(network_name: str, password: str) -> str:
    """Create connection to wifi.

    :param network_name: network SSID to connect to
    :param password: password of network

    :return: Success or error message
    """
    try:
        if platform.system() == "Windows":
            return "For Windows OS Please connect through OS settings"

        if platform.system() == "Darwin":
            # Use networksetup on macOS
            network_setup_path = shutil.which("networksetup")
            if not network_setup_path:
                return "networksetup command not found"

            subprocess.run([network_setup_path, "-setairportpower", "en0", "on"], check=True)
            service = "en0"
            cmd = [
                "networksetup",
                "-setairportnetwork",
                service,
                network_name,
                password,
            ]
            subprocess.run(cmd, check=True)
            return f"Successfully connected to {network_name}"

        # Create the Wi-Fi connection using nmcli
        nmcli_path = shutil.which("nmcli")
        if not nmcli_path:
            return "nmcli not found in PATH"
        subprocess.run([nmcli_path, "radio", "wifi", "on"], check=True)
        command = f"nmcli dev wifi connect '{network_name}' password '{password}'"
        subprocess.run(command, shell=True, check=True)

    except subprocess.CalledProcessError as e:
        return f"Failed to connect: {e}"

    return f"Successfully connected to {network_name}"
