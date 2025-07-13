"""
Platform dispatcher for network utilities.
Provides a unified interface to platform-specific implementations.
"""

import platform
import logging
from typing import List, Optional, Union, Tuple, Dict, Any

logger = logging.getLogger(__name__)

def get_platform() -> str:
    """
    Determine the current platform.
    
    Returns:
        String identifying the platform: 'windows', 'linux', 'macos', or 'unknown'
    """
    system = platform.system().lower()
    if system == 'darwin':
        return 'macos'
    elif system in ('windows', 'linux'):
        return system
    else:
        logger.warning(f"Unsupported platform: {system}")
        return 'unknown'

def set_dns_servers(dns_servers: List[str], interface: Optional[str] = None) -> bool:
    """
    Set DNS servers based on the current platform.
    
    Args:
        dns_servers: List of DNS server IP addresses
        interface: Network interface to set DNS servers for (optional)
        
    Returns:
        True if successful, False otherwise
    """
    platform_name = get_platform()
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import set_windows_dns
            return set_windows_dns(dns_servers, interface)
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import set_linux_dns
            return set_linux_dns(dns_servers, interface)
        elif platform_name == 'macos':
            from signal_booster.network.platform.macos import set_macos_dns
            return set_macos_dns(dns_servers, interface)
        else:
            logger.error(f"Unsupported platform for DNS configuration: {platform_name}")
            return False
    except Exception as e:
        logger.error(f"Error setting DNS servers: {e}")
        return False

def get_wifi_signal_strength() -> int:
    """
    Get the current WiFi signal strength based on the current platform.
    
    Returns:
        Signal strength as a percentage (0-100)
    """
    platform_name = get_platform()
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import get_windows_wifi_signal
            return get_windows_wifi_signal()
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import get_linux_wifi_signal
            return get_linux_wifi_signal()
        elif platform_name == 'macos':
            from signal_booster.network.platform.macos import get_macos_wifi_signal
            return get_macos_wifi_signal()
        else:
            logger.error(f"Unsupported platform for WiFi signal strength: {platform_name}")
            # Return a default value if platform is not supported
            return 60
    except Exception as e:
        logger.error(f"Error getting WiFi signal strength: {e}")
        # Return a default value in case of error
        return 60
        
def find_best_wifi_channel() -> int:
    """
    Find the best WiFi channel based on the current platform.
    
    Returns:
        Channel number
    """
    platform_name = get_platform()
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import find_windows_best_channel
            return find_windows_best_channel()
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import find_linux_best_channel
            return find_linux_best_channel()
        elif platform_name == 'macos':
            from signal_booster.network.platform.macos import find_macos_best_channel
            return find_macos_best_channel()
        else:
            logger.error(f"Unsupported platform for WiFi channel optimization: {platform_name}")
            # Return a default value if platform is not supported
            return 6  # Channel 6 is a common default
    except Exception as e:
        logger.error(f"Error finding best WiFi channel: {e}")
        # Return a default value in case of error
        return 6

def measure_jitter(host: str = "8.8.8.8", count: int = 10) -> float:
    """
    Measure network jitter based on the current platform.
    
    Args:
        host: Target host to ping (default: 8.8.8.8)
        count: Number of pings to perform
        
    Returns:
        Jitter value in milliseconds
    """
    platform_name = get_platform()
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import measure_windows_jitter
            return measure_windows_jitter(host, count)
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import measure_linux_jitter
            return measure_linux_jitter(host, count)
        elif platform_name == 'macos':
            # If macOS implementation is available, use it
            # Otherwise, fall back to Linux implementation which might work similarly
            try:
                from signal_booster.network.platform.macos import measure_macos_jitter
                return measure_macos_jitter(host, count)
            except ImportError:
                from signal_booster.network.platform.linux import measure_linux_jitter
                return measure_linux_jitter(host, count)
        else:
            logger.error(f"Unsupported platform for jitter measurement: {platform_name}")
            return 0.0
    except Exception as e:
        logger.error(f"Error measuring jitter: {e}")
        return 0.0

def measure_packet_loss(host: str = "8.8.8.8", count: int = 10) -> float:
    """
    Measure packet loss percentage based on the current platform.
    
    Args:
        host: Target host to ping (default: 8.8.8.8)
        count: Number of pings to perform
        
    Returns:
        Packet loss percentage (0-100)
    """
    platform_name = get_platform()
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import measure_windows_packet_loss
            return measure_windows_packet_loss(host, count)
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import measure_linux_packet_loss
            return measure_linux_packet_loss(host, count)
        elif platform_name == 'macos':
            # If macOS implementation is available, use it
            # Otherwise, fall back to Linux implementation which might work similarly
            try:
                from signal_booster.network.platform.macos import measure_macos_packet_loss
                return measure_macos_packet_loss(host, count)
            except ImportError:
                from signal_booster.network.platform.linux import measure_linux_packet_loss
                return measure_linux_packet_loss(host, count)
        else:
            logger.error(f"Unsupported platform for packet loss measurement: {platform_name}")
            return 0.0
    except Exception as e:
        logger.error(f"Error measuring packet loss: {e}")
        return 0.0

