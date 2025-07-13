"""
Network interface utilities for Signal Booster.
This module provides functions for working with network interfaces.
"""

from signal_booster.network.common import *

def _is_wireless_interface(interface: str) -> bool:
    """Check if the interface is wireless."""
    # This is a simplified check - actual implementation would be more complex
    # and OS-specific
    if platform.system() == "Windows":
        return "wi-fi" in interface.lower() or "wireless" in interface.lower()
    elif platform.system() == "Linux":
        return interface.startswith("wl")
    elif platform.system() == "Darwin":  # macOS
        return interface.startswith("en") and not interface.startswith("eth")
    return False


def _get_interface_speed(interface_name: str) -> float:
    """
    Get the speed of a network interface in Mbps.
    
    Args:
        interface_name: Name of the interface
        
    Returns:
        Speed in Mbps
    """
    speed = 0
    
    try:
        if platform.system() == "Windows":
            # Use PowerShell to get interface speed
            stdout, _, _ = run_command([
                "powershell", 
                "-Command", 
                f"(Get-NetAdapter -Name '*{interface_name}*' | Select-Object -First 1).LinkSpeed"
            ])
            
            # Parse the output (format is typically "1 Gbps" or "100 Mbps")
            if stdout:
                if "Gbps" in stdout:
                    speed_value = float(stdout.split()[0])
                    speed = speed_value * 1000  # Convert Gbps to Mbps
                elif "Mbps" in stdout:
                    speed = float(stdout.split()[0])
                    
        elif platform.system() == "Linux":
            # Check /sys/class/net/interface/speed
            speed_file = f"/sys/class/net/{interface_name}/speed"
            if os.path.exists(speed_file):
                with open(speed_file, "r") as f:
                    speed = float(f.read().strip())
                    
        elif platform.system() == "Darwin":  # macOS
            # Use networksetup to get interface speed
            # First need to map interface name to service name
            stdout, _, _ = run_command(["networksetup", "-listallhardwareports"])
            
            # Parse output to find the service name
            service_name = None
            if stdout:
                lines = stdout.split('\n')
                for i, line in enumerate(lines):
                    if f"Device: {interface_name}" in line and i > 0:
                        # Service name is typically on the line after "Hardware Port:"
                        for j in range(i-1, -1, -1):
                            if "Hardware Port:" in lines[j]:
                                service_name = lines[j].split(":", 1)[1].strip()
                                break
                        break
                
                if service_name:
                    # Get the interface details
                    stdout, _, _ = run_command(["networksetup", "-getinfo", service_name])
                    
                    # Look for speed information
                    if stdout:
                        for line in stdout.split('\n'):
                            if "Link Speed" in line and ":" in line:
                                speed_text = line.split(":", 1)[1].strip().lower()
                                if "gbps" in speed_text:
                                    speed = float(speed_text.split()[0]) * 1000  # Convert Gbps to Mbps
                                elif "mbps" in speed_text:
                                    speed = float(speed_text.split()[0])
                                break
    except Exception as e:
        logger.error(f"Error getting interface speed: {e}")
    
    return speed


def get_network_interfaces() -> Dict[str, Dict[str, Any]]:
    """
    Get all available network interfaces.
    
    Returns:
        Dictionary of interfaces with their details
    """
    interfaces = {}
    
    # If netifaces is not available, use a platform-specific approach
    if not HAS_NETIFACES:
        if platform.system() == "Windows":
            interfaces = _get_windows_interfaces()
        elif platform.system() == "Linux":
            interfaces = _get_linux_interfaces()
        elif platform.system() == "Darwin":  # macOS
            interfaces = _get_macos_interfaces()
    else:
        interfaces = _get_interfaces_with_netifaces()
    
    return interfaces


