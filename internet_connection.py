import platform
import subprocess
import re
import psutil  # pip install psutil
import os 
import time


def get_router_ip():
    '''Get your Routers IP'''
    if platform.system() == 'Windows':
        output = subprocess.check_output("ipconfig", encoding="utf-8")
        match = re.search(r"Default Gateway[ .:]*([\d.]+)", output)
        router_ip = match.group(1)
    # else:
    #     output = subprocess.check_output("ip route", shell=True, encoding="utf-8")
    #     match = re.search(r"default via ([\d.]+)", output)
    #     router_ip = match.group(1)
    
    # print(f"Routers IP address {router_ip}")
    # return router_ip


def get_network_interface():
    '''Get the current Network interface being used e.g. eth0 or wlan'''
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
def is_connected(router_ip) -> bool:
    """Check if there's an internet connection by pinging a router."""
    try:
        # Ping host with one packet and timeout of 2 seconds
        subprocess.check_call(["ping", "-c", "1", "-W", "2", router_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def reconnect(network_interface):
    """Attempt to reconnect by restarting the network interface."""
    print("No internet connection. Attempting to reconnect...")
    os.system(f"sudo ifconfig {network_interface} down")
    time.sleep(1)
    os.system(f"sudo ifconfig {network_interface} up")
    time.sleep(5)  # Wait for the network interface to come back up
    