def measure_bandwidth(duration: int = 5) -> Dict[str, float]:
    """
    Measure network bandwidth based on the current platform.
    
    Args:
        duration: Duration in seconds for the bandwidth test
        
    Returns:
        Dictionary with download and upload speeds in Mbps
    """
    platform_name = get_platform()
    result = {"download": 0.0, "upload": 0.0}
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import measure_windows_bandwidth
            return measure_windows_bandwidth(duration)
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import measure_linux_bandwidth
            return measure_linux_bandwidth(duration)
        elif platform_name == 'macos':
            # If macOS implementation is available, use it
            # Otherwise, fall back to Linux implementation which might work similarly
            try:
                from signal_booster.network.platform.macos import measure_macos_bandwidth
                return measure_macos_bandwidth(duration)
            except ImportError:
                from signal_booster.network.platform.linux import measure_linux_bandwidth
                return measure_linux_bandwidth(duration)
        else:
            logger.error(f"Unsupported platform for bandwidth measurement: {platform_name}")
            return result
    except Exception as e:
        logger.error(f"Error measuring bandwidth: {e}")
        return result

def analyze_network_congestion(interface: Optional[str] = None) -> float:
    """
    Analyze network congestion based on the current platform.
    
    Args:
        interface: Network interface to analyze (if None, uses active interface)
        
    Returns:
        Congestion percentage (0-100)
    """
    platform_name = get_platform()
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import analyze_windows_network_congestion
            return analyze_windows_network_congestion(interface)
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import analyze_linux_network_congestion
            return analyze_linux_network_congestion(interface)
        elif platform_name == 'macos':
            # If macOS implementation is available, use it
            # Otherwise, fall back to Linux implementation which might work similarly
            try:
                from signal_booster.network.platform.macos import analyze_macos_network_congestion
                return analyze_macos_network_congestion(interface)
            except ImportError:
                from signal_booster.network.platform.linux import analyze_linux_network_congestion
                return analyze_linux_network_congestion(interface)
        else:
            logger.error(f"Unsupported platform for network congestion analysis: {platform_name}")
            return 30.0  # Default to moderate congestion
    except Exception as e:
        logger.error(f"Error analyzing network congestion: {e}")
        return 30.0  # Default to moderate congestion

def clear_network_buffers() -> bool:
    """
    Clear network buffers based on the current platform.
    
    Returns:
        True if successful, False otherwise
    """
    platform_name = get_platform()
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import clear_windows_network_buffers
            return clear_windows_network_buffers()
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import clear_linux_network_buffers
            return clear_linux_network_buffers()
        elif platform_name == 'macos':
            # If macOS implementation is available, use it
            # Otherwise, return False
            try:
                from signal_booster.network.platform.macos import clear_macos_network_buffers
                return clear_macos_network_buffers()
            except ImportError:
                logger.error("Network buffer clearing not implemented for macOS")
                return False
        else:
            logger.error(f"Unsupported platform for clearing network buffers: {platform_name}")
            return False
    except Exception as e:
        logger.error(f"Error clearing network buffers: {e}")
        return False

def get_detailed_network_interfaces() -> List[Dict[str, Any]]:
    """
    Get detailed information about network interfaces based on the current platform.
    
    Returns:
        List of dictionaries containing interface details
    """
    platform_name = get_platform()
    
    try:
        if platform_name == 'windows':
            from signal_booster.network.platform.windows import get_windows_network_interfaces
            return get_windows_network_interfaces()
        elif platform_name == 'linux':
            from signal_booster.network.platform.linux import get_linux_network_interfaces
            return get_linux_network_interfaces()
        elif platform_name == 'macos':
            # If macOS implementation is available, use it
            # Otherwise, return an empty list
            try:
                from signal_booster.network.platform.macos import get_macos_network_interfaces
                return get_macos_network_interfaces()
            except ImportError:
                logger.error("Detailed network interface retrieval not implemented for macOS")
                return []
        else:
            logger.error(f"Unsupported platform for detailed network interface retrieval: {platform_name}")
            return []
    except Exception as e:
        logger.error(f"Error getting detailed network interfaces: {e}")
        return [] 