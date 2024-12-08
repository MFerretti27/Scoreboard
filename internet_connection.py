import platform
import subprocess
import sys
import psutil  # pip install psutil
import os 
import time


def get_network_interface() -> str:
    '''Get the current Network interface being used e.g. eth0 or wlan'''
    if platform.system() == 'Windows': return ''
    elif platform.system() == 'Darwin': return "en0"
    else:
        interfaces = psutil.net_if_stats()  # Get interface stats (up/down status)
        io_counters = psutil.net_io_counters(pernic=True)  # Get I/O data per interface
        for interface, stats in interfaces.items():
            if interface == "lo":  # Skip the loopback interface
                continue
            if stats.isup:  # Check if interface is up
                # Check if there has been any data transmitted or received
                data = io_counters.get(interface)
                if data and (data.bytes_sent > 0 or data.bytes_recv > 0):
                    network_interface = interface
        print(f"Current Network Interface {network_interface}")
        return network_interface


##################################
#                                #
#   Check internet connection    #
#                                #
##################################
def is_connected() -> bool:
    """Check if there's an internet connection by pinging a router."""
    try:
        # Ping host with one packet and timeout of 2 seconds
        subprocess.check_call(["ping", "-c", "1", "-W", "2", "8.8.8.8"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def reconnect(network_interface) -> None:
    """Attempt to reconnect by restarting the network interface.
        Mac and Windows should reconnect without restarting network interface
    """
    if platform.system() == 'Windows': return
    elif platform.system() == 'Darwin': return
    print("No internet connection. Attempting to reconnect...")
    os.system(f"sudo ifconfig {network_interface} down")
    time.sleep(1)
    os.system(f"sudo ifconfig {network_interface} up")
    time.sleep(5)  # Wait for the network interface to come back up
    