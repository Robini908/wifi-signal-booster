"""
Network diagnostics utilities for Signal Booster.
This module provides functions for diagnosing network issues.
"""

import json
from signal_booster.network.common import *
from signal_booster.network.interfaces import get_network_interfaces

def check_for_malware() -> Tuple[bool, List[str]]:
    """
    Check for malware that might be affecting network performance.
    
    Returns:
        Tuple of (issues_found, list_of_issues)
    """
    issues = []
    try:
        # Check for suspicious processes
        for proc in psutil.process_iter(['pid', 'name', 'username', 'connections']):
            process_info = proc.info
            
            # Check process name against a list of known suspicious names
            suspicious_names = ['malware', 'trojan', 'keylog', 'spyware', 'adware']
            if any(bad_name in process_info['name'].lower() for bad_name in suspicious_names):
                issues.append(f"Suspicious process found: {process_info['name']} (PID: {process_info['pid']})")
                
            # Check for processes with unusual network connections
            if 'connections' in process_info and process_info['connections']:
                for conn in process_info['connections']:
                    if conn.status == 'ESTABLISHED':
                        # Check if connection is to a suspicious port
                        suspicious_ports = [6667, 1080, 31337, 12345, 6666]
                        if conn.rport in suspicious_ports:
                            issues.append(f"Process {process_info['name']} (PID: {process_info['pid']}) has a connection to suspicious port {conn.rport}")
        
        # Check for unusual DNS settings that might indicate malware
        try:
            if platform.system() == "Windows":
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters', 0, winreg.KEY_READ) as key:
                    try:
                        nameserver, _ = winreg.QueryValueEx(key, "NameServer")
                        # Check against known malicious DNS servers
                        # This would need a proper list of malicious IPs
                        if nameserver:
                            if nameserver not in ["8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9"]:
                                issues.append(f"Unusual DNS server configured: {nameserver}")
                    except FileNotFoundError:
                        pass
            elif platform.system() == "Linux":
                # Check /etc/resolv.conf
                if os.path.exists("/etc/resolv.conf"):
                    with open("/etc/resolv.conf", "r") as f:
                        for line in f:
                            if line.startswith("nameserver"):
                                nameserver = line.split()[1]
                                # Check against known malicious DNS servers
                                if nameserver not in ["8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9"]:
                                    issues.append(f"Unusual DNS server configured: {nameserver}")
        except Exception as e:
            logger.warning(f"Could not check DNS settings: {e}")
            
        # Check for hosts file modifications (common malware target)
        try:
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
            if os.path.exists(hosts_path):
                with open(hosts_path, "r") as f:
                    hosts_content = f.read()
                    # Check for excessive entries or unusual redirects
                    lines = hosts_content.strip().split("\n")
                    non_comment_lines = [line for line in lines if line.strip() and not line.strip().startswith("#")]
                    
                    if len(non_comment_lines) > 20:  # Arbitrary threshold
                        issues.append(f"Hosts file contains an unusually high number of entries ({len(non_comment_lines)})")
                    
                    # Check for suspicious redirects
                    suspicious_domains = ["google", "facebook", "microsoft", "apple", "amazon", "bank"]
                    for line in non_comment_lines:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            ip = parts[0]
                            domain = parts[1].lower()
                            
                            # Check if common domains are redirected to suspicious IPs
                            if any(susp in domain for susp in suspicious_domains) and ip != "127.0.0.1":
                                issues.append(f"Suspicious redirect in hosts file: {domain} -> {ip}")
        except Exception as e:
            logger.warning(f"Could not check hosts file: {e}")
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
        if platform.system() == "Windows":
            # Use PowerShell to get network adapter driver information
            stdout, stderr, returncode = run_command([
                "powershell", 
                "-Command", 
                "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, DriverVersion | ConvertTo-Json"
            ])
            
            if stdout:
                # Parse the output
                try:
                    adapters = json.loads(stdout)
                    
                    # Ensure we have a list
                    if not isinstance(adapters, list):
                        adapters = [adapters]
                    
                    # Extract and check driver versions
                    for adapter in adapters:
                        name = adapter.get('Name', '')
                        desc = adapter.get('InterfaceDescription', '')
                        driver_version = adapter.get('DriverVersion', '')
                        
                        # Check driver version against known requirements
                        # In a real app, you'd compare against a database of driver versions
                        version_parts = driver_version.split('.')
                        if len(version_parts) >= 2:
                            # Very simple heuristic: major version < 10 could be outdated
                            try:
                                if int(version_parts[0]) < 10:
                                    outdated.append(f"{desc} - Driver version {driver_version} may be outdated")
                            except ValueError:
                                pass
                except json.JSONDecodeError:
                    logger.error("Could not parse adapter information")
            
            # Check for problematic devices
            stdout, stderr, returncode = run_command([
                "powershell", 
                "-Command", 
                "Get-NetAdapter | Where-Object {$_.Status -eq 'Disabled' -or $_.Status -eq 'NotPresent'} | Select-Object Name, InterfaceDescription | ConvertTo-Json"
            ])
            
            if stdout:
                try:
                    disabled_adapters = json.loads(stdout)
                    if not isinstance(disabled_adapters, list):
                        disabled_adapters = [disabled_adapters]
                    
                    for adapter in disabled_adapters:
                        desc = adapter.get('InterfaceDescription', '')
                        if desc:
                            outdated.append(f"{desc} - Network adapter is disabled or has driver issues")
                except json.JSONDecodeError:
                    pass
        
        elif platform.system() == "Linux":
            # Check for outdated network drivers on Linux
            # Get loaded network modules
            stdout, stderr, returncode = run_command(["lsmod"])
            
            if stdout:
                # Common network driver module prefixes
                network_modules = ["e1000", "r8169", "ath", "iwl", "rtl", "wl", "bcma", "bnx2", "tg3"]
                
                # Find network modules
                loaded_modules = []
                for line in stdout.split('\n')[1:]:  # Skip header
                    if not line.strip():
                        continue
                    parts = line.split()
                    if parts:
                        module_name = parts[0]
                        if any(module_name.startswith(prefix) for prefix in network_modules):
                            loaded_modules.append(module_name)
                
                # Check each module's version
                for module in loaded_modules:
                    # Get module info
                    stdout, stderr, returncode = run_command(["modinfo", module])
                    
                    if stdout:
                        # Extract version
                        version = None
                        for line in stdout.split('\n'):
                            if line.startswith("version:"):
                                version = line.split(":", 1)[1].strip()
                                break
                        
                        if version:
                            # Simple check for potentially outdated modules
                            if version.startswith("1.") or version.startswith("2."):
                                outdated.append(f"{module} - Driver version {version} might be outdated")
                
                # Also check dmesg for driver warnings
                stdout, stderr, returncode = run_command(["dmesg"])
                if stdout:
                    for line in stdout.split('\n'):
                        if any(warning in line.lower() for warning in ["firmware", "outdated", "deprecated"]) and \
                        any(net in line.lower() for net in ["eth", "wlan", "wifi"]):
                            outdated.append(f"Potential driver issue detected: {line}")
        
        elif platform.system() == "Darwin":  # macOS
            # For macOS, check system profiler information
            stdout, stderr, returncode = run_command(["system_profiler", "SPNetworkDataType"])
            
            if stdout:
                # Parse output to find interface types
                interfaces = []
                current_interface = None
                
                for line in stdout.split('\n'):
                    if ":" in line and not line.startswith(" "):
                        current_interface = line.strip().rstrip(":")
                    elif current_interface and line.strip().startswith("Type:"):
                        interface_type = line.split(":", 1)[1].strip()
                        
                        # Check for older WiFi standards
                        if "802.11" in interface_type:
                            if not any(standard in interface_type for standard in ["ac", "ax"]):
                                outdated.append(f"{current_interface} - Using older WiFi standard ({interface_type})")
                
                # Check macOS version for driver updates
                stdout, stderr, returncode = run_command(["sw_vers", "-productVersion"])
                if stdout:
                    os_version = stdout.strip()
                    version_parts = [int(x) for x in os_version.split(".")]
                    
                    if version_parts[0] < 10 or (version_parts[0] == 10 and version_parts[1] < 15):
                        outdated.append(f"macOS {os_version} - Consider updating for latest network drivers")
    except Exception as e:
        logger.error(f"Error checking network drivers: {e}")
    
    return len(outdated) == 0, outdated