def _get_windows_interfaces() -> Dict[str, Dict[str, Any]]:
    """Get network interfaces on Windows."""
    interfaces = {}
    try:
        # Use ipconfig to get interfaces on Windows
        stdout, _, _ = run_command(["ipconfig", "/all"])
        if stdout:
            current_if = None
            for line in stdout.split('\n'):
                if "adapter" in line and ":" in line:
                    current_if = line.split(":")[0].strip()
                    interfaces[current_if] = {
                        'name': current_if,
                        'ip_address': '',
                        'netmask': '',
                        'is_wireless': 'wireless' in current_if.lower() or 'wi-fi' in current_if.lower(),
                        'mac_address': ''
                    }
                elif current_if and "IPv4 Address" in line and ":" in line:
                    ip = line.split(":")[-1].strip()
                    # Remove (Preferred) suffix if present
                    ip = ip.split('(')[0].strip()
                    if current_if in interfaces:
                        interfaces[current_if]['ip_address'] = ip
                elif current_if and "Subnet Mask" in line and ":" in line:
                    mask = line.split(":")[-1].strip()
                    if current_if in interfaces:
                        interfaces[current_if]['netmask'] = mask
                elif current_if and "Physical Address" in line and ":" in line:
                    mac = line.split(":")[-1].strip()
                    if current_if in interfaces:
                        interfaces[current_if]['mac_address'] = mac
    except Exception as e:
        logger.error(f"Error getting network interfaces with ipconfig: {e}")
    return interfaces


def _get_linux_interfaces() -> Dict[str, Dict[str, Any]]:
    """Get network interfaces on Linux."""
    interfaces = {}
    try:
        # Use ifconfig on Linux
        stdout, _, _ = run_command(["ifconfig", "-a"])
        if stdout:
            sections = stdout.split('\n\n')
            for section in sections:
                if not section.strip():
                    continue
                lines = section.split('\n')
                if lines:
                    if_name = lines[0].split(':')[0].strip()
                    is_wireless = if_name.startswith('wl') or 'wlan' in if_name
                    ip_address = ''
                    mac_address = ''
                    netmask = ''
                    
                    for line in lines:
                        if 'inet ' in line:
                            parts = line.strip().split()
                            inet_idx = parts.index('inet')
                            if inet_idx + 1 < len(parts):
                                ip_address = parts[inet_idx + 1]
                            # Try to find netmask
                            if 'netmask' in line:
                                netmask_idx = parts.index('netmask')
                                if netmask_idx + 1 < len(parts):
                                    netmask = parts[netmask_idx + 1]
                        elif 'ether ' in line:
                            parts = line.strip().split()
                            ether_idx = parts.index('ether')
                            if ether_idx + 1 < len(parts):
                                mac_address = parts[ether_idx + 1]
                    
                    interfaces[if_name] = {
                        'name': if_name,
                        'ip_address': ip_address,
                        'netmask': netmask,
                        'is_wireless': is_wireless,
                        'mac_address': mac_address
                    }
    except Exception as e:
        logger.error(f"Error getting network interfaces with ifconfig: {e}")
        
        # Try with ip command if ifconfig fails
        try:
            stdout, _, _ = run_command(["ip", "addr"])
            if stdout:
                current_if = None
                for line in stdout.split('\n'):
                    if line.startswith(' '):
                        # Continuation of previous interface
                        if current_if:
                            # Look for inet (IPv4) address
                            if 'inet ' in line:
                                parts = line.strip().split()
                                addr_idx = parts.index('inet')
                                if addr_idx + 1 < len(parts):
                                    # Format is typically "inet 192.168.1.1/24"
                                    ip_cidr = parts[addr_idx + 1]
                                    if '/' in ip_cidr:
                                        ip = ip_cidr.split('/')[0]
                                        interfaces[current_if]['ip_address'] = ip
                            # Look for link/ether (MAC) address
                            elif 'link/ether' in line:
                                parts = line.strip().split()
                                if len(parts) >= 2:
                                    mac = parts[1]
                                    interfaces[current_if]['mac_address'] = mac
                    else:
                        # New interface
                        match = re.search(r'^\d+:\s+([^:]+):', line)
                        if match:
                            current_if = match.group(1)
                            is_wireless = current_if.startswith('wl') or 'wlan' in current_if
                            interfaces[current_if] = {
                                'name': current_if,
                                'ip_address': '',
                                'netmask': '',
                                'is_wireless': is_wireless,
                                'mac_address': ''
                            }
        except Exception as e:
            logger.error(f"Error getting network interfaces with ip: {e}")
    
    return interfaces


