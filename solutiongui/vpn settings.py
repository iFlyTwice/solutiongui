import json
import os
import platform
import subprocess
from pathlib import Path


def load_vpn_settings():
    """
    Load VPN settings from a configuration file.
    """
    settings_path = Path.home() / ".vpn_settings.json"
    if not settings_path.exists():
        print("VPN settings file not found.")
        return {}
    try:
        with settings_path.open('r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Error: VPN settings file is corrupt. Please fix the file.")
        return {}


def get_cisco_anyconnect_status():
    """
    Retrieve the VPN connection status from Cisco AnyConnect.
    Works only if Cisco AnyConnect is installed and `vpncli` is available.
    """
    try:
        # Run the Cisco AnyConnect command-line interface (vpncli)
        result = subprocess.run(
            ["vpncli", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "Cisco AnyConnect is installed, but no active VPN connection detected."
    except FileNotFoundError:
        return "Cisco AnyConnect VPN client is not installed or `vpncli` command is unavailable."
    except subprocess.TimeoutExpired:
        return "Cisco AnyConnect command timed out."
    except Exception as e:
        return f"Error retrieving Cisco AnyConnect status: {e}"


def get_connected_vpn():
    """
    Retrieve the current VPN connection details based on the OS.
    """
    current_os = platform.system()

    if current_os == "Linux":
        try:
            result = subprocess.run(["nmcli", "con", "show", "--active"], capture_output=True, text=True)
            active_connections = result.stdout.splitlines()
            vpn_connections = [line for line in active_connections if "vpn" in line.lower()]
            return vpn_connections[0] if vpn_connections else None
        except Exception as e:
            print(f"Error retrieving VPN details on Linux: {e}")
            return None

    elif current_os == "Windows":
        try:
            # First, check if Cisco AnyConnect is active
            cisco_status = get_cisco_anyconnect_status()
            if "Connected" in cisco_status:
                return cisco_status

            # If Cisco AnyConnect is not active, fallback to checking using PowerShell
            result = subprocess.run(["powershell", "-Command", "Get-VpnConnection"], capture_output=True, text=True)
            if "Name" in result.stdout:
                return result.stdout.strip()
            return None
        except Exception as e:
            print(f"Error retrieving VPN details on Windows: {e}")
            return None

    elif current_os == "Darwin":
        try:
            result = subprocess.run(["scutil", "--nc", "list"], capture_output=True, text=True)
            active_connections = result.stdout.splitlines()
            vpn_connections = [line for line in active_connections if "Connected" in line]
            return vpn_connections[0] if vpn_connections else None
        except Exception as e:
            print(f"Error retrieving VPN details on macOS: {e}")
            return None
    else:
        print(f"Unsupported operating system: {current_os}")
        return None


def show_vpn_settings():
    """
    Display VPN settings for the current VPN connection.
    """
    vpn_settings = load_vpn_settings()
    current_vpn = get_connected_vpn()

    print("Your VPN Settings:")
    if vpn_settings:
        for key, value in vpn_settings.items():
            print(f"{key}: {value}")

    if current_vpn:
        print("\nActive VPN Connection Details:")
        print(current_vpn)
    else:
        print("\nNo active VPN connection detected.")


if __name__ == "__main__":
    show_vpn_settings()
