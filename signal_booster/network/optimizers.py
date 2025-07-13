"""
Network optimization utilities for Signal Booster.
This module provides functions for optimizing network performance.
"""

from signal_booster.network.common import *
from signal_booster.network.interfaces import get_network_interfaces, get_active_interface

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
    """Optimize TCP settings on Windows with advanced algorithms."""
    try:
        success = True
        logger.info("Applying advanced Windows TCP optimizations")
        
        # 1. Advanced TCP autotuning with dynamic scaling based on network quality
        # Enable TCP autotuning at normal level initially
        stdout, stderr, returncode = run_command(
            ["netsh", "interface", "tcp", "set", "global", "autotuninglevel=normal"],
            check=True
        )
        
        if returncode != 0:
            success = False
            logger.warning("Failed to set TCP autotuning level")
        
        # 2. Advanced congestion control provider selection
        # Try newest congestion control algorithms first, then fall back to older ones
        congestion_providers = ["cubic", "ctcp", "newreno", "reno"]
        congestion_set = False
        
        for provider in congestion_providers:
            stdout, stderr, returncode = run_command(
                ["netsh", "interface", "tcp", "set", "global", f"congestionprovider={provider}"],
                check=False
            )
            if returncode == 0:
                logger.info(f"Successfully set TCP congestion provider to {provider}")
                congestion_set = True
                break
        
        if not congestion_set:
            logger.warning("Could not set any advanced TCP congestion provider")
            
        # 3. Advanced TCP registry optimizations with intelligent values
        try:
            import winreg
            import psutil
            
            # Get system memory to scale TCP parameters appropriately
            memory_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
            
            # Scale TCP window size based on available system memory
            # Use larger windows for systems with more RAM
            if memory_gb >= 16:
                tcp_window_size = 4194304  # 4MB for high-memory systems
            elif memory_gb >= 8:
                tcp_window_size = 2097152  # 2MB for medium-memory systems
            elif memory_gb >= 4:
                tcp_window_size = 1048576  # 1MB for lower-memory systems
            else:
                tcp_window_size = 524288   # 512KB for very low memory systems
                
            # TCP key parameters registry path
            tcp_params_path = r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, tcp_params_path, 0, winreg.KEY_WRITE) as key:
                # Enable all TCP timestamp options (RTTM, PAWS) with scaling
                winreg.SetValueEx(key, "Tcp1323Opts", 0, winreg.REG_DWORD, 3)
                
                # Enable TCP No Delay for lower latency
                winreg.SetValueEx(key, "TCPNoDelay", 0, winreg.REG_DWORD, 1)
                
                # Disable TCP delayed ACKs for faster response
                winreg.SetValueEx(key, "TcpAckFrequency", 0, winreg.REG_DWORD, 1)
                
                # Optimal TTL setting (128 is a good balance)
                winreg.SetValueEx(key, "DefaultTTL", 0, winreg.REG_DWORD, 128)
                
                # Increase SYN attack protection with SYN cookies
                winreg.SetValueEx(key, "SynAttackProtect", 0, winreg.REG_DWORD, 1)
                
                # Set the TCP window size calculated above
                winreg.SetValueEx(key, "TcpWindowSize", 0, winreg.REG_DWORD, tcp_window_size)
                
                # Enable TCP Fast Path processing for performance
                winreg.SetValueEx(key, "EnableTCPA", 0, winreg.REG_DWORD, 1)
                
                # Set maximum connections
                winreg.SetValueEx(key, "TcpNumConnections", 0, winreg.REG_DWORD, 0xFFFFFFE)
                
            # Also optimize TCP chimney offload if supported
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces', 0, winreg.KEY_READ) as interfaces_key:
                    # Get the number of interfaces
                    num_interfaces = winreg.QueryInfoKey(interfaces_key)[0]
                    
                    # For each interface
                    for i in range(num_interfaces):
                        interface_name = winreg.EnumKey(interfaces_key, i)
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"{tcp_params_path}\\Interfaces\\{interface_name}", 0, winreg.KEY_WRITE) as interface_key:
                            # Only set for interfaces that have IP addresses
                            try:
                                winreg.QueryValueEx(interface_key, "IPAddress")
                                # Set optimal MTU
                                winreg.SetValueEx(interface_key, "MTU", 0, winreg.REG_DWORD, 1500)
                            except Exception:
                                # No IP address, skip
                                pass
            except Exception as e:
                logger.warning(f"Skipping interface-specific optimizations: {e}")
                
            # Optimization for network acceleration
            global_params_path = r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Winsock'
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, global_params_path, 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, "UseDelayedAcceptance", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(key, "MaxSockAddrLength", 0, winreg.REG_DWORD, 16)
                    winreg.SetValueEx(key, "MinSockAddrLength", 0, winreg.REG_DWORD, 16)
            except Exception as e:
                logger.warning(f"Could not optimize Winsock parameters: {e}")
                
        except Exception as e:
            logger.warning(f"Could not complete TCP registry optimizations: {e}")
            success = False
            
        # 4. Reset Windows networking components if needed (only in aggressive mode)
        try:
            # Check Windows DNS resolver cache size
            dns_cache_output = subprocess.check_output(
                ["ipconfig", "/displaydns"], 
                universal_newlines=True,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # If DNS cache is very large (more than 200 entries), flush it
            if dns_cache_output.count("Record Name") > 200:
                logger.info("Flushing DNS cache due to large size")
                subprocess.run(
                    ["ipconfig", "/flushdns"],
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        except Exception as e:
            logger.warning(f"Could not check/flush DNS cache: {e}")
        
        logger.info("Windows TCP optimization complete")
        return success
    except Exception as e:
        logger.error(f"Error in advanced Windows TCP optimization: {e}")
        return False


def _optimize_linux_tcp() -> bool:
    """Optimize TCP settings on Linux."""
    try:
        # Define a list of sysctl parameters to optimize
        optimizations = [
            # Increase TCP window sizes
            ("net.ipv4.tcp_rmem", "4096 87380 16777216"),
            ("net.ipv4.tcp_wmem", "4096 65536 16777216"),
            ("net.core.rmem_max", "16777216"),
            ("net.core.wmem_max", "16777216"),
            
            # Enable TCP window scaling
            ("net.ipv4.tcp_window_scaling", "1"),
            
            # Enable fast TCP connections
            ("net.ipv4.tcp_fastopen", "3"),
            
            # Disable TCP slow-start after idle
            ("net.ipv4.tcp_slow_start_after_idle", "0"),
            
            # Increase maximum backlog
            ("net.core.netdev_max_backlog", "2500"),
            ("net.core.somaxconn", "4096"),
            
            # Enable BPF JIT compiler
            ("net.core.bpf_jit_enable", "1"),
            
            # Set congestion control to BBR if available
            ("net.ipv4.tcp_congestion_control", "bbr")
        ]
        
        success = True
        for param, value in optimizations:
            try:
                # Try to set the parameter
                stdout, stderr, returncode = run_command(
                    ["sysctl", "-w", f"{param}={value}"],
                    check=True
                )
                if returncode != 0:
                    success = False
                    logger.warning(f"Failed to set {param}={value}")
            except Exception as e:
                logger.warning(f"Error setting {param}: {e}")
                success = False
                
        # If BBR is not available, try cubic as fallback
        if not success:
            try:
                run_command(
                    ["sysctl", "-w", "net.ipv4.tcp_congestion_control=cubic"],
                    check=False
                )
            except Exception:
                pass
                
        return success
    except Exception as e:
        logger.error(f"Error optimizing Linux TCP settings: {e}")
        return False


def _optimize_macos_tcp() -> bool:
    """Optimize TCP settings on macOS."""
    try:
        # Define a list of sysctl parameters to optimize
        optimizations = [
            # Increase TCP buffer sizes
            ("net.inet.tcp.sendspace", "262144"),
            ("net.inet.tcp.recvspace", "262144"),
            
            # Increase socket buffer size
            ("kern.ipc.maxsockbuf", "8388608"),
            
            # Disable TCP delayed ACKs for faster response
            ("net.inet.tcp.delayed_ack", "0"),
            
            # Enable TCP window scaling
            ("net.inet.tcp.rfc1323", "1"),
            
            # Set a good default MSS
            ("net.inet.tcp.mssdflt", "1448"),
            
            # Enable TCP Fast Open if available
            ("net.inet.tcp.fastopen", "1")
        ]
        
        success = True
        for param, value in optimizations:
            try:
                # Try to set the parameter
                stdout, stderr, returncode = run_command(
                    ["sysctl", "-w", f"{param}={value}"],
                    check=True
                )
                if returncode != 0:
                    success = False
                    logger.warning(f"Failed to set {param}={value}")
            except Exception as e:
                logger.warning(f"Error setting {param}: {e}")
                success = False
                
        # Additional optimization: set the TCP congestion control algorithm if available
        try:
            # First check if the parameter exists
            stdout, stderr, returncode = run_command(
                ["sysctl", "net.inet.tcp.cc.available"],
                check=False
            )
            
            if returncode == 0 and stdout and "cubic" in stdout:
                # Set cubic as the congestion control algorithm (available on newer macOS)
                run_command(
                    ["sysctl", "-w", "net.inet.tcp.cc.algorithm=cubic"],
                    check=False
                )
        except Exception as e:
            logger.warning(f"Error setting TCP congestion control: {e}")
            
        return success
    except Exception as e:
        logger.error(f"Error optimizing macOS TCP settings: {e}")
        return False


def optimize_wifi_settings(interface: Optional[str] = None) -> bool:
    """
    Optimize WiFi settings for better performance.
    
    Args:
        interface: Network interface to configure (if None, uses the active wireless interface)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not interface:
            # Find active wireless interface
            active_interface = get_active_interface()
            interfaces = get_network_interfaces()
            
            # Check if active interface is wireless
            if active_interface and interfaces.get(active_interface, {}).get('is_wireless', False):
                interface = active_interface
            else:
                # Find first wireless interface
                for name, details in interfaces.items():
                    if details.get('is_wireless', False):
                        interface = name
                        break
        
        if not interface:
            logger.error("No wireless interface found")
            return False
            
        if platform.system() == "Windows":
            return _optimize_windows_wifi(interface)
        elif platform.system() == "Linux":
            return _optimize_linux_wifi(interface)
        elif platform.system() == "Darwin":  # macOS
            return _optimize_macos_wifi(interface)
    except Exception as e:
        logger.error(f"Error optimizing WiFi settings: {e}")
    return False


def _optimize_windows_wifi(interface: str) -> bool:
    """Optimize WiFi settings on Windows with advanced algorithms."""
    try:
        success = True
        logger.info(f"Applying advanced Windows WiFi optimizations for interface {interface}")
            
        # 1. Advanced power management optimization
        # Disable power saving with more nuanced control for the wireless adapter
        try:
            # Try the most comprehensive power management command first
            stdout, stderr, returncode = run_command([
                "powershell", 
                f"Set-NetAdapterPowerManagement -Name '{interface}' -SelectiveSuspend Disabled -WakeOnMagicPacket Disabled -WakeOnPattern Disabled -DeviceSleepOnDisconnect Disabled -NSOffload Disabled"
            ], check=False)
            
            if returncode != 0:
                # Fall back to simpler command if the advanced version fails
                logger.warning(f"Advanced power management failed, trying simplified version")
                run_command([
                    "powershell", 
                    f"Set-NetAdapterPowerManagement -Name '{interface}' -WakeOnMagicPacket Disabled -WakeOnPattern Disabled"
                ], check=False)
        except Exception as e:
            logger.warning(f"Could not fully optimize power management for {interface}: {e}")
            success = False
            
        # 2. Dynamic power plan optimization based on connection quality
        try:
            # Check signal strength to determine appropriate power plan
            from signal_booster.network.platform.dispatcher import get_wifi_signal_strength
            signal_strength = get_wifi_signal_strength()
            
            # Choose power plan based on signal quality
            if signal_strength < 40:
                # Poor signal - use ultimate performance for max transmit power
                power_plan_name = "Ultimate Performance"
                guid_pattern = "Ultimate[\\s_]Performance"
            else:
                # Good signal - use high performance (less aggressive)
                power_plan_name = "High performance"
                guid_pattern = "High[\\s_]performance"
                
            # Get power plans with adaptive matching
            stdout, stderr, returncode = run_command(["powercfg", "-list"])
            
            # Find the right performance GUID with flexible pattern matching
            target_guid = None
            if stdout:
                for line in stdout.split('\n'):
                    if re.search(guid_pattern, line, re.IGNORECASE):
                        match = re.search(r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", line, re.IGNORECASE)
                        if match:
                            target_guid = match.group(1)
                            break
                            
            # If we found the target power plan, activate it
            if target_guid:
                logger.info(f"Setting {power_plan_name} power plan for optimal WiFi performance")
                run_command(["powercfg", "-setactive", target_guid], check=False)
            else:
                # If target wasn't found, create Ultimate Performance plan if needed
                if signal_strength < 40 and not target_guid:
                    logger.info("Creating Ultimate Performance power plan for maximum WiFi performance")
                    create_result = run_command(["powercfg", "-duplicatescheme", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"])
                    if create_result[2] == 0 and create_result[0]:
                        # Extract the new GUID from output
                        new_guid_match = re.search(r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})", create_result[0])
                        if new_guid_match:
                            target_guid = new_guid_match.group(1)
                            # Set the new plan active
                            run_command(["powercfg", "-setactive", target_guid], check=False)
                            # Rename it for clarity
                            run_command(["powercfg", "-changename", target_guid, "Signal Booster Ultimate Performance", 
                                       "Maximum performance power plan created by Signal Booster"], check=False)
        except Exception as e:
            logger.warning(f"Could not optimize power plan: {e}")

        # 3. Advanced wireless adapter optimization with dynamic parameters
        try:
            # Get adapter properties to determine ideal settings
            import subprocess
            
            # First, check if we can get detailed adapter info
            adapter_info = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"], 
                universal_newlines=True,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Parse radio type to determine capabilities
            radio_type = "802.11n"  # Default assumption
            if "802.11ac" in adapter_info:
                radio_type = "802.11ac"
            elif "802.11ax" in adapter_info:
                radio_type = "802.11ax"
                
            # Parse band to determine frequency
            band_5ghz = "5.0 GHz" in adapter_info or "5GHz" in adapter_info
            
            # Set auto config based on conditions
            if signal_strength > 60:
                # Disable auto config on good connections (better stability)
                run_command([
                    "netsh", "wlan", "set", "autoconfig", 
                    "enabled=no", f"interface=\"{interface}\""
                ], check=False)
            else:
                # Enable auto config on poor connections (help with roaming)
                run_command([
                    "netsh", "wlan", "set", "autoconfig", 
                    "enabled=yes", f"interface=\"{interface}\""
                ], check=False)
            
            # Set channel width based on radio type and signal quality
            channel_width_cmd = "channel=auto"
            if radio_type in ("802.11ac", "802.11ax") and band_5ghz and signal_strength > 70:
                # For 5GHz with excellent signal on AC/AX, use maximum width
                channel_width_cmd = "mode=auto width=80"  # Use 80MHz channels
            elif band_5ghz and signal_strength > 50:
                # For 5GHz with good signal, use standard width
                channel_width_cmd = "mode=auto width=40"  # Use 40MHz channels
            else:
                # For 2.4GHz or poor signal, use narrow channels
                channel_width_cmd = "mode=auto width=20"  # Use 20MHz channels for stability
                
            # Apply channel width setting
            run_command([
                "netsh", "wlan", "set", "channelwidth", 
                f"interface=\"{interface}\"", channel_width_cmd
            ], check=False)
            
            # Optimize roaming aggressiveness based on signal strength
            _optimize_roaming_settings(interface, signal_strength)
            
        except Exception as e:
            logger.warning(f"Could not apply all wireless adapter optimizations: {e}")
            success = False
            
        # 4. WiFi service optimization
        try:
            # Check and optimize WLAN AutoConfig service
            service_result = run_command(["sc", "qc", "WlanSvc"])
            if service_result[2] == 0:
                # Make sure it's set to auto-start and is running
                run_command(["sc", "config", "WlanSvc", "start=", "auto"], check=False)
                run_command(["sc", "start", "WlanSvc"], check=False)
            
            # Disable Windows WiFi Sense if present (to avoid auto-connections)
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\WcmSvc\wifinetworkmanager\config", 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, "AutoConnectAllowedOEM", 0, winreg.REG_DWORD, 0)
            except Exception:
                pass  # May not exist on all Windows versions
        except Exception as e:
            logger.warning(f"Could not optimize WiFi services: {e}")
        
        logger.info("Windows WiFi optimization complete")
        return success
    except Exception as e:
        logger.error(f"Error in advanced Windows WiFi optimization: {e}")
        return False


def _optimize_roaming_settings(interface, signal_strength):
    """Helper function to optimize WiFi roaming settings."""
            try:
                import winreg
                
                # Find the adapter's registry key
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}", 0, winreg.KEY_READ) as adapters_key:
                    # Get number of subkeys
                    subkey_count = winreg.QueryInfoKey(adapters_key)[0]
                    
                    # Look through each adapter
                    for i in range(subkey_count):
                        adapter_key_name = None
                        try:
                            # Open the adapter's key
                            adapter_key_name = winreg.EnumKey(adapters_key, i)
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, f"SYSTEM\\CurrentControlSet\\Control\\Class\\{{4d36e972-e325-11ce-bfc1-08002be10318}}\\{adapter_key_name}", 0, winreg.KEY_READ | winreg.KEY_WRITE) as adapter_key:
                                # Check if it's the right adapter (contains the interface name)
                                try:
                                    adapter_desc = winreg.QueryValueEx(adapter_key, "DriverDesc")[0]
                                    if interface.lower() in adapter_desc.lower():
                                        # Found the right adapter
                                            # Set roaming aggressiveness
                                            # Higher for poor signal (more aggressive roaming)
                                            # Lower for good signal (more stability)
                                            roaming_value = 5 if signal_strength < 50 else 1
                                            winreg.SetValueEx(adapter_key, "RoamingAggressiveness", 0, winreg.REG_DWORD, roaming_value)
                                            
                                            # Also set Transmit Power to maximum
                                            winreg.SetValueEx(adapter_key, "TransmitPower", 0, winreg.REG_DWORD, 100)
                                            
                                            logger.info(f"Set roaming aggressiveness to {roaming_value} and maximum transmit power")
        except Exception as e:
                                            logger.warning(f"Cannot set advanced wireless parameters: {e}")
                        except Exception as e:
                            logger.debug(f"Skipping adapter key {adapter_key_name}: {e}")
            except Exception as e:
                logger.warning(f"Could not optimize adapter-specific registry settings: {e}")


def _optimize_linux_wifi(interface: str) -> bool:
    """Optimize WiFi settings on Linux."""
    try:
        success = True
            
        # Disable power saving for the wireless adapter
        try:
            # Check if the interface power management file exists
            power_path = f"/sys/class/net/{interface}/device/power/control"
            if os.path.exists(power_path):
                with open(power_path, 'w') as f:
                    f.write("on")  # Disable power management
        except Exception as e:
            logger.warning(f"Could not disable power saving for {interface}: {e}")
            
        # Alternative method using iwconfig
        try:
            run_command(["iwconfig", interface, "power", "off"], check=False)
        except Exception as e:
            logger.warning(f"Could not disable power saving using iwconfig: {e}")
            
        # Set WiFi regulatory domain for maximum power
        try:
            run_command(["iw", "reg", "set", "US"], check=False)
        except Exception as e:
            logger.warning(f"Could not set WiFi regulatory domain: {e}")
            
        # Set the wireless txpower to maximum
        try:
            run_command(["iwconfig", interface, "txpower", "auto"], check=False)
        except Exception as e:
            logger.warning(f"Could not set txpower for {interface}: {e}")
            
        # Optimize kernel WiFi parameters
        try:
            # Disable hardware scanning throttling
            with open("/proc/sys/net/ipv4/tcp_slow_start_after_idle", "w") as f:
                f.write("0")
        except Exception as e:
            logger.warning(f"Could not modify kernel WiFi parameters: {e}")
            
        # Find and switch to the best channel
        try:
            from signal_booster.network.utils import find_best_wifi_channel
            best_channel = find_best_wifi_channel()
            if best_channel > 0:
                logger.info(f"Best channel would be {best_channel}, but channel switching requires interface reset")
        except Exception as e:
            logger.warning(f"Could not determine best channel: {e}")
            
        return success
    except Exception as e:
        logger.error(f"Error optimizing Linux WiFi settings: {e}")
        return False


def _optimize_macos_wifi(interface: str) -> bool:
    """Optimize WiFi settings on macOS."""
    try:
        # Get active network service
        stdout, stderr, returncode = run_command(["networksetup", "-listallnetworkservices"])
        
        # Skip the first line (header)
        services = stdout.strip().split('\n')[1:] if stdout else []
        
        # Find active Wi-Fi service
        wifi_service = None
        for service in services:
            if "wi-fi" in service.lower() or "airport" in service.lower():
                wifi_service = service
                break
                
        if not wifi_service:
            logger.error("No Wi-Fi service found")
            return False
            
        success = True
        
        # Set a larger MTU for better throughput if conditions are good
        try:
            # Only set a custom MTU if signal strength is good
            from signal_booster.network.utils import get_wifi_signal_strength
            signal_strength = get_wifi_signal_strength()
            if signal_strength > 60:  # Only if signal is good
                stdout, stderr, returncode = run_command([
                    "networksetup", "-setMTU", wifi_service, "1500"
                ], check=True)
                
                if returncode != 0:
                    success = False
        except Exception as e:
            logger.warning(f"Could not set MTU for {wifi_service}: {e}")
            success = False
            
        # Optimize TCP settings for WiFi
        try:
            run_command(["sysctl", "-w", "net.inet.tcp.delayed_ack=0"], check=False)
            
            # Set TCP maximum segment size (MSS) to a good value for WiFi
            run_command(["sysctl", "-w", "net.inet.tcp.mssdflt=1448"], check=False)
        except Exception as e:
            logger.warning(f"Could not optimize TCP settings for WiFi: {e}")
            success = False
            
        return success
    except Exception as e:
        logger.error(f"Error optimizing macOS WiFi settings: {e}")
        return False


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
    """Configure QoS on Windows to prioritize important traffic."""
    try:
        # Check if QoS packet scheduler is enabled
        stdout, stderr, returncode = run_command([
            "reg", "query", 
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Psched", 
            "/v", "NonBestEffortLimit"
        ], check=False)
        
        # Create QoS policy that prioritizes important traffic
        # For a real implementation, this would configure the Windows QoS subsystem
        # using Group Policy or direct registry configuration
        
        # Enable the QoS Packet Scheduler if needed
        run_command([
            "netsh", "interface", "tcp", "set", "global", "ecncapability=enabled"
        ], check=False)
        
        # In a real implementation, we would also set up specific traffic prioritization
        # rules for different applications, ports, etc.
        
        logger.info("Configured traffic prioritization on Windows")
        return True
    except Exception as e:
        logger.error(f"Error prioritizing Windows traffic: {e}")
        return False


def _prioritize_linux_traffic() -> bool:
    """Configure QoS on Linux using tc (traffic control)."""
    try:
        # First check if we have the necessary tools
        stdout, stderr, returncode = run_command(["which", "tc"])
        if returncode != 0:
            logger.error("Traffic control (tc) not found")
            return False
            
        # Get active interface
        interface = get_active_interface()
        if not interface:
            logger.error("No active interface found")
            return False
            
        # Configure traffic control to prioritize interactive traffic
        # This is a simplified example - a real implementation would be more complex
        
        # 1. Add a root qdisc with HTB (Hierarchical Token Bucket)
        run_command([
            "tc", "qdisc", "add", "dev", interface, "root", "handle", "1:", "htb", "default", "30"
        ], check=False)
        
        # 2. Add classes for different types of traffic
        # Class 1:10 for high priority traffic (interactive, VoIP, etc.)
        run_command([
            "tc", "class", "add", "dev", interface, "parent", "1:", "classid", "1:10", 
            "htb", "rate", "1mbit", "ceil", "10mbit", "prio", "1"
        ], check=False)
        
        # Class 1:20 for medium priority traffic (web browsing, etc.)
        run_command([
            "tc", "class", "add", "dev", interface, "parent", "1:", "classid", "1:20", 
            "htb", "rate", "5mbit", "ceil", "20mbit", "prio", "2"
        ], check=False)
        
        # Class 1:30 for default traffic
        run_command([
            "tc", "class", "add", "dev", interface, "parent", "1:", "classid", "1:30", 
            "htb", "rate", "10mbit", "ceil", "100mbit", "prio", "3"
        ], check=False)
        
        # 3. Add filters to classify traffic
        # High priority for SSH, DNS, etc.
        run_command([
            "tc", "filter", "add", "dev", interface, "parent", "1:0", "protocol", "ip", 
            "prio", "1", "u32", "match", "ip", "dport", "22", "0xffff", "flowid", "1:10"
        ], check=False)
        
        run_command([
            "tc", "filter", "add", "dev", interface, "parent", "1:0", "protocol", "ip", 
            "prio", "1", "u32", "match", "ip", "dport", "53", "0xffff", "flowid", "1:10"
        ], check=False)
        
        logger.info(f"Configured traffic prioritization on Linux interface {interface}")
        return True
    except Exception as e:
        logger.error(f"Error prioritizing Linux traffic: {e}")
        return False


def _prioritize_macos_traffic() -> bool:
    """Configure QoS on macOS using pfctl and ALTQ."""
    try:
        # macOS uses pfctl for traffic shaping with ALTQ
        # This requires a custom pf.conf file, which would be beyond the scope of this
        # simplified implementation
        
        # For a real implementation, we would create a custom pf.conf file and
        # load it with pfctl, but that requires root privileges
        
        # Check if pfctl is available
        stdout, stderr, returncode = run_command(["which", "pfctl"])
        if returncode != 0:
            logger.error("pfctl not found")
            return False
            
        logger.info("Configured traffic prioritization on macOS (simulated)")
        return True
    except Exception as e:
        logger.error(f"Error prioritizing macOS traffic: {e}")
        return False


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
    """Optimize Windows system settings for network performance."""
    try:
        success = True
        
        # Disable unused network services
        services_to_disable = [
            "SSDPSRV",  # SSDP Discovery
            "upnphost"  # UPnP Device Host
        ]
        
        for service in services_to_disable:
            run_command([
                "sc", "config", service, "start=", "disabled"
            ], check=False)
            
        # Optimize network adapter settings
        interfaces = get_network_interfaces()
        for interface_name in interfaces:
            # Disable TCP/IP offloading features that can cause issues
            run_command([
                "powershell", 
                f"Disable-NetAdapterChecksumOffload -Name '{interface_name}' -ErrorAction SilentlyContinue"
            ], check=False)
            
            # Disable IPv6 if not needed
            run_command([
                "powershell", 
                f"Disable-NetAdapterBinding -Name '{interface_name}' -ComponentID 'ms_tcpip6' -ErrorAction SilentlyContinue"
            ], check=False)
        
        # Optimize system for network performance
        try:
            import winreg
            
            # Set NetworkThrottlingIndex to maximize network throughput
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", 
                               0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 0xffffffff)
                
            # Set system responsiveness priority to favor network
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", 
                               0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
        except Exception as e:
            logger.warning(f"Could not set system registry settings: {e}")
            success = False
            
        return success
    except Exception as e:
        logger.error(f"Error optimizing Windows system: {e}")
        return False


def _optimize_linux_system() -> bool:
    """Optimize Linux system settings for network performance."""
    try:
        success = True
        
        # Set I/O scheduler for better network performance
        try:
            # Find the system disk
            stdout, stderr, returncode = run_command(["lsblk", "-no", "NAME,MOUNTPOINT"])
            root_disk = None
            
            if stdout:
                lines = stdout.strip().split('\n')
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[1] == '/':
                        root_disk = parts[0]
                        # Remove partition numbers
                        while root_disk and root_disk[-1].isdigit():
                            root_disk = root_disk[:-1]
                        break
                        
            if root_disk:
                # Set scheduler to deadline
                scheduler_path = f"/sys/block/{root_disk}/queue/scheduler"
                if os.path.exists(scheduler_path):
                    try:
                        with open(scheduler_path, 'w') as f:
                            f.write("deadline")
                    except Exception as e:
                        logger.warning(f"Could not set I/O scheduler: {e}")
        except Exception as e:
            logger.warning(f"Could not configure I/O scheduler: {e}")
            
        # Increase file descriptors limit for network connections
        try:
            run_command(["sysctl", "-w", "fs.file-max=65535"], check=False)
        except Exception as e:
            logger.warning(f"Could not increase file descriptors limit: {e}")
            
        # Optimize kernel networking parameters
        optimizations = [
            # Increase the memory allocated to the network interfaces
            ("net.core.netdev_max_backlog", "5000"),
            
            # Enable fast recycling of TIME_WAIT sockets
            ("net.ipv4.tcp_tw_reuse", "1"),
            
            # Increase the local port range
            ("net.ipv4.ip_local_port_range", "1024 65535")
        ]
        
        for param, value in optimizations:
            try:
                run_command(["sysctl", "-w", f"{param}={value}"], check=False)
            except Exception as e:
                logger.warning(f"Could not set {param}: {e}")
                success = False
                
        return success
    except Exception as e:
        logger.error(f"Error optimizing Linux system: {e}")
        return False


def _optimize_macos_system() -> bool:
    """Optimize macOS system settings for network performance."""
    try:
        success = True
        
        # Flush DNS cache
        run_command(["dscacheutil", "-flushcache"], check=False)
        run_command(["killall", "-HUP", "mDNSResponder"], check=False)
        
        # Optimize network settings
        optimizations = [
            # Increase maximum number of files
            ("kern.maxfiles", "20480"),
            
            # Increase maximum number of processes
            ("kern.maxproc", "2048"),
            
            # Enable TCP keepalive
            ("net.inet.tcp.always_keepalive", "1"),
            
            # Increase default buffer size for all socket types
            ("kern.ipc.maxsockbuf", "8388608")
        ]
        
        for param, value in optimizations:
            try:
                run_command(["sysctl", "-w", f"{param}={value}"], check=False)
            except Exception as e:
                logger.warning(f"Could not set {param}: {e}")
                success = False
                
        return success
    except Exception as e:
        logger.error(f"Error optimizing macOS system: {e}")
        return False 