def check_connection_quality(target: str = "8.8.8.8", count: int = 10) -> Dict[str, Any]:
    """
    Analyze connection quality by measuring jitter, packet loss, and latency.
    
    Args:
        target: Host to test against
        count: Number of pings to perform
        
    Returns:
        Dict with jitter, packet_loss, and latency metrics
    """
    result = {
        "min_latency": 0.0,
        "max_latency": 0.0,
        "avg_latency": 0.0,
        "jitter": 0.0,
        "packet_loss": 0.0,
        "quality_score": 0,  # 0-100 score, higher is better
        "quality_issues": []
    }
    
    try:
        # Perform ping test
        if platform.system() == "Windows":
            stdout, stderr, returncode = run_command(["ping", "-n", str(count), target])
            
            if stdout:
                # Parse packet loss
                loss_match = re.search(r"(\d+)% loss", stdout)
                if loss_match:
                    result["packet_loss"] = float(loss_match.group(1))
                
                # Parse latency stats
                latency_match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", stdout)
                if latency_match:
                    result["min_latency"] = float(latency_match.group(1))
                    result["max_latency"] = float(latency_match.group(2))
                    result["avg_latency"] = float(latency_match.group(3))
                    
                    # Calculate jitter (standard deviation of latency)
                    # Simple approximation: (max - min) / 2
                    result["jitter"] = (result["max_latency"] - result["min_latency"]) / 2
        else:  # Linux/macOS
            stdout, stderr, returncode = run_command(["ping", "-c", str(count), target])
            
            if stdout:
                # Parse packet loss
                loss_match = re.search(r"(\d+\.?\d*)% packet loss", stdout)
                if loss_match:
                    result["packet_loss"] = float(loss_match.group(1))
                
                # Parse latency stats
                latency_match = re.search(r"min/avg/max/mdev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)", stdout)
                if latency_match:
                    result["min_latency"] = float(latency_match.group(1))
                    result["avg_latency"] = float(latency_match.group(2))
                    result["max_latency"] = float(latency_match.group(3))
                    # mdev is the mean deviation, which is a good approximation of jitter
                    result["jitter"] = float(latency_match.group(4))
        
        # Calculate connection quality score (0-100)
        # Factors: latency, jitter, packet loss
        
        # Latency score (lower is better): 40 points
        # < 20ms: 40 points, > 200ms: 0 points, linear in between
        latency_score = max(0, 40 - (result["avg_latency"] / 5))
        
        # Jitter score (lower is better): 30 points
        # < 5ms: 30 points, > 50ms: 0 points, linear in between
        jitter_score = max(0, 30 - (result["jitter"] * 0.6))
        
        # Packet loss score (lower is better): 30 points
        # 0%: 30 points, 10% or higher: 0 points, linear in between
        packet_loss_score = max(0, 30 - (result["packet_loss"] * 3))
        
        # Overall quality score
        result["quality_score"] = round(latency_score + jitter_score + packet_loss_score)
        
        # Identify quality issues
        if result["avg_latency"] > 100:
            result["quality_issues"].append("High latency")
        if result["jitter"] > 20:
            result["quality_issues"].append("High jitter/instability")
        if result["packet_loss"] > 1:
            result["quality_issues"].append("Packet loss detected")
        
        # Add quality rating
        if result["quality_score"] >= 90:
            result["quality_rating"] = "Excellent"
        elif result["quality_score"] >= 70:
            result["quality_rating"] = "Good"
        elif result["quality_score"] >= 50:
            result["quality_rating"] = "Fair"
        elif result["quality_score"] >= 30:
            result["quality_rating"] = "Poor"
        else:
            result["quality_rating"] = "Very Poor"
        
    except Exception as e:
        logger.error(f"Error checking connection quality: {e}")
        result["quality_issues"].append(f"Error analyzing connection: {str(e)}")
    
    return result


