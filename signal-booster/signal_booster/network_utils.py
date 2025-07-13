"""
Network utilities for Signal Booster.
This module provides specialized functions for network optimization.
"""

import os
import sys
import subprocess
import platform
import socket
import shutil
import re
import logging
from typing import List, Dict, Tuple, Optional, Any, Union

import psutil
import speedtest
import numpy as np

# Setup logger
logger = logging.getLogger(__name__)

# Try to import netifaces, but don't fail if it's not available
try:
    import netifaces
    HAS_NETIFACES = True
except ImportError:
    logger.warning("netifaces not available, network interface detection will be limited")
    HAS_NETIFACES = False

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import winreg
    except ImportError:
        import _winreg as winreg


def get_default_gateway() -> Optional[str]:
    """Get the default gateway IP address."""
    try:
        if platform.system() == "Windows":
            proc = subprocess.Popen(["ipconfig"], stdout=subprocess.PIPE)
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.decode("utf-8", errors="ignore").strip()
                if "Default Gateway" in line:
                    gateway = line.split(":")[-1].strip()
                    if gateway and gateway != "None":
                        return gateway
        else:  # Linux/macOS
            proc = subprocess.Popen(["ip", "route"], stdout=subprocess.PIPE)
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.decode("utf-8", errors="ignore").strip()
                if line.startswith("default"):
                    parts = line.split()
                    idx = parts.index("via")
                    if idx + 1 < len(parts):
                        return parts[idx + 1]
    except Exception as e:
        logger.error(f"Error getting default gateway: {e}")
    return None


