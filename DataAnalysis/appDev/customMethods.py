import subprocess
import socket


# def get_wifi_name():
#     try:
#         # Run the system command to get the Wi-Fi name (SSID)
#         result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, check=True)
#         # Parse the output to find the SSID
#         for line in result.stdout.split('\n'):
#             if "SSID" in line and "BSSID" not in line:
#                 return line.split(":")[1].strip()
#     except subprocess.CalledProcessError as e:
#         return f"Error: {e}"

def get_wifi_name():
    system = platform.system()  # Get the OS name (e.g., "Windows", "Linux")
    try:
        if system == "Windows":
            # Windows: Use netsh command to get Wi-Fi name
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if "SSID" in line and "BSSID" not in line:
                    return line.split(":")[1].strip()
        elif system == "Linux":
            # Linux: Use nmcli command to get Wi-Fi name
            result = subprocess.run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"], capture_output=True, text=True, check=True)
            for line in result.stdout.split('\n'):
                if "yes" in line:
                    return line.split(":")[1].strip()
        else:
            return f"Unsupported OS: {system}"
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {e}"


def get_local_ip():
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to an external server (doesn't actually send data)
        s.connect(("8.8.8.8", 80))
        # Get the local IP address
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return f"Error: {e}"