def detect_interference_sources() -> List[Dict[str, Any]]:
    """
    Detect potential sources of network interference.
    
    Returns:
        List of potential interference sources and their details
    """
    interference_sources = []
    
    try:
        # Check for nearby WiFi networks (if interface is wireless)
        if platform.system() == "Windows":
            stdout, stderr, returncode = run_command(["netsh", "wlan", "show", "networks", "mode=Bssid"])
            
            if stdout:
                # Parse the output to find networks and their signal strength
                networks = []
                current_network = None
                
                for line in stdout.split('\n'):
                    if "SSID" in line and ":" in line and not "BSSID" in line:
                        name = line.split(':', 1)[1].strip()
                        if name:
                            current_network = {
                                "name": name,
                                "signal": 0,
                                "channel": 0
                            }
                            networks.append(current_network)
                    elif current_network and "Signal" in line and ":" in line:
                        signal_str = line.split(':', 1)[1].strip().replace('%', '')
                        try:
                            current_network["signal"] = int(signal_str)
                        except ValueError:
                            pass
                    elif current_network and "Channel" in line and ":" in line:
                        channel_str = line.split(':', 1)[1].strip()
                        try:
                            current_network["channel"] = int(channel_str)
                        except ValueError:
                            pass
                
                # Analyze networks for potential interference
                # Group networks by channel
                channels = {}
                for network in networks:
                    channel = network["channel"]
                    if channel not in channels:
                        channels[channel] = []
                    channels[channel].append(network)
                
                # Check for channel congestion
                for channel, nets in channels.items():
                    if len(nets) >= 3:  # Arbitrary threshold, adjust as needed
                        interference_sources.append({
                            "type": "wifi_congestion",
                            "channel": channel,
                            "networks": len(nets),
                            "description": f"WiFi channel {channel} is congested with {len(nets)} networks"
                        })
                
                # Check for strong overlapping networks
                # In 2.4GHz, channels 1, 6, and 11 are the non-overlapping channels
                overlapping_channels = {
                    1: [2, 3, 4, 5],
                    2: [1, 3, 4, 5, 6],
                    3: [1, 2, 4, 5, 6, 7],
                    4: [1, 2, 3, 5, 6, 7, 8],
                    5: [1, 2, 3, 4, 6, 7, 8, 9],
                    6: [2, 3, 4, 5, 7, 8, 9, 10],
                    7: [3, 4, 5, 6, 8, 9, 10, 11],
                    8: [4, 5, 6, 7, 9, 10, 11],
                    9: [5, 6, 7, 8, 10, 11],
                    10: [6, 7, 8, 9, 11],
                    11: [7, 8, 9, 10]
                }
                
                for channel, overlaps in overlapping_channels.items():
                    if channel in channels:
                        for overlap_ch in overlaps:
                            if overlap_ch in channels:
                                strong_networks = [n for n in channels[overlap_ch] if n["signal"] > 70]
                                if strong_networks:
                                    interference_sources.append({
                                        "type": "channel_overlap",
                                        "channel": channel,
                                        "overlapping_channel": overlap_ch,
                                        "strong_networks": len(strong_networks),
                                        "description": f"Channel {channel} has overlap with {len(strong_networks)} strong networks on channel {overlap_ch}"
                                    })
        
        elif platform.system() == "Linux":
            stdout, stderr, returncode = run_command(["iwlist", "scanning"])
            
            # Similar parsing and analysis as Windows, but for Linux iwlist output
            
        elif platform.system() == "Darwin":  # macOS
            airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
            if os.path.exists(airport_path):
                stdout, stderr, returncode = run_command([airport_path, "-s"])
                
                # Similar parsing and analysis as Windows, but for macOS airport output
        
        # Check for USB 3.0 devices that might cause interference
        try:
            usb_devices = []
            
            if platform.system() == "Windows":
                stdout, stderr, returncode = run_command([
                    "powershell",
                    "-Command",
                    "Get-PnpDevice -Class USB | Where-Object { $_.Status -eq 'OK' } | Select-Object FriendlyName | ConvertTo-Json"
                ])
                
                if stdout:
                    try:
                        devices = json.loads(stdout)
                        if not isinstance(devices, list):
                            devices = [devices]
                        
                        usb_devices = [d.get('FriendlyName', '') for d in devices if d.get('FriendlyName')]
                    except json.JSONDecodeError:
                        pass
            
            # Check for USB 3.0 devices (keywords)
            usb3_keywords = ["USB 3.0", "SuperSpeed", "SuperSpd", "SS USB"]
            usb3_devices = [dev for dev in usb_devices if any(keyword in dev for keyword in usb3_keywords)]
            
            if usb3_devices and any("wireless" in dev.lower() or "wifi" in dev.lower() for dev in usb_devices):
                interference_sources.append({
                    "type": "usb3_interference",
                    "usb3_devices": len(usb3_devices),
                    "description": f"USB 3.0 devices ({len(usb3_devices)}) may interfere with 2.4GHz wireless devices"
                })
        except Exception as e:
            logger.warning(f"Could not check USB devices: {e}")
        
        # Check for microwave ovens and other potential interference sources
        # This is more speculative and would require more sophisticated analysis
        # For now, we'll just include some general checks
        
        # Check for intermittent latency spikes (could indicate physical interference)
        try:
            stdout, stderr, returncode = run_command(["ping", "-n" if platform.system() == "Windows" else "-c", "20", "8.8.8.8"])
            
            if stdout:
                # Parse ping times
                times = []
                ping_pattern = r"time=(\d+\.?\d*)" if platform.system() != "Windows" else r"time[<=](\d+)"
                
                for match in re.finditer(ping_pattern, stdout):
                    try:
                        times.append(float(match.group(1)))
                    except ValueError:
                        pass
                
                if times:
                    # Check for large variations/spikes
                    avg_time = sum(times) / len(times)
                    max_time = max(times)
                    
                    if max_time > avg_time * 3 and max_time > 100:
                        interference_sources.append({
                            "type": "intermittent_interference",
                            "max_latency": max_time,
                            "avg_latency": avg_time,
                            "description": "Intermittent latency spikes detected, may indicate physical interference (microwave, cordless phone, etc.)"
                        })
        except Exception as e:
            logger.warning(f"Could not check for latency spikes: {e}")
    
    except Exception as e:
        logger.error(f"Error detecting interference sources: {e}")
    
    return interference_sources 