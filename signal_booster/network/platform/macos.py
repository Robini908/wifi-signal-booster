"""
macOS-specific network utilities for Signal Booster.
"""

import os
import re
import subprocess
from typing import List, Dict, Tuple, Optional, Any

from signal_booster.network.common import logger, run_command

def set_macos_dns(dns_servers: List[str], interface: Optional[str] = None) -> bool:
    """Set DNS servers on macOS."""
    try:
        # Get network service name if interface is not provided
        network_service = None
        
        if interface:
            # Try to find the network service associated with this interface
            stdout, stderr, returncode = run_command(["networksetup", "-listallhardwareports"])
            
            if stdout:
                # Parse the output to find the service name for this interface
                current_service = None
                for line in stdout.split('\n'):
                    if "Hardware Port:" in line:
                        current_service = line.split(":", 1)[1].strip()
                    elif "Device:" in line and interface in line:
                        network_service = current_service
                        break
        
        if not network_service:
            # Get active network service
            stdout, stderr, returncode = run_command(["networksetup", "-listallnetworkservices"])
            
            if stdout:
                # Skip the first line (header)
                services = stdout.strip().split('\n')[1:]
                
                # Find active Wi-Fi or Ethernet service
                for service in services:
                    if any(keyword in service.lower() for keyword in ["wi-fi", "airport", "ethernet"]):
                        network_service = service
                        break
                    
        if not network_service:
            logger.error("No active network service found for DNS configuration")
            return False
            
        # Set DNS servers using networksetup
        stdout, stderr, returncode = run_command(
            ["networksetup", "-setdnsservers", network_service] + dns_servers,
            check=True
        )
        
        if returncode != 0:
            logger.error(f"Failed to set DNS servers: {stderr}")
            return False
        
        # Flush DNS cache
        run_command(["dscacheutil", "-flushcache"], check=False)
        
        # Also kill mDNSResponder to ensure cache is cleared
        try:
            run_command(["killall", "-HUP", "mDNSResponder"], check=False)
        except Exception:
            pass
            
        logger.info(f"Successfully set DNS servers on macOS to {dns_servers}")
        return True
    except Exception as e:
        logger.error(f"Error setting DNS servers on macOS: {e}")
        return False


def get_macos_wifi_signal() -> int:
    """Get WiFi signal strength on macOS."""
    try:
        # Use airport command to get signal strength
        airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if os.path.exists(airport_path):
            stdout, stderr, returncode = run_command([airport_path, "-I"])
            
            if stdout:
                # Parse the output to find signal strength (agrCtlRSSI)
                for line in stdout.split("\n"):
                    if "agrCtlRSSI" in line and ":" in line:
                        rssi = int(line.split(":")[1].strip())
                        # Convert RSSI to percentage
                        # Typical values: -50 dBm (excellent) to -100 dBm (very poor)
                        signal_percent = max(0, min(100, 2 * (rssi + 100)))
                        return signal_percent
                    
        # Alternative method using system_profiler
        stdout, stderr, returncode = run_command(["system_profiler", "SPAirPortDataType"])
        
        if stdout:
            # Look for signal/noise ratio
            snr_match = re.search(r"Signal / Noise:\s+(\d+)", stdout)
            if snr_match:
                snr = int(snr_match.group(1))
                # Convert SNR to approximate percentage
                # SNR of 40+ is excellent (100%), 10 or below is poor (0%)
                signal_percent = min(100, max(0, snr * 2.5))
                return signal_percent
    
    except Exception as e:
        logger.error(f"Error getting macOS WiFi signal strength: {e}")
    
    # If all methods failed, return a reasonable default
    return 60


def find_macos_best_channel() -> int:
    """Find best WiFi channel on macOS."""
    try:
        # Use airport command to scan for networks
        airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        if os.path.exists(airport_path):
            stdout, stderr, returncode = run_command([airport_path, "-s"])
            
            if stdout:
                # Parse output to identify channels and their usage
                channel_usage = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0}
                
                # Split the output into lines, skip the header
                lines = stdout.strip().split('\n')
                if len(lines) > 1:
                    lines = lines[1:]  # Skip header
                    
                    for line in lines:
                        # Channel info is typically in column 4
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                channel = int(parts[3])
                                if 1 <= channel <= 11:  # Only consider standard 2.4GHz channels
                                    channel_usage[channel] += 1
                                    
                                    # Also count this network as affecting adjacent channels (RF overlap)
                                    for adj_ch in range(max(1, channel - 2), min(11, channel + 2) + 1):
                                        if adj_ch != channel:
                                            channel_usage[adj_ch] += 0.5  # Lower weight for adjacent channels
                            except (ValueError, IndexError):
                                pass
                
                # Find channels with lowest usage
                min_usage = float('inf')
                best_channels = []
                
                for channel, usage in channel_usage.items():
                    if usage < min_usage:
                        min_usage = usage
                        best_channels = [channel]
                    elif usage == min_usage:
                        best_channels.append(channel)
                
                # If there are multiple best channels, prefer 1, 6, or 11 (standard non-overlapping channels)
                preferred = [ch for ch in best_channels if ch in (1, 6, 11)]
                if preferred:
                    return preferred[0]
                
                # Otherwise return the first best channel
                return best_channels[0] if best_channels else 6
        
        # Try alternative method if airport command is not available
        stdout, stderr, returncode = run_command(["system_profiler", "SPAirPortDataType"])
        
        if stdout:
            # Look for preferred channels
            preferred_match = re.search(r"Preferred Channels:\s*(.+)", stdout)
            if preferred_match:
                channels_str = preferred_match.group(1).strip()
                # Parse the channels
                channels = [int(ch.strip()) for ch in channels_str.split(',') if ch.strip().isdigit()]
                if channels:
                    # Return the first preferred channel that is 1, 6, or 11 if possible
                    for ch in channels:
                        if ch in (1, 6, 11):
                            return ch
                    # Otherwise just return the first preferred channel
                    return channels[0]
    
    except Exception as e:
        logger.error(f"Error finding best WiFi channel on macOS: {e}")
    
    # Default to channel 6 if we couldn't determine the best channel
    return 6 