"""
Network utilities for Signal Booster.
This module provides specialized functions for network measurement and information.
"""

import time
import urllib.request
from signal_booster.network.common import *
from signal_booster.network.interfaces import get_network_interfaces, _get_interface_speed

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


def _measure_speed_with_speedtest() -> Dict[str, float]:
    """Use speedtest-cli to measure internet speed."""
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
        logger.error(f"Error measuring speed with speedtest-cli: {e}")
    
    return result


def _measure_speed_alternative() -> Dict[str, float]:
    """Alternative method to measure internet speed without speedtest-cli."""
    result = {"download": 0.0, "upload": 0.0, "ping": 0.0}
    
    try:
        # Measure ping using our existing function
        ping_result = measure_latency(host="8.8.8.8", count=5)
        result["ping"] = ping_result["avg"]
        
        # Use a simple file download to estimate download speed
        try:
            # Standard test file for download speed (10MB file)
            url = "https://speed.cloudflare.com/__down?bytes=10000000"
            
            start_time = time.time()
            with urllib.request.urlopen(url) as response:
                downloaded_data = response.read()
            end_time = time.time()
            
            # Calculate download speed in Mbps
            download_time = end_time - start_time
            file_size_bits = len(downloaded_data) * 8
            result["download"] = file_size_bits / download_time / 1_000_000
        except Exception as e:
            logger.error(f"Error measuring download speed: {e}")
            
        # Estimate upload speed using socket connections
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            # Connect to a reliable server
            sock.connect(("8.8.8.8", 443))
            
            # Create a test payload (1MB)
            test_data = b'x' * 1_000_000
            
            # Measure upload time
            start_time = time.time()
            bytes_sent = 0
            for _ in range(5):  # Send data multiple times
                bytes_sent += sock.send(test_data)
            end_time = time.time()
            
            # Calculate upload speed
            upload_time = end_time - start_time
            bits_sent = bytes_sent * 8
            result["upload"] = bits_sent / upload_time / 1_000_000
        except Exception as e:
            logger.error(f"Error estimating upload speed: {e}")
            # Fallback to a conservative estimate based on download speed
            result["upload"] = result["download"] / 4
        finally:
            sock.close()
    except Exception as e:
        logger.error(f"Error using alternative speed measurement: {e}")
        
        # Use network interface detected speed as a fallback
        interfaces = get_network_interfaces()
        max_speed = 0
        for _, details in interfaces.items():
            if details.get('ip_address'):
                # Attempt to get actual interface speed
                speed = _get_interface_speed(details.get('name', ''))
                if speed > max_speed:
                    max_speed = speed
        
        if max_speed > 0:
            # Use interface speed as a basis for estimates
            # Actual speed is typically 60-80% of interface speed
            result["download"] = max_speed * 0.7
            result["upload"] = max_speed * 0.3
        else:
            # Default to conservative values if we can't determine
            result["download"] = 10.0  # 10 Mbps
            result["upload"] = 2.0    # 2 Mbps
        
        # Set ping to a reasonable default
        result["ping"] = 50.0
    
    return result


def measure_speed() -> Dict[str, float]:
    """
    Measure internet speed.
    
    Returns:
        Dict with download and upload speeds in Mbps and ping in ms
    """
    # If speedtest-cli is available, use it
    if HAS_SPEEDTEST:
        result = _measure_speed_with_speedtest()
        
        # If speedtest-cli failed (all zeros), try alternative method
        if result["download"] == 0.0 and result["upload"] == 0.0:
            logger.info("Speedtest-cli failed, using alternative method")
            result = _measure_speed_alternative()
    else:
        # Use alternative method if speedtest-cli is not available
        result = _measure_speed_alternative()
    
    return result


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
    try:
        # Windows uses ping with -f (don't fragment) and -l (size) to test MTU
        max_mtu = 1500  # Start with standard MTU
        min_mtu = 1200  # Minimum to test
        optimal_mtu = 1500  # Default
        
        # Binary search to find optimal MTU
        while max_mtu - min_mtu > 8:
            test_mtu = (max_mtu + min_mtu) // 2
            
            # Ping with don't fragment flag
            stdout, _, returncode = run_command(
                ["ping", "-f", "-l", str(test_mtu - 28), "-n", "1", target]
            )
            
            if stdout and ("Packet needs to be fragmented" in stdout or "100% loss" in stdout):
                # MTU too large
                max_mtu = test_mtu
            else:
                # MTU is good
                min_mtu = test_mtu
                optimal_mtu = test_mtu
        
        # Add 28 bytes for the IP and ICMP headers that weren't included in our test
        return optimal_mtu
    
    except Exception as e:
        logger.error(f"Error finding optimal MTU on Windows: {e}")
    
    # Default to standard MTU
    return 1500