def _get_macos_interfaces() -> Dict[str, Dict[str, Any]]:
    """Get network interfaces on macOS."""
    interfaces = {}
    try:
        # Use ifconfig on macOS
        stdout, _, _ = run_command(["ifconfig"])
        if stdout:
            sections = stdout.split('\n\n')
            for section in sections:
                if not section.strip():
                    continue
                lines = section.split('\n')
                if lines:
                    if_name = lines[0].split(':')[0].strip()
                    is_wireless = if_name.startswith('en') and not if_name.startswith('eth')
                    ip_address = ''
                    mac_address = ''
                    netmask = ''
                    
                    for line in lines:
                        if 'inet ' in line:
                            parts = line.strip().split()
                            inet_idx = parts.index('inet')
                            if inet_idx + 1 < len(parts):
                                ip_address = parts[inet_idx + 1]
                            # Try to find netmask
                            if 'netmask' in line:
                                netmask_idx = parts.index('netmask')
                                if netmask_idx + 1 < len(parts):
                                    # On macOS, netmask is often in hex format (0xffffff00)
                                    netmask_hex = parts[netmask_idx + 1]
                                    if netmask_hex.startswith('0x'):
                                        # Convert hex netmask to dotted decimal
                                        netmask_int = int(netmask_hex, 16)
                                        netmask = '.'.join([str((netmask_int >> (24 - i * 8)) & 0xFF) for i in range(4)])
                        elif 'ether ' in line:
                            parts = line.strip().split()
                            ether_idx = parts.index('ether')
                            if ether_idx + 1 < len(parts):
                                mac_address = parts[ether_idx + 1]
                    
                    interfaces[if_name] = {
                        'name': if_name,
                        'ip_address': ip_address,
                        'netmask': netmask,
                        'is_wireless': is_wireless,
                        'mac_address': mac_address
                    }
    except Exception as e:
        logger.error(f"Error getting network interfaces with ifconfig: {e}")
    
    return interfaces


def _get_interfaces_with_netifaces() -> Dict[str, Dict[str, Any]]:
    """Get network interfaces using netifaces module."""
    interfaces = {}
    
    try:
        for interface in netifaces.interfaces():
            try:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    # Get IP details
                    ip_info = addrs[netifaces.AF_INET][0]
                    
                    # Check if this is a wireless interface
                    is_wireless = _is_wireless_interface(interface)
                    
                    # Get MAC address
                    mac_address = ''
                    if netifaces.AF_LINK in addrs:
                        mac_address = addrs[netifaces.AF_LINK][0].get('addr', '')
                    
                    # Store the interface details
                    interfaces[interface] = {
                        'name': interface,
                        'ip_address': ip_info.get('addr', ''),
                        'netmask': ip_info.get('netmask', ''),
                        'is_wireless': is_wireless,
                        'mac_address': mac_address
                    }
            except Exception as e:
                logger.error(f"Error processing interface {interface}: {e}")
    except Exception as e:
        logger.error(f"Error using netifaces to get interfaces: {e}")
    
    return interfaces


def get_active_interface() -> Optional[str]:
    """
    Determine the currently active network interface.
    
    Returns:
        Name of the active interface or None if not found
    """
    # Get all interfaces
    interfaces = get_network_interfaces()
    
    # First try to find the interface with the default route
    try:
        if platform.system() == "Windows":
            stdout, _, _ = run_command(["route", "print", "0.0.0.0"])
            if stdout:
                lines = stdout.split('\n')
                for line in lines:
                    if "0.0.0.0" in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            interface_idx = parts[4]
                            # Now find the interface with this index
                            for name, details in interfaces.items():
                                if details.get('interface_idx') == interface_idx:
                                    return name
        elif platform.system() == "Linux":
            stdout, _, _ = run_command(["ip", "route", "show", "default"])
            if stdout:
                # Example: "default via 192.168.1.1 dev wlan0 proto static"
                match = re.search(r"dev\s+(\S+)", stdout)
                if match:
                    return match.group(1)
        elif platform.system() == "Darwin":  # macOS
            stdout, _, _ = run_command(["route", "-n", "get", "default"])
            if stdout:
                match = re.search(r"interface:\s+(\S+)", stdout)
                if match:
                    return match.group(1)
    except Exception as e:
        logger.error(f"Error finding interface with default route: {e}")
    
    # If default route lookup failed, try connectivity test
    for interface, details in interfaces.items():
        if details['ip_address']:
            try:
                # Test connectivity
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1)
                sock.connect(("8.8.8.8", 80))
                sock.close()
                return interface
            except:
                pass
    
    # Fall back to the first interface with an IP
    for interface, details in interfaces.items():
        if details['ip_address']:
            return interface
            
    return None 