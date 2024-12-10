'''Functions to Check Internet Connection and try to Reconnect'''

import platform
import subprocess
import os 
import time

def is_connected() -> bool:
    """Check if there's an internet connection by pinging 8.8.8.8"""
    try:
        # Ping host with one packet and timeout of 2 seconds
        subprocess.check_call(["ping", "-c", "1", "-W", "2", "8.8.8.8"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def reconnect() -> None:
    """Attempt to reconnect internet"""
    try:
        if platform.system() == 'Windows':
            subprocess.run(["netsh", "interface", "set", "interface", "Wi-fi", "disable"], check=True)
            time.sleep(5)
            subprocess.run(["netsh", "interface", "set", "interface", "Wi-fi", "enable"], check=True)

        elif platform.system() == 'Darwin':
            subprocess.run(["networksetup", "-setairportpower", "en0", "off"], check=True)
            time.sleep(5)
            subprocess.run(["networksetup", "-setairportpower", "en0", "on"], check=True)

        else:
            os.system(f"sudo nmcli radio wifi off")
            time.sleep(5)
            os.system(f"sudo nmcli radio wifi on")

    except subprocess.CalledProcessError as e:
        print(f"Error resetting the network interface : {e}")

    time.sleep(5)  # Wait for the network interface to come back up
    