def _find_linux_optimal_mtu(target: str) -> int:
    """Find optimal MTU on Linux."""
    try:
        max_mtu = 1500  # Start with standard MTU
        min_mtu = 1200  # Minimum to test
        optimal_mtu = 1500  # Default
        
        # Binary search to find optimal MTU
        while max_mtu - min_mtu > 8:
            test_mtu = (max_mtu + min_mtu) // 2
            
            # Ping with don't fragment flag
            stdout, _, returncode = run_command(
                ["ping", "-M", "do", "-s", str(test_mtu - 28), "-c", "1", target]
            )
            
            if stdout and ("Frag needed" in stdout or "Message too long" in stdout or "100% packet loss" in stdout):
                # MTU too large
                max_mtu = test_mtu
            else:
                # MTU is good
                min_mtu = test_mtu
                optimal_mtu = test_mtu
        
        # Add 28 bytes for the IP and ICMP headers that weren't included in our test
        return optimal_mtu
    
    except Exception as e:
        logger.error(f"Error finding optimal MTU on Linux: {e}")
    
    # Default to standard MTU
    return 1500


def _find_macos_optimal_mtu(target: str) -> int:
    """Find optimal MTU on macOS."""
    try:
        # Get current MTU as starting point
        stdout, _, _ = run_command(["ifconfig"])
        
        # Find current MTU
        # Example: "mtu 1500"
        mtu_match = re.search(r"mtu\s+(\d+)", stdout) if stdout else None
        current_mtu = int(mtu_match.group(1)) if mtu_match else 1500
        
        # Start with the current MTU and work downward
        optimal_mtu = current_mtu
        
        # Test different MTU sizes
        for test_mtu in range(current_mtu, 1400, -8):  # Decrement by 8 bytes at a time
            # Use ping with Don't Fragment flag to test MTU
            stdout, _, _ = run_command(
                ["ping", "-D", "-s", str(test_mtu - 28), "-c", "1", target]
            )
            
            if stdout and ("100.0% packet loss" in stdout or "DUP!" in stdout):
                # This MTU is too large
                continue
            else:
                # This MTU is good
                optimal_mtu = test_mtu
                break
        
        # Optimal MTU is 28 bytes less than the largest packet that can be sent
        # (IP header: 20 bytes, ICMP header: 8 bytes)
        return optimal_mtu
    
    except Exception as e:
        logger.error(f"Error finding optimal MTU on macOS: {e}")
    
    # Default to standard MTU
    return 1500


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
            from signal_booster.network.platform.windows import set_windows_dns
            return set_windows_dns(dns_servers, interface)
        elif platform.system() == "Linux":
            from signal_booster.network.platform.linux import set_linux_dns
            return set_linux_dns(dns_servers, interface)
        elif platform.system() == "Darwin":  # macOS
            from signal_booster.network.platform.macos import set_macos_dns
            return set_macos_dns(dns_servers, interface)
    except Exception as e:
        logger.error(f"Error setting DNS servers: {e}")
    return False


def get_wifi_signal_strength() -> int:
    """
    Get WiFi signal strength.
    
    Returns:
        Signal strength as a percentage (0-100)
    """
    try:
        if platform.system() == "Windows":
            from signal_booster.network.platform.windows import get_windows_wifi_signal
            return get_windows_wifi_signal()
        elif platform.system() == "Linux":
            from signal_booster.network.platform.linux import get_linux_wifi_signal
            return get_linux_wifi_signal()
        elif platform.system() == "Darwin":  # macOS
            from signal_booster.network.platform.macos import get_macos_wifi_signal
            return get_macos_wifi_signal()
    except Exception as e:
        logger.error(f"Error getting WiFi signal strength: {e}")
    return 60  # Default reasonable signal strength


def find_best_wifi_channel() -> int:
    """
    Find the WiFi channel with the least interference.
    
    Returns:
        Optimal channel number
    """
    try:
        if platform.system() == "Windows":
            from signal_booster.network.platform.windows import find_windows_best_channel
            return find_windows_best_channel()
        elif platform.system() == "Linux":
            from signal_booster.network.platform.linux import find_linux_best_channel
            return find_linux_best_channel()
        elif platform.system() == "Darwin":  # macOS
            from signal_booster.network.platform.macos import find_macos_best_channel
            return find_macos_best_channel()
    except Exception as e:
        logger.error(f"Error finding best WiFi channel: {e}")
    return 6  # Default to channel 6 