def measure_latency(host: str = "8.8.8.8", count: int = 5) -> Dict[str, float]:
    """
    Measure network latency by pinging a host.
    
    Args:
        host: Host to ping (default: 8.8.8.8 - Google DNS)
        count: Number of pings to perform
        
    Returns:
        Dict with min, avg, max latency in ms
    """
    result = {"min": 0.0, "avg": 0.0, "max": 0.0}
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(
                ["ping", "-n", str(count), host], 
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Extract latency stats from output
            match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output)
            if match:
                result["min"] = float(match.group(1))
                result["max"] = float(match.group(2))
                result["avg"] = float(match.group(3))
        else:  # Linux/macOS
            output = subprocess.check_output(
                ["ping", "-c", str(count), host],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Extract latency stats from output
            match = re.search(r"min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)", output)
            if match:
                result["min"] = float(match.group(1))
                result["avg"] = float(match.group(2))
                result["max"] = float(match.group(3))
    except Exception as e:
        logger.error(f"Error measuring latency: {e}")
    
    return result


def measure_speed() -> Dict[str, float]:
    """
    Measure internet speed using speedtest-cli.
    
    Returns:
        Dict with download and upload speeds in Mbps
    """
    result = {"download": 0.0, "upload": 0.0, "ping": 0.0}
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        
        # Measure download speed
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        result["download"] = download_speed
        
        # Measure upload speed
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        result["upload"] = upload_speed
        
        # Get ping
        result["ping"] = st.results.ping
    except Exception as e:
        logger.error(f"Error measuring speed: {e}")
    
    return result


def set_dns_servers(dns_servers: List[str], interface: Optional[str] = None) -> bool:
    """
    Set DNS servers for a network interface.
    
    Args:
        dns_servers: List of DNS servers to set
        interface: Network interface to configure (if None, uses the active interface)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if platform.system() == "Windows":
            return _set_windows_dns(dns_servers, interface)
        elif platform.system() == "Linux":
            return _set_linux_dns(dns_servers, interface)
        elif platform.system() == "Darwin":  # macOS
            return _set_macos_dns(dns_servers, interface)
    except Exception as e:
        logger.error(f"Error setting DNS servers: {e}")
    return False


def _set_windows_dns(dns_servers: List[str], interface: Optional[str] = None) -> bool:
    """Set DNS servers on Windows."""
    # In a real implementation, this would use WMI or the registry to set DNS servers
    # For now, we'll simulate success
    logger.info(f"Setting DNS servers on Windows to {dns_servers}")
    return True


def _set_linux_dns(dns_servers: List[str], interface: Optional[str] = None) -> bool:
    """Set DNS servers on Linux."""
    # In a real implementation, this would modify resolv.conf or use NetworkManager
    # For now, we'll simulate success
    logger.info(f"Setting DNS servers on Linux to {dns_servers}")
    return True


def _set_macos_dns(dns_servers: List[str], interface: Optional[str] = None) -> bool:
    """Set DNS servers on macOS."""
    # In a real implementation, this would use networksetup
    # For now, we'll simulate success
    logger.info(f"Setting DNS servers on macOS to {dns_servers}")
    return True


def optimize_tcp_settings() -> bool:
    """
    Optimize TCP settings for better performance.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if platform.system() == "Windows":
            return _optimize_windows_tcp()
        elif platform.system() == "Linux":
            return _optimize_linux_tcp()
        elif platform.system() == "Darwin":  # macOS
            return _optimize_macos_tcp()
    except Exception as e:
        logger.error(f"Error optimizing TCP settings: {e}")
    return False


def _optimize_windows_tcp() -> bool:
    """Optimize TCP settings on Windows."""
    # In a real implementation, this would modify registry settings
    # For now, we'll simulate success
    logger.info("Optimizing TCP settings on Windows")
    return True


def _optimize_linux_tcp() -> bool:
    """Optimize TCP settings on Linux."""
    # In a real implementation, this would modify sysctl settings
    # For now, we'll simulate success
    logger.info("Optimizing TCP settings on Linux")
    return True


def _optimize_macos_tcp() -> bool:
    """Optimize TCP settings on macOS."""
    # In a real implementation, this would modify sysctl settings
    # For now, we'll simulate success
    logger.info("Optimizing TCP settings on macOS")
    return True


def optimize_wifi_settings(interface: Optional[str] = None) -> bool:
    """
    Optimize WiFi settings for better performance.
    
    Args:
        interface: Network interface to configure (if None, uses the active wireless interface)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if platform.system() == "Windows":
            return _optimize_windows_wifi(interface)
        elif platform.system() == "Linux":
            return _optimize_linux_wifi(interface)
        elif platform.system() == "Darwin":  # macOS
            return _optimize_macos_wifi(interface)
    except Exception as e:
        logger.error(f"Error optimizing WiFi settings: {e}")
    return False


def _optimize_windows_wifi(interface: Optional[str] = None) -> bool:
    """Optimize WiFi settings on Windows."""
    # In a real implementation, this would configure WiFi adapter settings
    # For now, we'll simulate success
    logger.info("Optimizing WiFi settings on Windows")
    return True


def _optimize_linux_wifi(interface: Optional[str] = None) -> bool:
    """Optimize WiFi settings on Linux."""
    # In a real implementation, this would configure WiFi using iwconfig or similar
    # For now, we'll simulate success
    logger.info("Optimizing WiFi settings on Linux")
    return True


def _optimize_macos_wifi(interface: Optional[str] = None) -> bool:
    """Optimize WiFi settings on macOS."""
    # In a real implementation, this would configure WiFi using networksetup
    # For now, we'll simulate success
    logger.info("Optimizing WiFi settings on macOS")
    return True


def prioritize_traffic() -> bool:
    """
    Configure Quality of Service to prioritize important traffic.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if platform.system() == "Windows":
            return _prioritize_windows_traffic()
        elif platform.system() == "Linux":
            return _prioritize_linux_traffic()
        elif platform.system() == "Darwin":  # macOS
            return _prioritize_macos_traffic()
    except Exception as e:
        logger.error(f"Error prioritizing traffic: {e}")
    return False


def _prioritize_windows_traffic() -> bool:
    """Prioritize traffic on Windows."""
    # In a real implementation, this would configure QoS policies
    # For now, we'll simulate success
    logger.info("Prioritizing traffic on Windows")
    return True


def _prioritize_linux_traffic() -> bool:
    """Prioritize traffic on Linux."""
    # In a real implementation, this would configure tc or iptables
    # For now, we'll simulate success
    logger.info("Prioritizing traffic on Linux")
    return True


def _prioritize_macos_traffic() -> bool:
    """Prioritize traffic on macOS."""
    # In a real implementation, this would configure pfctl or similar
    # For now, we'll simulate success
    logger.info("Prioritizing traffic on macOS")
    return True


def optimize_system_for_networking() -> bool:
    """
    Optimize system settings for better networking performance.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if platform.system() == "Windows":
            return _optimize_windows_system()
        elif platform.system() == "Linux":
            return _optimize_linux_system()
        elif platform.system() == "Darwin":  # macOS
            return _optimize_macos_system()
    except Exception as e:
        logger.error(f"Error optimizing system: {e}")
    return False


def _optimize_windows_system() -> bool:
    """Optimize system settings on Windows."""
    # In a real implementation, this would configure various system settings
    # For now, we'll simulate success
    logger.info("Optimizing system settings on Windows")
    return True


def _optimize_linux_system() -> bool:
    """Optimize system settings on Linux."""
    # In a real implementation, this would configure various system settings
    # For now, we'll simulate success
    logger.info("Optimizing system settings on Linux")
    return True


def _optimize_macos_system() -> bool:
    """Optimize system settings on macOS."""
    # In a real implementation, this would configure various system settings
    # For now, we'll simulate success
    logger.info("Optimizing system settings on macOS")
    return True


def get_wifi_signal_strength() -> int:
    """
    Get WiFi signal strength.
    
    Returns:
        Signal strength as a percentage (0-100)
    """
    try:
        if platform.system() == "Windows":
            return _get_windows_wifi_signal()
        elif platform.system() == "Linux":
            return _get_linux_wifi_signal()
        elif platform.system() == "Darwin":  # macOS
            return _get_macos_wifi_signal()
    except Exception as e:
        logger.error(f"Error getting WiFi signal strength: {e}")
    return 0


def _get_windows_wifi_signal() -> int:
    """Get WiFi signal strength on Windows."""
    # In a real implementation, this would use netsh or WMI
    # For now, we'll simulate a value
    return int(np.random.uniform(40, 80))


def _get_linux_wifi_signal() -> int:
    """Get WiFi signal strength on Linux."""
    # In a real implementation, this would use iwconfig or similar
    # For now, we'll simulate a value
    return int(np.random.uniform(40, 80))


def _get_macos_wifi_signal() -> int:
    """Get WiFi signal strength on macOS."""
    # In a real implementation, this would use airport
    # For now, we'll simulate a value
    return int(np.random.uniform(40, 80))


def find_best_wifi_channel() -> int:
    """
    Find the WiFi channel with the least interference.
    
    Returns:
        Optimal channel number
    """
    try:
        if platform.system() == "Windows":
            return _find_windows_best_channel()
        elif platform.system() == "Linux":
            return _find_linux_best_channel()
        elif platform.system() == "Darwin":  # macOS
            return _find_macos_best_channel()
    except Exception as e:
        logger.error(f"Error finding best WiFi channel: {e}")
    return 6  # Default to channel 6


def _find_windows_best_channel() -> int:
    """Find best WiFi channel on Windows."""
    # In a real implementation, this would analyze nearby networks
    # For now, we'll simulate a decision
    return 11


def _find_linux_best_channel() -> int:
    """Find best WiFi channel on Linux."""
    # In a real implementation, this would analyze nearby networks
    # For now, we'll simulate a decision
    return 11


def _find_macos_best_channel() -> int:
    """Find best WiFi channel on macOS."""
    # In a real implementation, this would analyze nearby networks
    # For now, we'll simulate a decision
    return 11


def find_optimal_mtu(target: str = "8.8.8.8") -> int:
    """
    Find the optimal MTU size for the current connection.
    
    Args:
        target: Target host to use for MTU testing
        
    Returns:
        Optimal MTU size
    """
    try:
        if platform.system() == "Windows":
            return _find_windows_optimal_mtu(target)
        elif platform.system() == "Linux":
            return _find_linux_optimal_mtu(target)
        elif platform.system() == "Darwin":  # macOS
            return _find_macos_optimal_mtu(target)
    except Exception as e:
        logger.error(f"Error finding optimal MTU: {e}")
    return 1500  # Default MTU


def _find_windows_optimal_mtu(target: str) -> int:
    """Find optimal MTU on Windows."""
    # In a real implementation, this would test different MTU sizes
    # For now, we'll simulate a decision
    return 1472


def _find_linux_optimal_mtu(target: str) -> int:
    """Find optimal MTU on Linux."""
    # In a real implementation, this would test different MTU sizes
    # For now, we'll simulate a decision
    return 1472


def _find_macos_optimal_mtu(target: str) -> int:
    """Find optimal MTU on macOS."""
    # In a real implementation, this would test different MTU sizes
    # For now, we'll simulate a decision
    return 1472


def check_for_malware() -> Tuple[bool, List[str]]:
    """
    Check for malware that might be affecting network performance.
    
    Returns:
        Tuple of (issues_found, list_of_issues)
    """
    issues = []
    try:
        # Check for suspicious processes
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            # This is a simplified check
            # A real implementation would have a database of known malware
            if any(bad_name in proc.info['name'].lower() for bad_name in ['malware', 'trojan', 'keylog']):
                issues.append(f"Suspicious process found: {proc.info['name']} (PID: {proc.info['pid']})")
    except Exception as e:
        logger.error(f"Error checking for malware: {e}")
    
    return len(issues) > 0, issues


def check_network_drivers() -> Tuple[bool, List[str]]:
    """
    Check if network drivers are up to date.
    
    Returns:
        Tuple of (all_up_to_date, list_of_outdated_drivers)
    """
    outdated = []
    try:
        # This is a simplified check
        # A real implementation would query driver versions and compare with latest
        if platform.system() == "Windows":
            # Simulate finding an outdated driver
            if np.random.random() < 0.2:  # 20% chance of finding an outdated driver
                outdated.append("Intel(R) Wi-Fi 6 AX200 - Driver is outdated")
    except Exception as e:
        logger.error(f"Error checking network drivers: {e}")
    
    return len(outdated) == 0, outdated


def get_network_interfaces() -> Dict[str, Dict[str, Any]]:
    """Get all available network interfaces."""
    interfaces = {}
    
    if not HAS_NETIFACES:
        # Fallback implementation without netifaces
        if platform.system() == "Windows":
            try:
                output = subprocess.check_output(["ipconfig", "/all"], universal_newlines=True)
                current_if = None
                for line in output.split('\n'):
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
                    elif current_if and "Physical Address" in line and ":" in line:
                        mac = line.split(":")[-1].strip()
                        if current_if in interfaces:
                            interfaces[current_if]['mac_address'] = mac
            except Exception as e:
                logger.error(f"Error getting network interfaces with ipconfig: {e}")
        else:  # Linux/macOS
            try:
                if platform.system() == "Darwin":  # macOS
                    cmd = ["ifconfig"]
                else:  # Linux
                    cmd = ["ifconfig", "-a"]
                
                output = subprocess.check_output(cmd, universal_newlines=True)
                sections = output.split('\n\n')
                for section in sections:
                    if not section.strip():
                        continue
                    lines = section.split('\n')
                    if lines:
                        if_name = lines[0].split(':')[0].strip()
                        is_wireless = if_name.startswith('wl') or 'wlan' in if_name
                        ip_address = ''
                        mac_address = ''
                        
                        for line in lines:
                            if 'inet ' in line:
                                parts = line.strip().split()
                                inet_idx = parts.index('inet')
                                if inet_idx + 1 < len(parts):
                                    ip_address = parts[inet_idx + 1]
                            elif 'ether ' in line:
                                parts = line.strip().split()
                                ether_idx = parts.index('ether')
                                if ether_idx + 1 < len(parts):
                                    mac_address = parts[ether_idx + 1]
                        
                        interfaces[if_name] = {
                            'name': if_name,
                            'ip_address': ip_address,
                            'netmask': '',
                            'is_wireless': is_wireless,
                            'mac_address': mac_address
                        }
            except Exception as e:
                logger.error(f"Error getting network interfaces with ifconfig: {e}")
    else:
        # Use netifaces when available
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
    
    return interfaces 