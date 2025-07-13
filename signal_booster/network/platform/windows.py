"""
Windows-specific network utilities for Signal Booster.
Handles Windows-specific network operations and optimizations.
"""

import os
import re
import subprocess
import logging
import ctypes
import winreg
from typing import List, Dict, Tuple, Optional, Any
import time

from signal_booster.network.common import logger, run_command
from signal_booster.network.interfaces import get_network_interfaces

logger = logging.getLogger(__name__)

# Check for admin privileges
def is_admin() -> bool:
    """
    Check if the current process has administrator privileges.
    
    Returns:
        Boolean indicating if the process has admin privileges
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.error(f"Error checking admin privileges: {e}")
        return False

def set_windows_dns(dns_servers: List[str], interface: Optional[str] = None) -> bool:
    """
    Set DNS servers on Windows.
    
    Args:
        dns_servers: List of DNS server IP addresses
        interface: Network interface to set DNS servers for (optional)
        
    Returns:
        True if successful, False otherwise
    """
    if not is_admin():
        logger.error("Administrator privileges required to set DNS servers")
        return False
    
    try:
        # If interface is not specified, get the active interface
        if not interface:
            interface = get_active_interface()
            if not interface:
                logger.error("Could not determine active network interface")
                return False
        
        # Format DNS servers as comma-separated string
        dns_string = ",".join(dns_servers)
        
        # Use netsh to set DNS servers
        cmd = f'netsh interface ip set dns name="{interface}" static {dns_servers[0]} primary'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to set primary DNS server: {result.stderr}")
            return False
        
        # Add additional DNS servers
        for i, dns in enumerate(dns_servers[1:], 1):
            cmd = f'netsh interface ip add dns name="{interface}" {dns} index={i+1}'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if result.returncode != 0:
                logger.error(f"Failed to add DNS server {dns}: {result.stderr}")
        
        # Flush DNS cache
        subprocess.run('ipconfig /flushdns', shell=True)
        
        logger.info(f"Successfully set DNS servers to {dns_string} on {interface}")
        return True
    except Exception as e:
        logger.error(f"Error setting DNS servers: {e}")
        return False

def get_active_interface() -> Optional[str]:
    """
    Get the name of the active network interface on Windows.
    
    Returns:
        Name of the active interface or None if not found
    """
    try:
        # Run ipconfig command to get network information
        result = subprocess.run('ipconfig', capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to get network interfaces: {result.stderr}")
            return None
        
        output = result.stdout
        
        # Find the active interface (one with an IPv4 address)
        interfaces = re.findall(r'Ethernet adapter (.*?):|Wireless LAN adapter (.*?):', output)
        
        # Flatten the list of tuples
        interface_names = []
        for iface in interfaces:
            interface_names.extend([name for name in iface if name])
        
        for name in interface_names:
            # Check if this interface has an IPv4 address
            pattern = f"({'|'.join([re.escape(name) for name in interface_names])}).*?IPv4 Address.*?: (\\d+\\.\\d+\\.\\d+\\.\\d+)"
            match = re.search(pattern, output, re.DOTALL)
            if match:
                return match.group(1)
        
        logger.warning("No active network interface found")
        return None
    except Exception as e:
        logger.error(f"Error getting active interface: {e}")
        return None

def get_windows_wifi_signal() -> int:
    """
    Get WiFi signal strength on Windows.
    
    Returns:
        Signal strength as a percentage (0-100)
    """
    try:
        # Use netsh to get wireless signal quality
        result = subprocess.run('netsh wlan show interfaces', capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to get WiFi signal strength: {result.stderr}")
            return 0
            
        output = result.stdout
        
        # Extract signal quality percentage
        match = re.search(r'Signal\s+:\s+(\d+)%', output)
        if match:
            return int(match.group(1))
        
        logger.warning("Could not determine WiFi signal strength")
        return 0
    except Exception as e:
        logger.error(f"Error getting WiFi signal strength: {e}")
        return 0

def find_windows_best_channel() -> int:
    """
    Find the best WiFi channel on Windows by analyzing available networks.
    
    Returns:
        Recommended channel number
    """
    try:
        # Get network information
        result = subprocess.run('netsh wlan show networks mode=bssid', capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to get WiFi networks: {result.stderr}")
            return 6  # Default to channel 6
            
        output = result.stdout
        
        # Extract channels from network list
        channels = re.findall(r'Channel\s+:\s+(\d+)', output)
        channel_count = {}
        
        # Count occurrences of each channel
        for channel in channels:
            channel_int = int(channel)
            if channel_int in channel_count:
                channel_count[channel_int] += 1
            else:
                channel_count[channel_int] = 1
        
        if not channel_count:
            logger.warning("No WiFi channels detected")
            return 6  # Default to channel 6
        
        # Find the least congested channel among the primary channels (1, 6, 11)
        primary_channels = {1: 0, 6: 0, 11: 0}
        
        for channel in primary_channels:
            # Count channels that would overlap
            for ch, count in channel_count.items():
                if abs(channel - ch) <= 2:  # Channels within 2 positions will overlap
                    primary_channels[channel] += count
        
        # Find channel with minimum interference
        best_channel = min(primary_channels.items(), key=lambda x: x[1])[0]
        logger.info(f"Best WiFi channel determined to be {best_channel}")
        return best_channel
    except Exception as e:
        logger.error(f"Error finding best WiFi channel: {e}")
        return 6  # Default to channel 6

def optimize_tcp_settings(params: Dict[str, Any]) -> bool:
    """
    Optimize TCP settings on Windows by setting registry values.
    
    Args:
        params: Dictionary of TCP parameters to set
        
    Returns:
        True if successful, False otherwise
    """
    if not is_admin():
        logger.error("Administrator privileges required to optimize TCP settings")
        return False
    
    try:
        # TCP/IP parameters are stored in the registry
        reg_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
        
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_WRITE) as key:
            # Set each TCP parameter
            for param_name, param_value in params.items():
                # Convert parameter name to Windows registry format if needed
                reg_name = param_name
                reg_type = winreg.REG_DWORD  # Default type for most TCP parameters
                
                # Set the registry value
                winreg.SetValueEx(key, reg_name, 0, reg_type, param_value)
                logger.info(f"Set TCP parameter {reg_name} to {param_value}")
        
        # Some changes require a system restart to take effect
        logger.info("TCP settings optimized. Some changes may require a system restart.")
        return True
    except Exception as e:
        logger.error(f"Error optimizing TCP settings: {e}")
        return False

def measure_windows_jitter(host: str = "8.8.8.8", count: int = 10) -> float:
    """
    Measure network jitter (latency variation) on Windows.
    
    Args:
        host: Target host to ping (default: 8.8.8.8)
        count: Number of pings to perform
        
    Returns:
        Jitter value in milliseconds
    """
    try:
        # Use ping to measure latency variation
        cmd = f'ping -n {count} {host}'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            # Extract the times from the ping output
            times = []
            for line in result.stdout.splitlines():
                # Look for lines like "Reply from 8.8.8.8: bytes=32 time=15ms TTL=113"
                match = re.search(r'time=(\d+)ms', line)
                if match:
                    times.append(int(match.group(1)))
            
            if times:
                # Calculate jitter as the standard deviation of ping times
                if len(times) >= 2:  # Need at least 2 samples to calculate standard deviation
                    # Method 1: Standard deviation
                    mean_time = sum(times) / len(times)
                    sum_squared_diff = sum((t - mean_time) ** 2 for t in times)
                    jitter = (sum_squared_diff / len(times)) ** 0.5
                    
                    # Method 2: Use the max-min difference as a simpler approximation
                    jitter_alt = (max(times) - min(times)) / 2
                    
                    # Use the smaller of the two methods for a conservative estimate
                    return min(jitter, jitter_alt)
                else:
                    # If we only got one sample, return 0 jitter
                    return 0.0
        
        # If ping failed or no times were found, try to use PowerShell for more detailed analysis
        cmd = f'powershell -Command "Test-Connection -ComputerName {host} -Count {count} -ErrorAction SilentlyContinue | Measure-Object -Property ResponseTime -Average -Maximum -Minimum"'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            # Extract max and min values
            max_match = re.search(r'Maximum\s+:\s+(\d+)', result.stdout)
            min_match = re.search(r'Minimum\s+:\s+(\d+)', result.stdout)
            
            if max_match and min_match:
                max_time = float(max_match.group(1))
                min_time = float(min_match.group(1))
                # Calculate jitter as half the difference between max and min
                return (max_time - min_time) / 2
        
        logger.warning(f"Failed to measure jitter: no valid ping responses")
        return 0.0
    except Exception as e:
        logger.error(f"Error measuring jitter: {e}")
        return 0.0

def measure_windows_packet_loss(host: str = "8.8.8.8", count: int = 10) -> float:
    """
    Measure packet loss percentage on Windows.
    
    Args:
        host: Target host to ping (default: 8.8.8.8)
        count: Number of pings to perform
        
    Returns:
        Packet loss percentage (0-100)
    """
    try:
        # Use ping to measure packet loss
        cmd = f'ping -n {count} {host}'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        # Check for packet loss information in the output
        if result.stdout:
            # Look for the packet loss statistics
            # Format: "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"
            match = re.search(r'Lost = \d+ \((\d+)% loss\)', result.stdout)
            if match:
                loss_percent = float(match.group(1))
                return loss_percent
            
            # Alternative parsing in case the format differs
            sent_match = re.search(r'Sent = (\d+)', result.stdout)
            received_match = re.search(r'Received = (\d+)', result.stdout)
            
            if sent_match and received_match:
                sent = int(sent_match.group(1))
                received = int(received_match.group(1))
                
                if sent > 0:
                    loss_percent = ((sent - received) / sent) * 100
                    return loss_percent
        
        # If the standard approach fails, try PowerShell
        cmd = f'powershell -Command "$pingResult = Test-Connection -ComputerName {host} -Count {count} -ErrorAction SilentlyContinue; $sent = {count}; $received = ($pingResult | Measure-Object).Count; $loss = 100 - ($received / $sent * 100); $loss"'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                return float(result.stdout.strip())
            except ValueError:
                pass
        
        # If all methods fail, check if the host is reachable at all
        result = subprocess.run(f'ping -n 1 -w 1000 {host}', capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            # Host is unreachable
            logger.warning(f"Host {host} is unreachable")
            return 100.0
        
        logger.warning("Failed to calculate packet loss percentage")
        return 0.0
    except Exception as e:
        logger.error(f"Error measuring packet loss: {e}")
        return 0.0

def measure_windows_bandwidth(duration: int = 5) -> Dict[str, float]:
    """
    Measure network bandwidth on Windows.
    
    Args:
        duration: Duration in seconds for the bandwidth test
        
    Returns:
        Dictionary with download and upload speeds in Mbps
    """
    result = {"download": 0.0, "upload": 0.0}
    
    try:
        # Check if speedtest-cli is available via Python
        try:
            import speedtest
            logger.info("Using speedtest-cli to measure bandwidth")
            
            st = speedtest.Speedtest()
            st.get_best_server()
            
            # Measure download speed
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            result["download"] = download_speed
            
            # Measure upload speed
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            result["upload"] = upload_speed
            
            return result
        except (ImportError, Exception) as e:
            logger.warning(f"speedtest-cli not available or failed: {e}")
        
        # Check if speedtest-cli is available as a command-line tool
        try:
            cmd = 'speedtest-cli --simple'
            proc = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=duration + 30)
            
            if proc.returncode == 0:
                # Parse download speed
                download_match = re.search(r'Download: (\d+\.\d+) Mbit/s', proc.stdout)
                if download_match:
                    result["download"] = float(download_match.group(1))
                
                # Parse upload speed
                upload_match = re.search(r'Upload: (\d+\.\d+) Mbit/s', proc.stdout)
                if upload_match:
                    result["upload"] = float(upload_match.group(1))
                
                return result
        except Exception as e:
            logger.warning(f"Command-line speedtest-cli failed: {e}")
        
        # Try using PowerShell and Windows Performance Counters 
        try:
            logger.info("Using network interfaces to estimate bandwidth")
            
            # Get the active interface alias (name)
            interface_cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Select-Object -ExpandProperty Name"'
            interface_result = subprocess.run(interface_cmd, capture_output=True, text=True, shell=True)
            
            if interface_result.returncode == 0 and interface_result.stdout.strip():
                interface_name = interface_result.stdout.strip()
                
                # Get initial byte counts
                initial_cmd = f'powershell -Command "(Get-NetAdapterStatistics -Name \'{interface_name}\').ReceivedBytes, (Get-NetAdapterStatistics -Name \'{interface_name}\').SentBytes"'
                initial_result = subprocess.run(initial_cmd, capture_output=True, text=True, shell=True)
                
                if initial_result.returncode == 0 and initial_result.stdout:
                    # Parse initial values
                    values = initial_result.stdout.strip().split('\n')
                    if len(values) >= 2:
                        try:
                            initial_rx = int(values[0].strip())
                            initial_tx = int(values[1].strip())
                            
                            # Wait for the specified duration
                            time.sleep(duration)
                            
                            # Get final byte counts
                            final_cmd = f'powershell -Command "(Get-NetAdapterStatistics -Name \'{interface_name}\').ReceivedBytes, (Get-NetAdapterStatistics -Name \'{interface_name}\').SentBytes"'
                            final_result = subprocess.run(final_cmd, capture_output=True, text=True, shell=True)
                            
                            if final_result.returncode == 0 and final_result.stdout:
                                # Parse final values
                                values = final_result.stdout.strip().split('\n')
                                if len(values) >= 2:
                                    final_rx = int(values[0].strip())
                                    final_tx = int(values[1].strip())
                                    
                                    # Calculate bits per second (convert to Mbps)
                                    rx_bps = (final_rx - initial_rx) * 8 / duration / 1_000_000
                                    tx_bps = (final_tx - initial_tx) * 8 / duration / 1_000_000
                                    
                                    result["download"] = rx_bps
                                    result["upload"] = tx_bps
                                    
                                    return result
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Error parsing interface statistics: {e}")
        except Exception as e:
            logger.warning(f"Error using interface statistics for bandwidth measurement: {e}")
                
        # If all direct measurements fail, try to get the link speed as an estimate
        try:
            speed_cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Select-Object -ExpandProperty LinkSpeed"'
            speed_result = subprocess.run(speed_cmd, capture_output=True, text=True, shell=True)
            
            if speed_result.returncode == 0 and speed_result.stdout:
                speed_text = speed_result.stdout.strip()
                # Format is typically "1 Gbps" or "100 Mbps"
                if "Gbps" in speed_text:
                    value = float(speed_text.split()[0])
                    # Estimate actual throughput as 70% of link speed for download, 30% for upload
                    result["download"] = value * 1000 * 0.7  # Convert Gbps to Mbps and estimate actual throughput
                    result["upload"] = value * 1000 * 0.3
                elif "Mbps" in speed_text:
                    value = float(speed_text.split()[0])
                    result["download"] = value * 0.7
                    result["upload"] = value * 0.3
                
                return result
        except Exception as e:
            logger.warning(f"Error getting link speed: {e}")
        
        # If everything fails, return conservative estimates
        logger.warning("Could not measure bandwidth accurately, using conservative estimates")
        result["download"] = 10.0  # 10 Mbps
        result["upload"] = 2.0  # 2 Mbps
        return result
    except Exception as e:
        logger.error(f"Error measuring bandwidth: {e}")
        return result

def analyze_windows_network_congestion(interface: Optional[str] = None) -> float:
    """
    Analyze network congestion on Windows.
    
    Args:
        interface: Network interface to analyze (if None, uses the active interface)
        
    Returns:
        Congestion percentage (0-100)
    """
    try:
        congestion_factors = []
        
        # Get the active interface if not specified
        if not interface:
            active_interface_cmd = 'powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq \'Up\'} | Select-Object -ExpandProperty Name"'
            result = subprocess.run(active_interface_cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0 and result.stdout.strip():
                interface = result.stdout.strip()
            else:
                logger.warning("No active interface found for congestion analysis")
                return 30.0  # Default to moderate congestion
        
        # Factor 1: Measure jitter
        jitter = measure_windows_jitter()
        # Normalize jitter to a 0-100 scale (higher means more congestion)
        # 0ms jitter = 0% congestion, 30ms jitter = 100% congestion
        jitter_factor = min(100, jitter * 3.33)
        congestion_factors.append(jitter_factor)
        
        # Factor 2: Measure packet loss
        packet_loss = measure_windows_packet_loss()
        # Packet loss directly contributes to congestion assessment
        congestion_factors.append(packet_loss)
        
        # Factor 3: Check network adapter statistics
        try:
            if interface:
                # Check for discarded packets and errors
                stats_cmd = f'powershell -Command "Get-NetAdapterStatistics -Name \'{interface}\' | Select-Object ReceivedDiscardedPackets, ReceivedPacketErrors, SentDiscardedPackets, SentPacketErrors, ReceivedPackets, SentPackets"'
                stats_result = subprocess.run(stats_cmd, capture_output=True, text=True, shell=True)
                
                if stats_result.returncode == 0 and stats_result.stdout:
                    # Parse the values
                    rx_discarded = re.search(r'ReceivedDiscardedPackets\s+:\s+(\d+)', stats_result.stdout)
                    rx_errors = re.search(r'ReceivedPacketErrors\s+:\s+(\d+)', stats_result.stdout)
                    tx_discarded = re.search(r'SentDiscardedPackets\s+:\s+(\d+)', stats_result.stdout)
                    tx_errors = re.search(r'SentPacketErrors\s+:\s+(\d+)', stats_result.stdout)
                    rx_packets = re.search(r'ReceivedPackets\s+:\s+(\d+)', stats_result.stdout)
                    tx_packets = re.search(r'SentPackets\s+:\s+(\d+)', stats_result.stdout)
                    
                    if all([rx_discarded, rx_errors, tx_discarded, tx_errors, rx_packets, tx_packets]):
                        total_errors = (int(rx_discarded.group(1)) + int(rx_errors.group(1)) + 
                                       int(tx_discarded.group(1)) + int(tx_errors.group(1)))
                        total_packets = int(rx_packets.group(1)) + int(tx_packets.group(1))
                        
                        if total_packets > 0:
                            error_percent = min(100, (total_errors / max(1, total_packets)) * 100)
                            congestion_factors.append(error_percent)
        except Exception as e:
            logger.error(f"Error analyzing interface statistics: {e}")
        
        # Factor 4: Check TCP connection quality
        try:
            # Get TCP connection statistics
            tcp_cmd = 'powershell -Command "Get-NetTCPConnection | Where-Object {$_.State -eq \'Established\'} | Measure-Object | Select-Object -ExpandProperty Count"'
            tcp_result = subprocess.run(tcp_cmd, capture_output=True, text=True, shell=True)
            
            if tcp_result.returncode == 0 and tcp_result.stdout.strip():
                tcp_conn_count = int(tcp_result.stdout.strip())
                
                # More than 100 concurrent TCP connections might indicate congestion
                tcp_factor = min(100, (tcp_conn_count / 100) * 50)  # Scale: 0-50%
                congestion_factors.append(tcp_factor)
        except Exception as e:
            logger.error(f"Error analyzing TCP connections: {e}")
        
        # Factor 5: Check system CPU usage as a proxy for local congestion
        try:
            cpu_cmd = 'powershell -Command "Get-Counter -Counter \'\\Processor(_Total)\\% Processor Time\' | Select-Object -ExpandProperty CounterSamples | Select-Object -ExpandProperty CookedValue"'
            cpu_result = subprocess.run(cpu_cmd, capture_output=True, text=True, shell=True)
            
            if cpu_result.returncode == 0 and cpu_result.stdout.strip():
                cpu_usage = float(cpu_result.stdout.strip())
                
                # High CPU usage could affect network performance
                # CPU usage over 70% starts to contribute to congestion assessment
                if cpu_usage > 70:
                    cpu_factor = (cpu_usage - 70) * 3.33  # Scale: 0-100% for CPU usage 70-100%
                    congestion_factors.append(cpu_factor * 0.5)  # Lower weight for CPU
        except Exception as e:
            logger.error(f"Error checking system CPU usage: {e}")
        
        # Calculate overall congestion percentage
        if congestion_factors:
            return sum(congestion_factors) / len(congestion_factors)
        
        return 30.0  # Default to moderate congestion
    except Exception as e:
        logger.error(f"Error analyzing network congestion: {e}")
        return 30.0  # Default to moderate congestion

def clear_windows_network_buffers() -> bool:
    """
    Clear network buffers on Windows to reset connection state.
    
    Returns:
        True if successful, False otherwise
    """
    if not is_admin():
        logger.error("Administrator privileges required to clear network buffers")
        return False
    
    try:
        # Flush DNS cache
        dns_cmd = 'ipconfig /flushdns'
        dns_result = subprocess.run(dns_cmd, capture_output=True, text=True, shell=True)
        
        if dns_result.returncode != 0:
            logger.warning(f"DNS cache flush failed: {dns_result.stderr}")
        
        # Reset Winsock catalog
        winsock_cmd = 'netsh winsock reset'
        winsock_result = subprocess.run(winsock_cmd, capture_output=True, text=True, shell=True)
        
        if winsock_result.returncode != 0:
            logger.warning(f"Winsock reset failed: {winsock_result.stderr}")
            
        # Reset TCP/IP stack
        ip_cmd = 'netsh int ip reset'
        ip_result = subprocess.run(ip_cmd, capture_output=True, text=True, shell=True)
        
        if ip_result.returncode != 0:
            logger.warning(f"TCP/IP reset failed: {ip_result.stderr}")
        
        # Clear NetBIOS cache
        nbtstat_cmd = 'nbtstat -R'
        nbtstat_result = subprocess.run(nbtstat_cmd, capture_output=True, text=True, shell=True)
        
        # Reset network interfaces
        interface_cmd = 'ipconfig /release && ipconfig /renew'
        interface_result = subprocess.run(interface_cmd, capture_output=True, text=True, shell=True)
        
        # Note: Some of these commands may require a system restart to take full effect
        logger.info("Successfully cleared network buffers (some changes may require a system restart)")
        return True
    except Exception as e:
        logger.error(f"Error clearing network buffers: {e}")
        return False

def set_windows_qos_priority(application: str, priority: str = 'high') -> bool:
    """
    Set QoS priority for specific applications on Windows.
    
    Args:
        application: Path to the application executable
        priority: Priority level ('high', 'medium', 'low')
        
    Returns:
        True if successful, False otherwise
    """
    if not is_admin():
        logger.error("Administrator privileges required to set QoS priorities")
        return False
    
    try:
        # Convert priority to QoS DSCP values
        prio_map = {
            'high': 46,     # Expedited Forwarding
            'medium': 26,   # Assured Forwarding 31
            'low': 8        # Class Selector 1
        }
        
        if priority not in prio_map:
            logger.error(f"Invalid priority: {priority}")
            return False
        
        dscp_value = prio_map[priority]
        
        # Get the filename from the path
        app_name = os.path.basename(application)
        
        # Configure QoS policy using Group Policy
        # First, check if the policy exists
        check_cmd = f'powershell -Command "Get-NetQosPolicy -Name \'{app_name}\' -ErrorAction SilentlyContinue"'
        check_result = subprocess.run(check_cmd, capture_output=True, text=True, shell=True)
        
        if "No MSFT_NetQosPolicy objects found" in check_result.stdout or check_result.returncode != 0:
            # Create a new policy
            create_cmd = f'powershell -Command "New-NetQosPolicy -Name \'{app_name}\' -AppPathNameMatchCondition \'{application}\' -DSCPAction {dscp_value} -IPProtocol Both"'
            create_result = subprocess.run(create_cmd, capture_output=True, text=True, shell=True)
            
            if create_result.returncode != 0:
                logger.error(f"Failed to create QoS policy: {create_result.stderr}")
                return False
        else:
            # Update existing policy
            update_cmd = f'powershell -Command "Set-NetQosPolicy -Name \'{app_name}\' -DSCPAction {dscp_value}"'
            update_result = subprocess.run(update_cmd, capture_output=True, text=True, shell=True)
            
            if update_result.returncode != 0:
                logger.error(f"Failed to update QoS policy: {update_result.stderr}")
                return False
        
        logger.info(f"Successfully set QoS priority for {app_name} to {priority}")
        return True
    except Exception as e:
        logger.error(f"Error setting QoS priority: {e}")
        return False

def get_windows_network_interfaces() -> List[Dict[str, Any]]:
    """
    Get detailed information about network interfaces on Windows.
    
    Returns:
        List of dictionaries containing interface details
    """
    interfaces = []
    
    try:
        # Use PowerShell to get network adapter information
        cmd = 'powershell -Command "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress, LinkSpeed | ConvertTo-Json"'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0 and result.stdout:
            try:
                # Parse JSON output
                import json
                
                # Check if we got a single object or an array
                if result.stdout.strip().startswith('{'):
                    # Single object
                    adapter_data = [json.loads(result.stdout)]
                else:
                    # Array of objects
                    adapter_data = json.loads(result.stdout)
                
                for adapter in adapter_data:
                    # Basic interface information
                    interface_info = {
                        'name': adapter.get('Name', ''),
                        'description': adapter.get('InterfaceDescription', ''),
                        'status': adapter.get('Status', ''),
                        'mac': adapter.get('MacAddress', ''),
                        'speed': adapter.get('LinkSpeed', ''),
                        'ipv4': [],
                        'ipv6': []
                    }
                    
                    # Get IP addresses for this adapter
                    ip_cmd = f'powershell -Command "Get-NetIPAddress -InterfaceAlias \'{interface_info["name"]}\' | Select-Object IPAddress, PrefixLength, AddressFamily | ConvertTo-Json"'
                    ip_result = subprocess.run(ip_cmd, capture_output=True, text=True, shell=True)
                    
                    if ip_result.returncode == 0 and ip_result.stdout:
                        try:
                            # Check if we got a single object or an array
                            if ip_result.stdout.strip().startswith('{'):
                                # Single object
                                ip_data = [json.loads(ip_result.stdout)]
                            else:
                                # Array of objects
                                ip_data = json.loads(ip_result.stdout)
                            
                            for ip in ip_data:
                                address_family = ip.get('AddressFamily', 0)
                                if address_family == 2:  # IPv4
                                    interface_info['ipv4'].append({
                                        'address': ip.get('IPAddress', ''),
                                        'prefix': ip.get('PrefixLength', 0)
                                    })
                                elif address_family == 23:  # IPv6
                                    interface_info['ipv6'].append({
                                        'address': ip.get('IPAddress', ''),
                                        'prefix': ip.get('PrefixLength', 0)
                                    })
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse IP information JSON for {interface_info['name']}")
                    
                    interfaces.append(interface_info)
            
            except json.JSONDecodeError:
                logger.warning("Failed to parse adapter information JSON")
        
        # If PowerShell with JSON fails, fallback to standard command parsing
        if not interfaces:
            # Use ipconfig for a more compatible approach
            cmd = 'ipconfig /all'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                sections = result.stdout.split('\r\n\r\n')
                current_section = None
                
                for section in sections:
                    if not section.strip():
                        continue
                    
                    lines = section.splitlines()
                    if lines and "adapter" in lines[0].lower():
                        # New adapter section
                        adapter_name = lines[0].split(':')[0].split('adapter')[1].strip()
                        
                        interface_info = {
                            'name': adapter_name,
                            'description': '',
                            'status': 'Unknown',
                            'mac': '',
                            'speed': '',
                            'ipv4': [],
                            'ipv6': []
                        }
                        
                        for line in lines[1:]:
                            line = line.strip()
                            if "Description" in line:
                                interface_info['description'] = line.split(':')[1].strip()
                            elif "Physical Address" in line:
                                interface_info['mac'] = line.split(':')[1].strip()
                            elif "Media State" in line:
                                state = line.split(':')[1].strip()
                                interface_info['status'] = 'Up' if 'connected' in state.lower() else 'Down'
                            elif "IPv4 Address" in line:
                                ipv4 = line.split(':')[1].strip().split('(')[0].strip()
                                interface_info['ipv4'].append({
                                    'address': ipv4,
                                    'prefix': 24  # Assume /24 if not specified
                                })
                            elif "Subnet Mask" in line and interface_info['ipv4']:
                                mask = line.split(':')[1].strip()
                                # Convert subnet mask to prefix length (approximate)
                                prefix = sum([bin(int(x)).count('1') for x in mask.split('.')])
                                interface_info['ipv4'][-1]['prefix'] = prefix
                            elif "IPv6 Address" in line:
                                ipv6 = line.split(':')[1].strip().split('(')[0].strip()
                                interface_info['ipv6'].append({
                                    'address': ipv6,
                                    'prefix': 64  # Assume /64 if not specified
                                })
                        
                        interfaces.append(interface_info)
    
    except Exception as e:
        logger.error(f"Error getting network interfaces: {e}")
    
    return interfaces

def import_time_module():
    """
    Import the time module for use by other functions.
    This is separated to avoid import issues when the module is first loaded.
    """
    global time
    import time
    return time

# Import time module for bandwidth measurements
time = import_time_module() 