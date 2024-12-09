import platform
import subprocess
import psutil  # pip install psutil
import os 
import time


def get_network_interface() -> str:
    '''Get the current Network interface being used e.g. eth0 or wlan'''

    network_interface = None
    try:
        if platform.system() == 'Windows': 
            result = subprocess.run("netsh interface show interface", capture_output=True, text=True, check=True)
            interfaces = result.stdout.splitlines()

            # Look for the name of the wireless interface
            for line in interfaces:
                if "Connected" in line:
                    if "Wi-Fi" in line:  # Look for the interface containing "Wi-Fi"
                        network_interface = line.split()[-1]  # Last word is the interface name

                    elif "Ethernet" in line:  # Look for the interface containing "Ethernet"
                        network_interface = line.split()[-1]  # Last word is the interface name

        elif platform.system() == 'Darwin':
            result = subprocess.run(["networksetup", "-listallhardwareports"], capture_output=True, text=True, check=True)
            hardware_ports = result.stdout.splitlines()

            #TODO: This does not fully work but luckily mac doesn't need correct network address it will do it on its own when trying to reconnect
            # Loop through the list of hardware ports
            for i, line in enumerate(hardware_ports):
                if "Wi-Fi" in line:
                    wifi_interface = hardware_ports[i + 1].strip()  # The next line gives the interface name (e.g., en0)
                elif "Ethernet Adapter" in line:
                    ethernet_interface = hardware_ports[i + 1].strip()  # The next line gives the interface name (e.g., en1)

            # Check if Wi-Fi or Ethernet is active by trying to ping the network interface
            if wifi_interface:
                wifi_status = subprocess.run(["ifconfig", wifi_interface], capture_output=True, text=True)
                if "status: active" in wifi_status.stdout:
                    network_interface = "en0"

            if ethernet_interface:
                ethernet_status = subprocess.run(["ifconfig", ethernet_interface], capture_output=True, text=True)
                if "status: active" in ethernet_status.stdout:
                    network_interface = "en1"

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
        
        print(f"Network Interface being used is {network_interface}")
        return network_interface
    except subprocess.CalledProcessError as e:
        print(f"Error resetting the network interface {network_interface}: {e}")

def is_connected() -> bool:
    """Check if there's an internet connection by pinging a router"""
    try:
        # Ping host with one packet and timeout of 2 seconds
        subprocess.check_call(["ping", "-c", "1", "-W", "2", "8.8.8.8"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def reconnect(network_interface: str) -> None:
    """Attempt to reconnect by restarting the network interface
       Mac and Windows should reconnect without restarting network interface

       :param network_interface: Interface to shut down and start up, reconnecting internet
    """
    if network_interface == None:
        network_interface = get_network_interface()
        # If it still cant get network interface default wifi network interface
        if network_interface == None:
            if platform.system() == 'Darwin':
                network_interface = 'en0'
            else: # For Raspberry both try resetting both
                os.system(f"sudo ifconfig eth0 down")
                time.sleep(5)
                os.system(f"sudo ifconfig eth0 up")
                os.system(f"sudo ifconfig wlan0 down")
                time.sleep(5)
                os.system(f"sudo ifconfig wlan0 up")
                return

    try:
        if platform.system() == 'Windows':
            subprocess.run(["netsh", "interface", "set", "interface", network_interface, "disable"], check=True)
            time.sleep(5)
            subprocess.run(["netsh", "interface", "set", "interface", network_interface, "enable"], check=True)

        elif platform.system() == 'Darwin':
            subprocess.run(["networksetup", "-setairportpower", network_interface, "off"], check=True)
            time.sleep(5)
            subprocess.run(["networksetup", "-setairportpower", network_interface, "on"], check=True)

        else:
            os.system(f"sudo ifconfig {network_interface} down")
            time.sleep(5)
            os.system(f"sudo ifconfig {network_interface} up")

    except subprocess.CalledProcessError as e:
        print(f"Error resetting the network interface {network_interface}: {e}")

    time.sleep(5)  # Wait for the network interface to come back up
    