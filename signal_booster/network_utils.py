"""
Network utilities for Signal Booster.
This module provides specialized functions for network optimization.
This is a compatibility module and will be deprecated in favor of using signal_booster.network directly.
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
import numpy as np

# Setup logger
logger = logging.getLogger(__name__)

# Try to import speedtest but don't fail if it's not available
try:
    import speedtest
    HAS_SPEEDTEST = True
except ImportError:
    logger.warning("speedtest-cli not available, speed testing functionality will be limited")
    HAS_SPEEDTEST = False

# Try to import netifaces but don't fail if it's not available
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

# Implementation of helper functions - no circular imports
def _get_interface_speed(interface_name: str) -> int:
    """Get the speed of a network interface in Mbps."""
    speed = 100  # Default to 100 Mbps
    
    try:
        if platform.system() == "Windows":
            # On Windows, we can get the speed from the registry
            key_path = f"SYSTEM\\CurrentControlSet\\Control\\Class\\{{4D36E972-E325-11CE-BFC1-08002BE10318}}\\0000"
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                speed_value = winreg.QueryValueEx(key, "LinkSpeed")[0]
                if isinstance(speed_value, int):
                    speed = speed_value
                winreg.CloseKey(key)
            except Exception:
                pass
        elif platform.system() == "Linux":
            # On Linux, we can get the speed from /sys/class/net
            try:
                with open(f"/sys/class/net/{interface_name}/speed", "r") as f:
                    speed = int(f.read().strip())
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Error getting interface speed: {e}")
    
    return speed

# Direct implementations of utility functions without imports from signal_booster.network

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
        if HAS_SPEEDTEST:
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
        else:
            # Fallback to a conservative estimate
            result["download"] = 10.0  # 10 Mbps
            result["upload"] = 2.0     # 2 Mbps
            result["ping"] = 50.0      # 50 ms
    except Exception as e:
        logger.error(f"Error measuring speed: {e}")
    
    return result

def get_network_interfaces() -> Dict[str, Dict[str, Any]]:
    """Get a dictionary of network interfaces and their details."""
    interfaces = {}
    
    try:
        if HAS_NETIFACES:
            # Use netifaces to get interface information
            for iface in netifaces.interfaces():
                interfaces[iface] = {
                    'name': iface,
                    'ip_address': None,
                    'mac_address': None,
                    'is_wireless': False,
                    'speed': 0
                }
                
                # Get addresses (IP, MAC)
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    interfaces[iface]['ip_address'] = addrs[netifaces.AF_INET][0].get('addr')
                if netifaces.AF_LINK in addrs:
                    interfaces[iface]['mac_address'] = addrs[netifaces.AF_LINK][0].get('addr')
                
                # Try to determine if wireless (approximate)
                if 'wi' in iface.lower() or 'wl' in iface.lower():
                    interfaces[iface]['is_wireless'] = True
                
                # Get interface speed
                interfaces[iface]['speed'] = _get_interface_speed(iface)
        else:
            # Fallback to using psutil
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for iface, addrs in net_if_addrs.items():
                ip_addr = None
                mac_addr = None
                
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ip_addr = addr.address
                    elif addr.family == psutil.AF_LINK:
                        mac_addr = addr.address
                
                speed = 0
                if iface in net_if_stats:
                    speed = net_if_stats[iface].speed
                
                # Simple heuristic to guess if interface is wireless
                is_wireless = 'wi' in iface.lower() or 'wl' in iface.lower()
                
                interfaces[iface] = {
                    'name': iface,
                    'ip_address': ip_addr,
                    'mac_address': mac_addr,
                    'is_wireless': is_wireless,
                    'speed': speed
                }
    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
    
    return interfaces

def get_active_interface() -> Optional[str]:
    """Get the active network interface."""
    if HAS_NETIFACES:
        return netifaces.gateways()['default'][netifaces.AF_INET][0]
    else:
        logger.warning("netifaces not available, network interface detection will be limited")
        return None

def find_optimal_mtu(target: str = "8.8.8.8") -> int:
    """Find the optimal MTU size."""
    # Implementation of find_optimal_mtu function
    # This is a placeholder and should be replaced with the actual implementation
    return 1500  # Default value, actual implementation needed

def set_dns_servers(dns_servers: List[str], interface: Optional[str] = None) -> bool:
    """Set DNS servers."""
    # Implementation of set_dns_servers function
    # This is a placeholder and should be replaced with the actual implementation
    return False  # Default return, actual implementation needed

def get_wifi_signal_strength() -> int:
    """Get WiFi signal strength."""
    # Implementation of get_wifi_signal_strength function
    # This is a placeholder and should be replaced with the actual implementation
    return 0  # Default return, actual implementation needed

def find_best_wifi_channel() -> int:
    """Find the best WiFi channel."""
    # Implementation of find_best_wifi_channel function
    # This is a placeholder and should be replaced with the actual implementation
    return 0  # Default return, actual implementation needed

def optimize_tcp_settings() -> bool:
    """Optimize TCP settings."""
    # Implementation of optimize_tcp_settings function
    # This is a placeholder and should be replaced with the actual implementation
    return False  # Default return, actual implementation needed

def optimize_wifi_settings(interface: Optional[str] = None) -> bool:
    """Optimize WiFi settings."""
    # Implementation of optimize_wifi_settings function
    # This is a placeholder and should be replaced with the actual implementation
    return False  # Default return, actual implementation needed

def prioritize_traffic() -> bool:
    """Prioritize network traffic."""
    # Implementation of prioritize_traffic function
    # This is a placeholder and should be replaced with the actual implementation
    return False  # Default return, actual implementation needed

def optimize_system_for_networking() -> bool:
    """Optimize system for networking."""
    # Implementation of optimize_system_for_networking function
    # This is a placeholder and should be replaced with the actual implementation
    return False  # Default return, actual implementation needed