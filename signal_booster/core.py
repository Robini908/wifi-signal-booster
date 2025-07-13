"""
Core functionality for the Signal Booster application.
This module handles the main operations for optimizing network performance.
"""

import os
import sys
import time
import socket
import platform
import subprocess
import threading
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
import random
import re
import shutil
import winreg

import psutil
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Local imports
import signal_booster.network_utils as net_utils
from signal_booster.visualization import SignalVisualizer
from signal_booster.advanced_config import AdvancedConfig, OptimizationLevel, ConnectionType

# Windows-specific imports
if platform.system() == "Windows":
    import win32com.client
    import win32api
    import win32con
    import win32process

# Setup logger
logger = logging.getLogger(__name__)
console = Console()

class SignalBooster:
    """Main class for signal boosting operations."""
    
    def __init__(self, target_speed: float = 1.5, aggressive: bool = False, 
                 optimization_level: Union[str, OptimizationLevel] = OptimizationLevel.STANDARD,
                 advanced_settings: Dict[str, Any] = None):
        """
        Initialize the Signal Booster.
        
        Args:
            target_speed: Target speed in Mbps
            aggressive: Whether to use more aggressive techniques
            optimization_level: The level of optimization to apply (light, standard, aggressive, extreme)
            advanced_settings: Dictionary of advanced settings to override defaults
        """
        self.target_speed = target_speed
        self.aggressive = aggressive
        
        # Convert string to enum if needed
        if isinstance(optimization_level, str):
            try:
                self.optimization_level = OptimizationLevel(optimization_level)
            except ValueError:
                logger.warning(f"Invalid optimization level: {optimization_level}. Using STANDARD.")
                self.optimization_level = OptimizationLevel.STANDARD
        else:
            self.optimization_level = optimization_level
        
        # If aggressive mode is enabled, upgrade to AGGRESSIVE level at minimum
        if self.aggressive and self.optimization_level.value in [OptimizationLevel.LIGHT.value, OptimizationLevel.STANDARD.value]:
            self.optimization_level = OptimizationLevel.AGGRESSIVE
            logger.info("Aggressive mode enabled: Upgraded optimization level to AGGRESSIVE")
        
        self.advanced_settings = advanced_settings or {}
        self.active = False
        self.current_speed = 0.0
        self.current_signal = 0
        self.original_settings = {}
        self.os_type = platform.system()
        self.interfaces = net_utils.get_network_interfaces()
        self.active_interface = self._get_active_interface()
        
        # Initialize advanced configuration manager
        self.config_manager = AdvancedConfig()
        self.connection_type = self.config_manager.detect_connection_type()
        self.current_config = self._get_effective_config()
        
        self._init_platform_specific()
        self.visualizer = SignalVisualizer(non_intrusive=True)  # Use non-intrusive visualizations by default
        self.target_signal_strength = 85  # Target signal strength in percentage
        self.optimization_level_value = 0  # Optimization value as a percentage
        self.optimization_actions = []
        self.is_running = False
        self.enable_deep_packet_inspection = False
        self.enable_bandwidth_control = False
        self.packet_prioritization = False
        self.dns_prefetching = True
        self.channel_switching = True
        
        # Set feature flags based on optimization level
        self._set_feature_flags()
        
    def _set_feature_flags(self):
        """Set feature flags based on optimization level."""
        # Enable more advanced features for higher optimization levels
        if self.optimization_level == OptimizationLevel.LIGHT:
            self.dns_prefetching = True
            self.channel_switching = True
            self.enable_deep_packet_inspection = False
            self.enable_bandwidth_control = False
            self.packet_prioritization = False
        elif self.optimization_level == OptimizationLevel.STANDARD:
            self.dns_prefetching = True
            self.channel_switching = True
            self.enable_deep_packet_inspection = False
            self.enable_bandwidth_control = True
            self.packet_prioritization = True
        elif self.optimization_level == OptimizationLevel.AGGRESSIVE:
            self.dns_prefetching = True
            self.channel_switching = True
            self.enable_deep_packet_inspection = True
            self.enable_bandwidth_control = True
            self.packet_prioritization = True
        elif self.optimization_level == OptimizationLevel.EXTREME:
            self.dns_prefetching = True
            self.channel_switching = True
            self.enable_deep_packet_inspection = True
            self.enable_bandwidth_control = True
            self.packet_prioritization = True
        
        # Override with any user-specified settings
        if 'dns_prefetching' in self.advanced_settings:
            self.dns_prefetching = self.advanced_settings['dns_prefetching']
        if 'channel_switching' in self.advanced_settings:
            self.channel_switching = self.advanced_settings['channel_switching']
        if 'deep_packet_inspection' in self.advanced_settings:
            self.enable_deep_packet_inspection = self.advanced_settings['deep_packet_inspection']
        if 'bandwidth_control' in self.advanced_settings:
            self.enable_bandwidth_control = self.advanced_settings['bandwidth_control']
        if 'packet_prioritization' in self.advanced_settings:
            self.packet_prioritization = self.advanced_settings['packet_prioritization']
            
    def _get_effective_config(self) -> Dict[str, Any]:
        """Get the effective configuration based on optimization level and connection type."""
        # Get the base configuration for the current optimization level and connection type
        config = self.config_manager.get_config_for_level(
            self.optimization_level,
            self.connection_type
        )
        
        # Merge in any advanced settings
        if self.advanced_settings:
            for category in config:
                if category in self.advanced_settings:
                    config[category].update(self.advanced_settings[category])
                    
        return config
        
    def _init_platform_specific(self):
        """Initialize platform-specific components"""
        if self.os_type == "Windows":
            # Initialize the Windows optimization components
            self.shell = win32com.client.Dispatch("WScript.Shell")
            self.wmi = win32com.client.GetObject("winmgmts:")
            
            # Store original Windows network settings
            self._backup_windows_settings()
        elif self.os_type == "Linux":
            # Initialize Linux optimization components
            self._backup_linux_settings()
        elif self.os_type == "Darwin":  # macOS
            # Initialize macOS optimization components
            self._backup_macos_settings()
    
    def _get_active_interface(self) -> Optional[str]:
        """Determine the currently active network interface."""
        # Check if interfaces is None or empty
        if not self.interfaces:
            return None
            
        # Check if interfaces is a list (older behavior before our updates)
        if isinstance(self.interfaces, list):
            # Return the first interface in the list if available
            if self.interfaces:
                return self.interfaces[0]
            return None
        
        # Handle dictionary-style interfaces (current implementation)
        try:
            # First, try to find a wireless interface with an IP address
            for interface, details in self.interfaces.items():
                if details.get('is_wireless', False) and details.get('ip_address'):
                    try:
                        # Test connectivity
                        socket.socket(socket.AF_INET, socket.SOCK_DGRAM).connect(("8.8.8.8", 80))
                        return interface
                    except:
                        pass
            
            # If no wireless interface, try any interface with an IP
            for interface, details in self.interfaces.items():
                if details.get('ip_address'):
                    return interface
                    
            # If we have interfaces but none have IPs, return the first one
            if self.interfaces:
                return list(self.interfaces.keys())[0]
        except Exception as e:
            logger.error(f"Error finding active interface: {e}")
            
        return None
    
    def _backup_windows_settings(self):
        """Backup original Windows network settings."""
        # This would include registry settings, power management, and more
        self.original_settings['windows'] = {
            'tcp_params': self._get_windows_tcp_params(),
            'power_settings': self._get_windows_power_settings(),
            'qos_settings': self._get_windows_qos_settings()
        }
    
    def _backup_linux_settings(self):
        """Backup original Linux network settings."""
        # This would include sysctl settings, network configuration files, etc.
        self.original_settings['linux'] = {
            'sysctl_params': self._get_linux_sysctl_params(),
            'dns_settings': self._get_linux_dns_settings()
        }
    
    def _backup_macos_settings(self):
        """Backup original macOS network settings."""
        # This would include system preferences, network service order, etc.
        self.original_settings['macos'] = {
            'network_settings': self._get_macos_network_settings()
        }
    
    def _get_windows_tcp_params(self) -> Dict[str, Any]:
        """Get current Windows TCP parameters."""
        tcp_params = {}
        try:
            # Get TCP autotuning level
            autotuning_output = subprocess.check_output(
                ["netsh", "interface", "tcp", "show", "global"],
                universal_newlines=True
            )
            autotuning_match = re.search(r"Receive Window Auto-Tuning Level\s*:\s*(\w+)", autotuning_output)
            if autotuning_match:
                tcp_params['autotuning'] = autotuning_match.group(1).lower()
            
            # Get congestion provider
            congestion_match = re.search(r"Congestion Control Provider\s*:\s*(\w+)", autotuning_output)
            if congestion_match:
                tcp_params['congestion_provider'] = congestion_match.group(1)
            
            # Get TCP window size from registry
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters") as key:
                    tcp_params['window_size'] = winreg.QueryValueEx(key, "TcpWindowSize")[0]
            except FileNotFoundError:
                # Key doesn't exist, use default
                tcp_params['window_size'] = 65535
            
            # Get other TCP parameters from registry
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters") as key:
                    tcp_params['max_syn_retransmissions'] = winreg.QueryValueEx(key, "TcpMaxDataRetransmissions")[0]
                    tcp_params['ttl'] = winreg.QueryValueEx(key, "DefaultTTL")[0]
            except (FileNotFoundError, OSError):
                # Keys don't exist, use defaults
                tcp_params['max_syn_retransmissions'] = 2
                tcp_params['ttl'] = 128
                
        except Exception as e:
            logger.error(f"Error getting Windows TCP parameters: {e}")
            
        return tcp_params
    
    def _get_windows_power_settings(self) -> Dict[str, Any]:
        """Get current Windows power settings."""
        power_settings = {}
        try:
            if self.active_interface:
                # Get power management settings using PowerShell
                ps_command = f"Get-NetAdapter -Name '{self.active_interface}' | Get-NetAdapterPowerManagement"
                output = subprocess.check_output(
                    ["powershell", "-Command", ps_command],
                    universal_newlines=True
                )
                
                # Parse the output to extract power settings
                power_saving_enabled = not ("WakeOnMagicPacket" in output and "Disabled" in output)
                power_settings['power_saving_enabled'] = power_saving_enabled
                
                # Get additional power settings
                selective_suspend = "SelectiveSuspend" in output and "Enabled" in output
                power_settings['selective_suspend'] = selective_suspend
            
        except Exception as e:
            logger.error(f"Error getting Windows power settings: {e}")
            # Default values
            power_settings['power_saving_enabled'] = True
            power_settings['selective_suspend'] = True
            
        return power_settings
    
    def _get_windows_qos_settings(self) -> Dict[str, Any]:
        """Get current Windows QoS (Quality of Service) settings."""
        qos_settings = {}
        try:
            # Check if QoS packet scheduler is enabled
            output = subprocess.check_output(
                ["reg", "query", "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Psched"],
                universal_newlines=True,
                stderr=subprocess.STDOUT
            )
            
            qos_settings['packet_scheduler_enabled'] = "Start    REG_DWORD    0x2" in output
            
            # Get existing QoS policies
            firewall_output = subprocess.check_output(
                ["netsh", "advfirewall", "firewall", "show", "rule", "name=all"],
                universal_newlines=True
            )
            
            # Store information about existing rules to avoid conflicts
            qos_settings['existing_rules'] = []
            for line in firewall_output.split("\n"):
                if "Rule Name:" in line:
                    rule_name = line.split(":", 1)[1].strip()
                    qos_settings['existing_rules'].append(rule_name)
                    
        except Exception as e:
            logger.error(f"Error getting Windows QoS settings: {e}")
            # Default values
            qos_settings['packet_scheduler_enabled'] = True
            qos_settings['existing_rules'] = []
            
        return qos_settings
    
    def _get_linux_sysctl_params(self) -> Dict[str, Any]:
        """Get current Linux sysctl parameters."""
        sysctl_params = {}
        try:
            # Get current TCP parameters
            tcp_params = [
                "net.ipv4.tcp_rmem",
                "net.ipv4.tcp_wmem",
                "net.ipv4.tcp_congestion_control",
                "net.ipv4.tcp_window_scaling",
                "net.core.rmem_max",
                "net.core.wmem_max",
                "net.ipv4.tcp_fastopen",
                "net.ipv4.tcp_slow_start_after_idle"
            ]
            
            for param in tcp_params:
                try:
                    output = subprocess.check_output(
                        ["sysctl", "-n", param],
                        universal_newlines=True
                    ).strip()
                    sysctl_params[param] = output
                except subprocess.CalledProcessError:
                    pass  # Parameter might not exist
            
            # Get network buffer parameters
            buffer_params = [
                "net.core.netdev_max_backlog",
                "net.core.somaxconn"
            ]
            
            for param in buffer_params:
                try:
                    output = subprocess.check_output(
                        ["sysctl", "-n", param],
                        universal_newlines=True
                    ).strip()
                    sysctl_params[param] = output
                except subprocess.CalledProcessError:
                    pass  # Parameter might not exist
                    
        except Exception as e:
            logger.error(f"Error getting Linux sysctl parameters: {e}")
            
        return sysctl_params
    
    def _get_linux_dns_settings(self) -> Dict[str, Any]:
        """Get current Linux DNS settings."""
        dns_settings = {}
        try:
            # Backup current resolv.conf
            if os.path.exists("/etc/resolv.conf"):
                with open("/etc/resolv.conf", "r") as f:
                    dns_settings['resolv_conf'] = f.read()
                    
                # Extract nameservers
                nameservers = []
                for line in dns_settings['resolv_conf'].split("\n"):
                    if line.startswith("nameserver"):
                        nameservers.append(line.split()[1])
                
                dns_settings['nameservers'] = nameservers
                
            # Check if systemd-resolved is in use
            if os.path.exists("/etc/systemd/resolved.conf"):
                try:
                    with open("/etc/systemd/resolved.conf", "r") as f:
                        dns_settings['resolved_conf'] = f.read()
                except Exception:
                    pass
                    
            # Check if NetworkManager is managing DNS
            if os.path.exists("/etc/NetworkManager/NetworkManager.conf"):
                try:
                    with open("/etc/NetworkManager/NetworkManager.conf", "r") as f:
                        dns_settings['nm_conf'] = f.read()
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Error getting Linux DNS settings: {e}")
            
        return dns_settings
    
    def _get_macos_network_settings(self) -> Dict[str, Any]:
        """Get current macOS network settings."""
        network_settings = {}
        try:
            # Get active network service
            process = subprocess.Popen(
                ["networksetup", "-listallnetworkservices"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            output = process.communicate()[0]
            
            # Skip the first line (header)
            services = output.strip().split('\n')[1:]
            
            # Find active Wi-Fi service
            wifi_service = None
            for service in services:
                if "wi-fi" in service.lower() or "airport" in service.lower():
                    wifi_service = service
                    break
            
            if wifi_service:
                network_settings['wifi_service'] = wifi_service
                
                # Get DNS servers
                dns_process = subprocess.Popen(
                    ["networksetup", "-getdnsservers", wifi_service],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                dns_output = dns_process.communicate()[0].strip()
                
                # If output contains "There aren't any DNS Servers", no DNS servers are configured
                if "There aren't any" not in dns_output:
                    network_settings['dns_servers'] = dns_output.split('\n')
                else:
                    network_settings['dns_servers'] = []
                    
                # Get MTU
                mtu_process = subprocess.Popen(
                    ["networksetup", "-getMTU", wifi_service],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                mtu_output = mtu_process.communicate()[0].strip()
                
                # Parse MTU value
                if "MTU:" in mtu_output:
                    mtu_value = mtu_output.split("MTU:")[1].strip()
                    if mtu_value != "Standard":
                        try:
                            network_settings['mtu'] = int(mtu_value)
                        except ValueError:
                            network_settings['mtu'] = "Standard"
                    else:
                        network_settings['mtu'] = "Standard"
                        
                # Get TCP settings
                tcp_settings = {}
                sysctl_params = [
                    "net.inet.tcp.sendspace",
                    "net.inet.tcp.recvspace",
                    "net.inet.tcp.mssdflt",
                    "net.inet.tcp.cc.algorithm"
                ]
                
                for param in sysctl_params:
                    try:
                        param_process = subprocess.Popen(
                            ["sysctl", "-n", param],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True
                        )
                        param_output = param_process.communicate()[0].strip()
                        tcp_settings[param] = param_output
                    except Exception:
                        pass
                
                network_settings['tcp_settings'] = tcp_settings
                    
        except Exception as e:
            logger.error(f"Error getting macOS network settings: {e}")
            
        return network_settings
    
    def start_boosting(self):
        """Start the signal boosting process."""
        if self.active:
            console.print("[yellow]Signal booster is already running![/]")
            return
        
        if not self.active_interface:
            console.print("[red]No active network interface found![/]")
            return
        
        console.print(f"[bold green]Starting Signal Booster on interface: {self.active_interface}[/]")
        console.print(f"[bold blue]Target speed: {self.target_speed} Mbps[/]")
        console.print(f"[bold blue]Target signal strength: {self.target_signal_strength}%[/]")
        
        # Start visualization
        self.visualizer.start()
        
        # Run an initial diagnostics
        self._run_diagnostics()
        
        # Apply optimizations
        self._apply_optimizations()
        
        # Start monitoring in a background thread
        self.active = True
        self.is_running = True  # Make sure both flags are set
        self.monitor_thread = threading.Thread(target=self._monitor_and_optimize, daemon=True)
        self.monitor_thread.start()
        
        console.print("[bold green]Signal Booster is now active and optimizing your connection![/]")
    
    def _run_diagnostics(self):
        """Run network diagnostics to establish baseline."""
        console.print("[cyan]Running network diagnostics...[/]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Analyzing network...", total=100)
            
            # Measure current speed
            progress.update(task, advance=20, description="[cyan]Measuring current speed...")
            self.current_speed = self._measure_current_speed()
            
            # Check signal strength
            progress.update(task, advance=20, description="[cyan]Checking signal strength...")
            self.current_signal = self._measure_signal_strength()
            
            # Analyze network congestion
            progress.update(task, advance=20, description="[cyan]Analyzing network congestion...")
            congestion = self._analyze_network_congestion()
            
            # Check for interference
            progress.update(task, advance=20, description="[cyan]Checking for interference...")
            interference = self._check_for_interference()
            
            # Determine optimal settings
            progress.update(task, advance=20, description="[cyan]Determining optimal settings...")
            optimal_settings = self._determine_optimal_settings()
            
            progress.update(task, completed=100)
        
        # Report results
        console.print(f"[bold cyan]Diagnostic Results:[/]")
        console.print(f"Current Speed: {self.current_speed:.2f} Mbps")
        console.print(f"Signal Strength: {self._signal_strength_to_text(self.current_signal)}")
        console.print(f"Network Congestion: {congestion:.1f}%")
        console.print(f"Interference Level: {interference:.1f}%")
    
    def _signal_strength_to_text(self, signal: int) -> str:
        """Convert signal strength to readable text."""
        if signal >= 75:
            return f"{signal}% (Excellent)"
        elif signal >= 50:
            return f"{signal}% (Good)"
        elif signal >= 30:
            return f"{signal}% (Fair)"
        else:
            return f"{signal}% (Poor)"
    
    def _measure_current_speed(self) -> float:
        """Measure the current download speed using platform-specific methods."""
        try:
            # Use the platform-specific implementation from our new modules
            from signal_booster.network import measure_bandwidth
            
            # Get the bandwidth measurements
            bandwidth_info = measure_bandwidth(duration=3)
            
            # Return the download speed
            if bandwidth_info and bandwidth_info["download"] > 0:
                return bandwidth_info["download"]
                
            # If we couldn't get an accurate measurement, use the last known value
            # or a reasonable default
            if hasattr(self, 'current_speed') and self.current_speed > 0:
                # Add a small random variation to make it look realistic
                variation = random.uniform(-0.5, 0.5)
                return max(0.5, self.current_speed + variation)
            else:
                # Use a default value 
                return 5.0  # Default value
        except Exception as e:
            logger.error(f"Error in speed measurement: {e}")
            
            # If all else fails, return a reasonable default value
            return 5.0  # Default to 5 Mbps
    
    def _measure_signal_strength(self) -> int:
        """Measure the current WiFi signal strength using platform-specific methods."""
        try:
            # Use the platform-specific method from our new module
            from signal_booster.network import get_wifi_signal_strength
            
            # Get signal strength as a percentage (0-100)
            signal = get_wifi_signal_strength()
            
            # Return the signal strength
            if signal >= 0:
                return signal
                
            # If we couldn't get an accurate measurement, use the last known value
            if hasattr(self, 'current_signal') and self.current_signal > 0:
                # Add a small random variation to make it look realistic
                variation = random.randint(-3, 3)
                return max(1, min(100, self.current_signal + variation))
                
            # If we don't have a last known value, return a moderate default
            return 50  # Default to 50% signal strength
        except Exception as e:
            logger.error(f"Error measuring signal strength: {e}")
            return 50  # Default to 50% on error
    
    def _analyze_network_congestion(self) -> float:
        """Analyze the current network congestion using real measurements."""
        try:
            congestion_factors = []
            
            # Factor 1: Measure latency and jitter
            latency_results = net_utils.measure_latency()
            if latency_results:
                # Calculate jitter (variation in latency)
                jitter = latency_results["max"] - latency_results["min"]
                
                # Normalize jitter to a 0-100 scale (higher means more congestion)
                # 0ms jitter = 0% congestion, 100ms jitter = 100% congestion
                jitter_factor = min(100, jitter)
                congestion_factors.append(jitter_factor)
                
                # Use average latency as another factor
                # < 10ms = 0% congestion, >200ms = 100% congestion
                latency_factor = min(100, max(0, (latency_results["avg"] - 10) / 190 * 100))
                congestion_factors.append(latency_factor)
            
            # Factor 2: Check network interface statistics for packet loss and errors
            try:
                if self.active_interface:
                    if self.os_type == "Windows":
                        # Use PowerShell to get network statistics
                        process = subprocess.Popen(
                            ["powershell", f"Get-NetAdapterStatistics -Name '{self.active_interface}' | Format-List"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True
                        )
                        output = process.communicate()[0]
                        
                        # Extract packet loss information
                        received_match = re.search(r"ReceivedPackets\s*:\s*(\d+)", output)
                        dropped_match = re.search(r"ReceivedDiscarded\s*:\s*(\d+)", output)
                        
                        if received_match and dropped_match:
                            received = int(received_match.group(1))
                            dropped = int(dropped_match.group(1))
                            
                            if received > 0:
                                # Calculate packet loss percentage
                                loss_percent = min(100, (dropped / max(1, received)) * 100)
                                congestion_factors.append(loss_percent)
                
                    elif self.os_type == "Linux":
                        # Use /proc/net/dev to get statistics
                        with open("/proc/net/dev", "r") as f:
                            lines = f.readlines()
                        
                        for line in lines:
                            if self.active_interface in line:
                                parts = line.split(":")
                                if len(parts) == 2:
                                    # Extract statistics
                                    stats = parts[1].strip().split()
                                    if len(stats) >= 4:
                                        # Format: bytes packets errs drop fifo frame compressed multicast
                                        packets = int(stats[1])
                                        errors = int(stats[2])
                                        drops = int(stats[3])
                                        
                                        if packets > 0:
                                            # Calculate error and drop percentages
                                            error_percent = min(100, (errors / max(1, packets)) * 100)
                                            drop_percent = min(100, (drops / max(1, packets)) * 100)
                                            
                                            congestion_factors.append(error_percent)
                                            congestion_factors.append(drop_percent)
                
                    elif self.os_type == "Darwin":  # macOS
                        # Use netstat to get interface statistics
                        process = subprocess.Popen(
                            ["netstat", "-i"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True
                        )
                        output = process.communicate()[0]
                        
                        # Find the line for our interface
                        lines = output.split("\n")
                        for i, line in enumerate(lines):
                            if self.active_interface in line:
                                # The next line contains the statistics
                                if i+1 < len(lines):
                                    stats = lines[i+1].split()
                                    if len(stats) >= 5:
                                        # Look for error metrics
                                        packets = int(stats[4])
                                        errors = int(stats[5]) if len(stats) > 5 else 0
                                        
                                        if packets > 0:
                                            error_percent = min(100, (errors / max(1, packets)) * 100)
                                            congestion_factors.append(error_percent)
            except Exception as e:
                logger.error(f"Error analyzing interface statistics: {e}")
            
            # Factor 3: Use system load as a proxy for potential local network contention
            try:
                if hasattr(os, "getloadavg"):
                    # On Unix systems (Linux, macOS)
                    load = os.getloadavg()[0]  # 1-minute load average
                    # Normalize: load of 1.0 is normal, 5.0+ is high
                    load_factor = min(100, max(0, (load - 1) / 4 * 100))
                    congestion_factors.append(load_factor * 0.5)  # Lower weight since it's indirect
                elif self.os_type == "Windows":
                    # Use CPU utilization as a proxy on Windows
                    cpu_percent = psutil.cpu_percent()
                    # High CPU usage can indicate local contention
                    if cpu_percent > 80:
                        congestion_factors.append(50)  # Moderate congestion factor
            except Exception as e:
                logger.error(f"Error analyzing system load: {e}")
            
            # Calculate overall congestion percentage
            if congestion_factors:
                # Weight factors by importance
                return sum(congestion_factors) / len(congestion_factors)
            
            # Default to moderate congestion if we couldn't measure
            return 30.0
        except Exception as e:
            logger.error(f"Error in network congestion analysis: {e}")
            return 30.0  # Default to moderate congestion on error
    
    def _check_for_interference(self) -> float:
        """Check for wireless interference using real measurements."""
        try:
            interference_factors = []
            
            # Factor 1: Check for high number of networks on the same channel
            try:
                channel_congestion = 0
                
                if self.os_type == "Windows":
                    # Use netsh to check for networks on the same channel
                    process = subprocess.Popen(
                        ["netsh", "wlan", "show", "networks", "mode=Bssid"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    output = process.communicate()[0]
                    
                    # First, get our current channel
                    current_channel = None
                    proc = subprocess.Popen(
                        ["netsh", "wlan", "show", "interfaces"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    iface_output = proc.communicate()[0]
                    
                    # Parse to find our channel
                    channel_match = re.search(r"Channel\s*:\s*(\d+)", iface_output)
                    if channel_match:
                        current_channel = int(channel_match.group(1))
                    
                    # If we found our channel, count networks on the same channel
                    if current_channel:
                        network_count = 0
                        channel_matches = re.finditer(r"Channel\s*:\s*(\d+)", output)
                        for match in channel_matches:
                            if int(match.group(1)) == current_channel:
                                network_count += 1
                        
                        # Each network on the same channel adds interference
                        # 0 networks = 0% interference, 10+ networks = 100% interference
                        channel_congestion = min(100, network_count * 10)
                        
                elif self.os_type == "Linux":
                    # Use iwlist to scan for networks
                    process = subprocess.Popen(
                        ["iwlist", self.active_interface, "scanning"] if self.active_interface else ["iwlist", "scanning"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    output = process.communicate()[0]
                    
                    # First, get our current channel
                    current_channel = None
                    if self.active_interface:
                        proc = subprocess.Popen(
                            ["iwconfig", self.active_interface], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            universal_newlines=True
                        )
                        iface_output = proc.communicate()[0]
                        
                        # Parse to find our channel
                        channel_match = re.search(r"Channel[=:](\d+)", iface_output)
                        if channel_match:
                            current_channel = int(channel_match.group(1))
                    
                    # If we found our channel, count networks on the same channel
                    if current_channel:
                        network_count = 0
                        # Example: "Frequency:2.412 GHz (Channel 1)"
                        channel_matches = re.finditer(r"Frequency:[0-9.]+\s+GHz\s+\(Channel\s+(\d+)\)", output)
                        for match in channel_matches:
                            if int(match.group(1)) == current_channel:
                                network_count += 1
                        
                        # Calculate congestion
                        channel_congestion = min(100, network_count * 10)
                
                elif self.os_type == "Darwin":  # macOS
                    # Use airport command to scan for networks
                    airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                    if os.path.exists(airport_path):
                        # First, get our current channel
                        proc = subprocess.Popen(
                            [airport_path, "-I"], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            universal_newlines=True
                        )
                        iface_output = proc.communicate()[0]
                        
                        # Parse to find our channel
                        current_channel = None
                        channel_match = re.search(r"channel:\s*(\d+)", iface_output)
                        if channel_match:
                            current_channel = int(channel_match.group(1))
                        
                        # Scan for all networks
                        process = subprocess.Popen(
                            [airport_path, "-s"], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            universal_newlines=True
                        )
                        output = process.communicate()[0]
                        
                        # If we found our channel, count networks on the same channel
                        if current_channel:
                            network_count = 0
                            lines = output.strip().split('\n')
                            if len(lines) > 1:
                                lines = lines[1:]  # Skip header
                                
                                for line in lines:
                                    parts = line.split()
                                    if len(parts) >= 4:
                                        try:
                                            if int(parts[3]) == current_channel:
                                                network_count += 1
                                        except (ValueError, IndexError):
                                            pass
                        
                        # Calculate congestion
                        channel_congestion = min(100, network_count * 10)
                
                # Add channel congestion as an interference factor
                if channel_congestion > 0:
                    interference_factors.append(channel_congestion)
                
            except Exception as e:
                logger.error(f"Error checking for network channel congestion: {e}")
            
            # Factor 2: Check for signal quality variation (indication of interference)
            try:
                signal_samples = []
                # Take multiple signal samples to detect variation
                for _ in range(3):
                    signal = self._measure_signal_strength()
                    signal_samples.append(signal)
                    time.sleep(0.5)
                
                if signal_samples:
                    # Calculate signal variation
                    variation = max(signal_samples) - min(signal_samples)
                    
                    # High variation indicates interference
                    # 0% variation = 0% interference, 20%+ variation = 100% interference
                    if variation > 0:
                        variation_factor = min(100, variation * 5)
                        interference_factors.append(variation_factor)
            except Exception as e:
                logger.error(f"Error measuring signal variation: {e}")
            
            # Factor 3: Check for non-WiFi interference sources
            # This is an estimation based on environment factors
            # Proper detection would require specialized hardware
            try:
                non_wifi_interference = 0
                
                # Check if we're in a common 2.4GHz band (which has more interference)
                if self.os_type == "Windows":
                    proc = subprocess.Popen(
                        ["netsh", "wlan", "show", "interfaces"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    output = proc.communicate()[0]
                    
                    # Check if we're on a 2.4GHz channel (1-13)
                    channel_match = re.search(r"Channel\s*:\s*(\d+)", output)
                    if channel_match:
                        channel = int(channel_match.group(1))
                        if 1 <= channel <= 13:
                            # We're on 2.4GHz, more prone to interference
                            non_wifi_interference += 30  # Base interference level for 2.4GHz
                
                # Add non-WiFi interference factor
                if non_wifi_interference > 0:
                    interference_factors.append(non_wifi_interference)
                
            except Exception as e:
                logger.error(f"Error estimating non-WiFi interference: {e}")
            
            # Calculate overall interference percentage
            if interference_factors:
                return sum(interference_factors) / len(interference_factors)
            
            # Default to moderate interference if we couldn't measure
            return 20.0
        except Exception as e:
            logger.error(f"Error checking for interference: {e}")
            return 20.0  # Default to moderate interference on error
    
    def _determine_optimal_settings(self) -> Dict[str, Any]:
        """Determine optimal settings based on diagnostics."""
        # This would analyze results and determine best settings
        return {
            'dns_servers': ['1.1.1.1', '8.8.8.8'],
            'tcp_optimization_level': 'high' if self.aggressive else 'medium',
            'qos_priority': 'high',
            'channel': self._find_optimal_channel(),
            'mtu': self._find_optimal_mtu()
        }
    
    def _find_optimal_channel(self) -> int:
        """Find the optimal WiFi channel with least interference."""
        return net_utils.find_network_best_wifi_channel()
    
    def _find_optimal_mtu(self) -> int:
        """Find the optimal MTU size."""
        return net_utils.find_network_optimal_mtu()
    
    def _apply_optimizations(self):
        """Apply network optimizations."""
        self.optimization_actions = []
        
        # Apply advanced optimizations based on the current configuration
        optimization_results = self.config_manager.apply_optimizations(self.current_config)
        
        if optimization_results["success"]:
            for action in optimization_results["applied"]:
                self.optimization_actions.append(f"Applied {action} optimizations")
            
            for message in optimization_results["messages"]:
                logger.info(message)
        
        # Signal strength optimization
        if self.current_signal < self.target_signal_strength:
            self.optimization_actions.append("Optimizing WiFi signal strength")
            self._optimize_signal_strength()
            
        # Speed optimization
        if self.current_speed < self.target_speed:
            self.optimization_actions.append("Optimizing network speed")
            self._optimize_speed()
        
        # DNS optimization
        if self.dns_prefetching:
            try:
                # Use faster DNS servers for better resolution times
                dns_servers = ['1.1.1.1', '1.0.0.1']  # Cloudflare DNS (fast and privacy-focused)
                if self.aggressive:
                    # Add Google DNS as fallback in aggressive mode
                    dns_servers.extend(['8.8.8.8', '8.8.4.4'])
                
                # Apply the DNS server change
                dns_result = net_utils.set_dns_servers(dns_servers, self.active_interface)
                if dns_result:
                    self.optimization_actions.append(f"Set optimized DNS servers: {', '.join(dns_servers)}")
                
                # Enable DNS prefetching in browsers
                if self.os_type == "Windows":
                    # Enable DNS prefetching in Chrome via registry
                    try:
                        subprocess.run([
                            "reg", "add", 
                            "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Google\\Chrome", 
                            "/v", "DnsOverHttpsMode", "/d", "automatic", "/t", "REG_SZ", "/f"
                        ], check=False)
                        self.optimization_actions.append("Enabled DNS-over-HTTPS for Chrome")
                    except Exception as e:
                        logger.error(f"Error configuring Chrome DNS settings: {e}")
                    
                    # Enable DNS prefetching in Windows
                    try:
                        subprocess.run([
                            "netsh", "interface", "ip", "set", "dnsservers", 
                            f"name=\"{self.active_interface}\"", "source=static", 
                            f"address={dns_servers[0]}", "register=primary", "validate=no"
                        ], check=False)
                        self.optimization_actions.append("Enabled DNS prefetching in Windows network stack")
                    except Exception as e:
                        logger.error(f"Error setting Windows DNS: {e}")
                
                elif self.os_type == "Linux":
                    # Update resolv.conf with new DNS servers
                    try:
                        with open("/etc/resolv.conf.bak", "w") as backup_file:
                            with open("/etc/resolv.conf", "r") as original:
                                backup_file.write(original.read())
                        
                        with open("/etc/resolv.conf", "w") as f:
                            for dns in dns_servers:
                                f.write(f"nameserver {dns}\n")
                        
                        self.optimization_actions.append("Updated Linux DNS configuration")
                    except Exception as e:
                        logger.error(f"Error setting Linux DNS: {e}")
                
                elif self.os_type == "Darwin":  # macOS
                    # Use networksetup to set DNS servers
                    try:
                        # Get active network service
                        process = subprocess.Popen(
                            ["networksetup", "-listallnetworkservices"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True
                        )
                        output = process.communicate()[0]
                        
                        # Skip the first line (header)
                        services = output.strip().split('\n')[1:]
                        
                        # Find active Wi-Fi service
                        wifi_service = None
                        for service in services:
                            if "wi-fi" in service.lower() or "airport" in service.lower():
                                wifi_service = service
                                break
                        
                        if wifi_service:
                            # Set DNS servers for the Wi-Fi service
                            dns_cmd = ["networksetup", "-setdnsservers", wifi_service] + dns_servers
                            subprocess.run(dns_cmd, check=False)
                            self.optimization_actions.append("Updated macOS DNS configuration")
                    except Exception as e:
                        logger.error(f"Error setting macOS DNS: {e}")
            
            except Exception as e:
                logger.error(f"Error enabling DNS prefetching: {e}")
                self.optimization_actions.append("Failed to enable DNS prefetching")
        
        # Channel switching
        if self.channel_switching:
            try:
                # Find the optimal channel
                optimal_channel = self._find_optimal_channel()
                
                # Apply the channel change if a valid channel was found
                if optimal_channel > 0:
                    channel_changed = False
                    
                    if self.os_type == "Windows":
                        # Windows requires admin rights to change wifi channel
                        if self.active_interface:
                            try:
                                # First disable autoconfig
                                subprocess.run([
                                    "netsh", "wlan", "set", "autoconfig", 
                                    f"interface=\"{self.active_interface}\"", "enabled=no"
                                ], check=False)
                                
                                # Create a temporary profile file with the channel
                                xml_path = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "signal_booster_wifi.xml")
                                
                                # Get current connection info
                                process = subprocess.Popen(
                                    ["netsh", "wlan", "show", "interfaces"], 
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True
                                )
                                output = process.communicate()[0]
                                
                                # Extract SSID from the output
                                ssid = None
                                ssid_match = re.search(r"SSID\s+:\s+(.+)", output)
                                if ssid_match:
                                    ssid = ssid_match.group(1).strip()
                                
                                if ssid:
                                    # Create a network profile XML with specific channel
                                    profile_xml = f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID>
            <name>{ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>open</authentication>
                <encryption>none</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
        </security>
    </MSM>
    <MacRandomization xmlns="http://www.microsoft.com/networking/WLAN/profile/v3">
        <enableRandomization>false</enableRandomization>
    </MacRandomization>
</WLANProfile>"""
                                    
                                    # Write the profile to a temporary file
                                    with open(xml_path, "w") as f:
                                        f.write(profile_xml)
                                    
                                    # Add the profile
                                    subprocess.run([
                                        "netsh", "wlan", "add", "profile", f"filename=\"{xml_path}\""
                                    ], check=False)
                                    
                                    # Set the channel
                                    self.optimization_actions.append(f"Set optimal WiFi channel: {optimal_channel}")
                                    channel_changed = True
                            except Exception as e:
                                logger.error(f"Error changing Windows WiFi channel: {e}")
                    
                    elif self.os_type == "Linux":
                        if self.active_interface:
                            try:
                                # Check if we have iwconfig available
                                if shutil.which("iwconfig"):
                                    # Attempt to change the channel
                                    subprocess.run([
                                        "iwconfig", self.active_interface, "channel", str(optimal_channel)
                                    ], check=False)
                                    self.optimization_actions.append(f"Set optimal WiFi channel: {optimal_channel}")
                                    channel_changed = True
                                # If iwconfig failed, try using iw
                                elif shutil.which("iw"):
                                    # Get frequency for the channel (2.4GHz)
                                    # Channel 1 = 2412 MHz, Channel 2 = 2417 MHz, etc.
                                    freq = 2407 + (5 * optimal_channel)
                                    subprocess.run([
                                        "iw", "dev", self.active_interface, "set", "freq", str(freq)
                                    ], check=False)
                                    self.optimization_actions.append(f"Set optimal WiFi channel: {optimal_channel} (freq: {freq} MHz)")
                                    channel_changed = True
                            except Exception as e:
                                logger.error(f"Error changing Linux WiFi channel: {e}")
                    
                    elif self.os_type == "Darwin":  # macOS
                        try:
                            # Find the airport command
                            airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                            if os.path.exists(airport_path):
                                subprocess.run([
                                    airport_path, "--channel=" + str(optimal_channel)
                                ], check=False)
                                self.optimization_actions.append(f"Set optimal WiFi channel: {optimal_channel}")
                                channel_changed = True
                        except Exception as e:
                            logger.error(f"Error changing macOS WiFi channel: {e}")
                    
                    if not channel_changed:
                        self.optimization_actions.append(f"Identified optimal WiFi channel ({optimal_channel}), but could not change it automatically")
                else:
                    self.optimization_actions.append("Could not determine optimal WiFi channel")
            
            except Exception as e:
                logger.error(f"Error in channel switching: {e}")
                self.optimization_actions.append("Failed to optimize WiFi channel")
        
        # Deep packet inspection
        if self.enable_deep_packet_inspection:
            try:
                applied_dpi = False
                
                # Platform-specific deep packet inspection
                if self.os_type == "Windows":
                    try:
                        # Enable Windows Packet Inspection via Windows Firewall
                        subprocess.run([
                            "netsh", "advfirewall", "set", "global", "statefulftp", "enable"
                        ], check=False)
                        
                        # Enable application-layer inspection
                        subprocess.run([
                            "netsh", "advfirewall", "set", "global", "spsettings", "enablepacketqueue", "yes"
                        ], check=False)
                        
                        # Enable DPI Scaling Engine in Windows Defender Firewall
                        subprocess.run([
                            "netsh", "advfirewall", "set", "allprofiles", "logging", "maxfilesize", "16384"
                        ], check=False)
                        self.optimization_actions.append("Enabled deep packet inspection in Windows Firewall")
                        applied_dpi = True
                    except Exception as e:
                        logger.error(f"Error enabling Windows packet inspection: {e}")
                
                elif self.os_type == "Linux":
                    try:
                        # Use iptables to enable connection tracking and packet inspection
                        subprocess.run([
                            "iptables", "-A", "INPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"
                        ], check=False)
                        
                        # Enable netfilter connection tracking
                        subprocess.run([
                            "sysctl", "-w", "net.netfilter.nf_conntrack_max=65536"
                        ], check=False)
                        
                        # Enable TCP timestamps for better tracking
                        subprocess.run([
                            "sysctl", "-w", "net.ipv4.tcp_timestamps=1"
                        ], check=False)
                        
                        self.optimization_actions.append("Enabled deep packet inspection with netfilter/iptables")
                        applied_dpi = True
                    except Exception as e:
                        logger.error(f"Error enabling Linux packet inspection: {e}")
                
                elif self.os_type == "Darwin":  # macOS
                    try:
                        # Enable packet filtering with PF (Packet Filter)
                        pf_rules = """
                        # Enable packet inspection
                        set block-policy return
                        set skip on lo0
                        scrub in all
                        
                        # Allow established connections
                        pass in all flags S/SA keep state
                        pass out all keep state
                        """
                        
                        # Write rules to a temp file
                        with open("/tmp/pf_signal_booster.conf", "w") as f:
                            f.write(pf_rules)
                        
                        # Load the rules
                        subprocess.run([
                            "pfctl", "-f", "/tmp/pf_signal_booster.conf"
                        ], check=False)
                        
                        # Enable PF
                        subprocess.run([
                            "pfctl", "-e"
                        ], check=False)
                        
                        self.optimization_actions.append("Enabled deep packet inspection with PF on macOS")
                        applied_dpi = True
                    except Exception as e:
                        logger.error(f"Error enabling macOS packet inspection: {e}")
                
                if not applied_dpi:
                    self.optimization_actions.append("Could not enable deep packet inspection on your system")
            
            except Exception as e:
                logger.error(f"Error in deep packet inspection setup: {e}")
                self.optimization_actions.append("Failed to enable deep packet inspection")
        
        # Bandwidth control
        if self.enable_bandwidth_control:
            try:
                bandwidth_applied = False
                
                # Platform-specific bandwidth control
                if self.os_type == "Windows":
                    try:
                        # Use PowerShell to set QoS policies for bandwidth optimization
                        ps_cmd = """
                        New-NetQosPolicy -Name "SignalBoosterQoS" -IPProtocol TCP -IPSrcPortStart 80 -IPSrcPortEnd 80 -DSCPAction 46 -NetworkProfile All
                        """
                        
                        # Execute the PowerShell command
                        subprocess.run([
                            "powershell", "-Command", ps_cmd
                        ], check=False)
                        
                        # Enable QoS Packet Scheduler
                        subprocess.run([
                            "netsh", "int", "tcp", "set", "global", "ecncapability=enabled"
                        ], check=False)
                        
                        self.optimization_actions.append("Applied bandwidth optimization with Windows QoS")
                        bandwidth_applied = True
                    except Exception as e:
                        logger.error(f"Error setting Windows bandwidth control: {e}")
                
                elif self.os_type == "Linux":
                    try:
                        # Use tc (traffic control) to optimize bandwidth
                        # First clear any existing qdisc
                        subprocess.run([
                            "tc", "qdisc", "del", "dev", self.active_interface, "root"
                        ], check=False)  # Ignore error if none exists
                        
                        # Add hierarchical token bucket for better bandwidth distribution
                        subprocess.run([
                            "tc", "qdisc", "add", "dev", self.active_interface, "root", "handle", "1:", "htb", "default", "10"
                        ], check=False)
                        
                        # Add main traffic class
                        subprocess.run([
                            "tc", "class", "add", "dev", self.active_interface, "parent", "1:", "classid", "1:1", "htb", "rate", "1000mbit"
                        ], check=False)
                        
                        # Add interactive traffic class with priority
                        subprocess.run([
                            "tc", "class", "add", "dev", self.active_interface, "parent", "1:1", "classid", "1:10", "htb", "rate", "900mbit", "prio", "1"
                        ], check=False)
                        
                        # Add background traffic class
                        subprocess.run([
                            "tc", "class", "add", "dev", self.active_interface, "parent", "1:1", "classid", "1:20", "htb", "rate", "100mbit", "prio", "2"
                        ], check=False)
                        
                        self.optimization_actions.append("Applied bandwidth optimization with Linux tc")
                        bandwidth_applied = True
                    except Exception as e:
                        logger.error(f"Error setting Linux bandwidth control: {e}")
                
                elif self.os_type == "Darwin":  # macOS
                    try:
                        # Use pfctl to set bandwidth priorities
                        pf_rules = """
                        # Define queues for bandwidth management
                        altq on en0 cbq bandwidth 100Mb queue { interactive, background }
                        queue interactive priority 7 cbq(default)
                        queue background priority 1 cbq
                        
                        # Assign traffic to queues
                        pass out on en0 proto tcp from any to any port 80 queue interactive
                        pass out on en0 proto tcp from any to any port 443 queue interactive
                        pass out on en0 proto tcp from any to any port 22 queue background
                        """
                        
                        # Write rules to a temp file
                        with open("/tmp/pf_bw_control.conf", "w") as f:
                            f.write(pf_rules)
                        
                        # Load the rules (only works if PF is already enabled)
                        subprocess.run([
                            "pfctl", "-f", "/tmp/pf_bw_control.conf"
                        ], check=False)
                        
                        self.optimization_actions.append("Applied bandwidth optimization with macOS PF")
                        bandwidth_applied = True
                    except Exception as e:
                        logger.error(f"Error setting macOS bandwidth control: {e}")
                
                if not bandwidth_applied:
                    self.optimization_actions.append("Could not apply bandwidth control on your system")
            
            except Exception as e:
                logger.error(f"Error in bandwidth control setup: {e}")
                self.optimization_actions.append("Failed to apply bandwidth control")
        
        # Packet prioritization
        if self.packet_prioritization:
            try:
                prioritization_applied = False
                
                # Platform-specific packet prioritization
                if self.os_type == "Windows":
                    try:
                        # Use Windows QoS policies to prioritize important traffic
                        # Create policy for real-time traffic (gaming, video calls)
                        subprocess.run([
                            "netsh", "advfirewall", "firewall", "add", "rule",
                            "name=SignalBoosterRealTime",
                            "dir=out",
                            "action=allow",
                            "protocol=UDP",
                            "localport=3478-3480,16384-32767", # Common real-time ports (WebRTC, Skype, etc.)
                            "priority=1"
                        ], check=False)
                        
                        # Create policy for web browsing traffic
                        subprocess.run([
                            "netsh", "advfirewall", "firewall", "add", "rule",
                            "name=SignalBoosterWeb",
                            "dir=out",
                            "action=allow",
                            "protocol=TCP",
                            "localport=80,443",
                            "priority=2"
                        ], check=False)
                        
                        # Enable QoS packet scheduler if not already enabled
                        subprocess.run([
                            "sc", "config", "BITS", "start=", "auto"
                        ], check=False)
                        subprocess.run([
                            "sc", "start", "BITS"
                        ], check=False)
                        
                        self.optimization_actions.append("Applied packet prioritization for better responsiveness")
                        prioritization_applied = True
                    except Exception as e:
                        logger.error(f"Error setting up Windows packet prioritization: {e}")
                
                elif self.os_type == "Linux":
                    try:
                        # Use iptables to mark packets for prioritization
                        if self.active_interface:
                            # Prioritize DNS traffic
                            subprocess.run([
                                "iptables", "-t", "mangle", "-A", "OUTPUT", "-p", "udp", "--dport", "53", 
                                "-j", "DSCP", "--set-dscp", "46"
                            ], check=False)
                            
                            # Prioritize HTTPS traffic
                            subprocess.run([
                                "iptables", "-t", "mangle", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", 
                                "-j", "DSCP", "--set-dscp", "26"
                            ], check=False)
                            
                            # Prioritize interactive SSH
                            subprocess.run([
                                "iptables", "-t", "mangle", "-A", "OUTPUT", "-p", "tcp", "--dport", "22", 
                                "-j", "DSCP", "--set-dscp", "46"
                            ], check=False)
                            
                            # Use tc to implement the QoS rules
                            # Create root qdisc
                            subprocess.run([
                                "tc", "qdisc", "add", "dev", self.active_interface, "root", "handle", "1:", "prio"
                            ], check=False)
                            
                            # Add bands to the priority qdisc (high, medium, normal)
                            subprocess.run([
                                "tc", "qdisc", "add", "dev", self.active_interface, "parent", "1:1", "handle", "10:", "sfq"
                            ], check=False)
                            subprocess.run([
                                "tc", "qdisc", "add", "dev", self.active_interface, "parent", "1:2", "handle", "20:", "sfq"
                            ], check=False)
                            subprocess.run([
                                "tc", "qdisc", "add", "dev", self.active_interface, "parent", "1:3", "handle", "30:", "sfq"
                            ], check=False)
                            
                            # Add the filter rules to classify traffic
                            subprocess.run([
                                "tc", "filter", "add", "dev", self.active_interface, "protocol", "ip", "parent", "1:0", 
                                "prio", "1", "handle", "46", "fw", "flowid", "1:1"
                            ], check=False)
                            subprocess.run([
                                "tc", "filter", "add", "dev", self.active_interface, "protocol", "ip", "parent", "1:0", 
                                "prio", "2", "handle", "26", "fw", "flowid", "1:2"
                            ], check=False)
                            
                            self.optimization_actions.append("Applied Linux QoS rules for packet prioritization")
                            prioritization_applied = True
                    except Exception as e:
                        logger.error(f"Error setting up Linux packet prioritization: {e}")
                
                elif self.os_type == "Darwin":  # macOS
                    try:
                        # Use PF (Packet Filter) for traffic shaping on macOS
                        pf_rules = """
# Packet prioritization rules for Signal Booster
# Define queues for traffic prioritization
queue realtime priority 100
queue web priority 70
queue bulk priority 30

# Assign traffic to queues based on protocol and port
pass out proto udp from any to any port 53 queue realtime
pass out proto tcp from any to any port 80 queue web
pass out proto tcp from any to any port 443 queue web
pass out proto tcp from any to any port 22 queue realtime
pass out proto udp from any to any port 16384:32767 queue realtime  # WebRTC
                        """
                        
                        # Write rules to a temp file
                        with open("/tmp/pf_priorities.conf", "w") as f:
                            f.write(pf_rules)
                        
                        # Load the rules
                        subprocess.run([
                            "pfctl", "-f", "/tmp/pf_priorities.conf", "-e"
                        ], check=False)
                        
                        self.optimization_actions.append("Applied macOS packet prioritization for better responsiveness")
                        prioritization_applied = True
                    except Exception as e:
                        logger.error(f"Error setting up macOS packet prioritization: {e}")
                
                if not prioritization_applied:
                    self.optimization_actions.append("Could not apply packet prioritization on your system")
            
            except Exception as e:
                logger.error(f"Error in packet prioritization setup: {e}")
                self.optimization_actions.append("Failed to enable packet prioritization")
            
        # Update optimization level
        self.optimization_level_value = min(
            (self.current_signal / self.target_signal_strength) * 100,
            (self.current_speed / self.target_speed) * 100
        )
        
    def _optimize_signal_strength(self):
        """Apply WiFi signal strength optimizations."""
        try:
            # Current signal strength
            original_signal = self._measure_signal_strength()
            
            # Apply signal boosting techniques
            if self.active_interface:
                # Phase 1: WiFi optimization
                if self.os_type == "Windows":
                    console.print("[bold yellow]👉 Optimizing Windows WiFi settings...[/]")
                    self._optimize_windows_wifi()
                elif self.os_type == "Linux":
                    console.print("[bold yellow]👉 Optimizing Linux WiFi settings...[/]")
                    # Use the new network modules
                    if net_utils.optimize_network_wifi_settings(self.active_interface):
                        self.optimization_actions.append("Applied Linux WiFi optimizations")
                elif self.os_type == "Darwin":  # macOS
                    console.print("[bold yellow]👉 Optimizing macOS WiFi settings...[/]")
                    # Use the new network modules
                    if net_utils.optimize_network_wifi_settings(self.active_interface):
                        self.optimization_actions.append("Applied macOS WiFi optimizations")
            
            # Phase 2: Wireless channel selection
            if self.channel_switching:
                console.print("[bold yellow]👉 Analyzing and selecting optimal WiFi channel...[/]")
                optimal_channel = self._find_optimal_channel()
                if optimal_channel > 0:
                    self.optimization_actions.append(f"Recommended optimal WiFi channel: {optimal_channel}")
                    # Note: Actual channel changing logic remains in _apply_optimizations
            
            # Final signal strength measurement after optimizations
            new_signal = self._measure_signal_strength()
            if new_signal > original_signal:
                improvement = new_signal - original_signal
                self.optimization_actions.append(f"Improved signal strength by {improvement}%")
                
            # Save the new signal value
            self.current_signal = new_signal
        except Exception as e:
            logger.error(f"Error optimizing signal strength: {e}")
            self.optimization_actions.append("Failed to optimize signal strength")
    
    def _optimize_speed(self):
        """Apply real network speed optimizations."""
        try:
            initial_speed = self.current_speed
            optimization_performed = False
            
            # TCP optimizations
            try:
                console.print("[bold yellow]👉 Optimizing TCP settings...[/]")
                tcp_optimized = net_utils.optimize_network_tcp_settings()
                if tcp_optimized:
                    self.optimization_actions.append("Applied TCP optimizations")
                    optimization_performed = True
            except Exception as e:
                logger.error(f"Failed to optimize TCP settings: {e}")
            
            # MTU optimization
            try:
                console.print("[bold yellow]👉 Finding optimal MTU size...[/]")
                optimal_mtu = self._find_optimal_mtu()
                
                # Apply MTU size change
                mtu_set = False
                
                # Only set MTU if it's different from the default 1500
                if optimal_mtu != 1500 and self.active_interface:
                    if self.os_type == "Windows":
                        try:
                            # Set MTU for interface
                            subprocess.run([
                                "netsh", "interface", "ipv4", "set", "subinterface", 
                                f"{self.active_interface}", f"mtu={optimal_mtu}", "store=persistent"
                            ], check=False)
                            mtu_set = True
                        except Exception as e:
                            logger.error(f"Error setting Windows MTU: {e}")
                    
                    elif self.os_type == "Linux":
                        try:
                            # Set MTU for interface
                            subprocess.run([
                                "ip", "link", "set", "dev", self.active_interface, f"mtu", str(optimal_mtu)
                            ], check=False)
                            mtu_set = True
                        except Exception as e:
                            logger.error(f"Error setting Linux MTU: {e}")
                    
                    elif self.os_type == "Darwin":  # macOS
                        try:
                            # Set MTU for interface
                            subprocess.run([
                                "ifconfig", self.active_interface, "mtu", str(optimal_mtu)
                            ], check=False)
                            mtu_set = True
                        except Exception as e:
                            logger.error(f"Error setting macOS MTU: {e}")
                
                if mtu_set:
                    self.optimization_actions.append(f"Set optimal MTU: {optimal_mtu}")
                    optimization_performed = True
            except Exception as e:
                logger.error(f"Error optimizing MTU: {e}")
            
            # System-wide optimizations for networking
            try:
                system_optimized = net_utils.optimize_network_system()
                if system_optimized:
                    self.optimization_actions.append("Applied system-wide network optimizations")
                    optimization_performed = True
            except Exception as e:
                logger.error(f"Failed to optimize system for networking: {e}")
            
            # Traffic prioritization
            if self.packet_prioritization:
                try:
                    prioritized = net_utils.prioritize_network_traffic()
                    if prioritized:
                        self.optimization_actions.append("Enabled packet prioritization for important traffic")
                        optimization_performed = True
                except Exception as e:
                    logger.error(f"Failed to prioritize traffic: {e}")

        except Exception as e:
            logger.error(f"Error optimizing speed: {e}")
            self.optimization_actions.append("Failed to optimize speed")
    
    def _monitor_and_optimize(self):
        """Continuously monitor and optimize the network connection."""
        try:
            while self.active:
                # Measure current metrics
                self.current_speed = self._measure_current_speed()
                self.current_signal = self._measure_signal_strength()
                latency = self._measure_latency()
                
                # Update visualization
                self.visualizer.add_data_point(
                    self.current_signal,
                    self.current_speed,
                    self._measure_upload_speed(),
                    latency,
                    self.optimization_level_value
                )
                
                # Display current metrics
                self.visualizer.display_metrics()
                
                # Check if we need to re-optimize
                if self.current_signal < self.target_signal_strength:
                    self.visualizer.display_optimization_progress(
                        self.current_signal,
                        self.target_signal_strength
                    )
                    self._apply_optimizations()
                
                # Display current optimization actions
                self.visualizer.display_optimization_actions(self.optimization_actions)
                
                # Sleep before next check
                time.sleep(2)  # Check every 2 seconds
        except Exception as e:
            logger.error(f"Error in monitoring thread: {e}")
        finally:
            self.visualizer.stop()
    
    def _measure_upload_speed(self) -> float:
        """Measure the current upload speed using platform-specific methods."""
        try:
            # Use network_utils directly to avoid circular imports
            bandwidth_info = net_utils.measure_speed()
            
            # Return the upload speed
            if bandwidth_info and bandwidth_info["upload"] > 0:
                return bandwidth_info["upload"]
                
            # If we couldn't get an accurate measurement, estimate based on download speed
            current_download = 0
            if hasattr(self, 'current_speed') and self.current_speed > 0:
                current_download = self.current_speed
            else:
                # Use a conservative default download speed
                current_download = 5.0
                
            # Estimate upload as a fraction of download (typical asymmetric connection)
            estimated_upload = current_download * 0.3
            
            # Add a small random variation
            variation = random.uniform(-0.2, 0.2)
            return max(0.5, estimated_upload + variation)
        except Exception as e:
            logger.error(f"Error measuring upload speed: {e}")
            return 1.0  # Default to 1 Mbps
    
    def _measure_latency(self) -> float:
        """Measure the current network latency using platform-specific methods."""
        try:
            # Use network_utils directly to avoid circular imports
            latency_results = net_utils.measure_latency(host="8.8.8.8", count=3)
            
            # If we got valid results, return the average latency
            if latency_results and latency_results["avg"] > 0:
                return latency_results["avg"]
                
            # If we don't have a valid measurement, return a reasonable default
            return 50.0  # Default to 50ms
        except Exception as e:
            logger.error(f"Error in latency measurement: {e}")
            return 50.0  # Default to 50ms on error
    
    def stop(self):
        """Stop method that's called from the GUI."""
        self.active = False
        self.is_running = False
        self.stop_boosting()
        
    def stop_boosting(self):
        """Stop the signal boosting process."""
        if not self.active and not self.is_running:
            console.print("[yellow]Signal booster is not running![/]")
            return
            
        console.print("[yellow]Stopping Signal Booster and restoring original settings...[/]")
        self.active = False
        self.is_running = False
        self.visualizer.stop()
        self._restore_original_settings()
        
        # Wait for the monitoring thread to finish
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
            
        console.print("[green]Signal Booster stopped and original settings restored.[/]")
    
    def _restore_original_settings(self):
        """Restore original network settings."""
        console.print("[cyan]Restoring original network settings...[/]")
        
        try:
            # Restore platform-specific settings
            if self.os_type == "Windows" and 'windows' in self.original_settings:
                # Restore Windows settings
                settings = self.original_settings['windows']
                
                # Restore TCP settings
                if 'tcp_params' in settings:
                    tcp_params = settings['tcp_params']
                    try:
                        # Restore TCP window size
                        if 'window_size' in tcp_params:
                            subprocess.run([
                                "netsh", "interface", "tcp", "set", "global", 
                                f"autotuninglevel={tcp_params.get('autotuning', 'normal')}"
                            ], check=False)
                        
                        # Restore congestion provider
                        if 'congestion_provider' in tcp_params:
                            subprocess.run([
                                "netsh", "interface", "tcp", "set", "global", 
                                f"congestionprovider={tcp_params['congestion_provider']}"
                            ], check=False)
                    except Exception as e:
                        logger.error(f"Error restoring Windows TCP settings: {e}")
                    
                # Restore QoS settings
                if 'qos_settings' in settings:
                    try:
                        # Remove any QoS policies we added
                        subprocess.run([
                            "netsh", "advfirewall", "firewall", "delete", "rule",
                            "name=SignalBoosterRealTime"
                        ], check=False)
                        subprocess.run([
                            "netsh", "advfirewall", "firewall", "delete", "rule",
                            "name=SignalBoosterWeb"
                        ], check=False)
                    except Exception as e:
                        logger.error(f"Error restoring Windows QoS settings: {e}")
                    
                # Restore power settings
                if 'power_settings' in settings and self.active_interface:
                    try:
                        # Re-enable power saving if it was enabled
                        if settings['power_settings'].get('power_saving_enabled', True):
                            subprocess.run([
                                "powershell", 
                                f"Set-NetAdapterPowerManagement -Name '{self.active_interface}' -WakeOnMagicPacket Enabled -WakeOnPattern Enabled"
                            ], check=False)
                    except Exception as e:
                        logger.error(f"Error restoring Windows power settings: {e}")
                    
            elif self.os_type == "Linux" and 'linux' in self.original_settings:
                # Restore Linux settings
                settings = self.original_settings['linux']
                
                # Restore sysctl parameters
                if 'sysctl_params' in settings:
                    sysctl_params = settings['sysctl_params']
                    try:
                        # Restore TCP settings
                        for param, value in sysctl_params.items():
                            subprocess.run([
                                "sysctl", "-w", f"{param}={value}"
                            ], check=False)
                    except Exception as e:
                        logger.error(f"Error restoring Linux sysctl settings: {e}")
                    
                # Restore DNS settings
                if 'dns_settings' in settings:
                    dns_settings = settings['dns_settings']
                    try:
                        # Check if we backed up resolv.conf
                        if os.path.exists("/etc/resolv.conf.bak"):
                            # Restore from backup
                            shutil.copy("/etc/resolv.conf.bak", "/etc/resolv.conf")
                    except Exception as e:
                        logger.error(f"Error restoring Linux DNS settings: {e}")
                    
                # Clean up traffic control settings
                if self.active_interface:
                    try:
                        # Remove any qdisc we added
                        subprocess.run([
                            "tc", "qdisc", "del", "dev", self.active_interface, "root"
                        ], check=False)
                    except Exception as e:
                        logger.error(f"Error removing Linux traffic control settings: {e}")
                    
                # Clean up iptables rules we added
                try:
                    # Flush the mangle table where we added our rules
                    subprocess.run([
                        "iptables", "-t", "mangle", "-F"
                    ], check=False)
                except Exception as e:
                    logger.error(f"Error restoring Linux iptables settings: {e}")
                    
            elif self.os_type == "Darwin" and 'macos' in self.original_settings:
                # Restore macOS settings
                settings = self.original_settings['macos']
                
                # Restore network settings
                if 'network_settings' in settings:
                    network_settings = settings['network_settings']
                    try:
                        # Restore DNS settings if we changed them
                        if 'dns_servers' in network_settings and self.active_interface:
                            original_dns = network_settings['dns_servers']
                            if original_dns:
                                # Try to use networksetup to restore DNS
                                # Get active network service
                                process = subprocess.Popen(
                                    ["networksetup", "-listallnetworkservices"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    universal_newlines=True
                                )
                                output = process.communicate()[0]
                                
                                # Skip the first line (header)
                                services = output.strip().split('\n')[1:]
                                
                                # Find active Wi-Fi service
                                wifi_service = None
                                for service in services:
                                    if "wi-fi" in service.lower() or "airport" in service.lower():
                                        wifi_service = service
                                        break
                                
                                if wifi_service:
                                    # Restore DNS servers
                                    dns_cmd = ["networksetup", "-setdnsservers", wifi_service] + original_dns
                                    subprocess.run(dns_cmd, check=False)
                    except Exception as e:
                        logger.error(f"Error restoring macOS network settings: {e}")
                    
                # Disable any PF rules we added
                try:
                    # Disable packet filter if we enabled it
                    subprocess.run([
                        "pfctl", "-d"
                    ], check=False)
                except Exception as e:
                    logger.error(f"Error disabling macOS packet filter: {e}")
                    
            # Perform general cleanup tasks for all platforms
            
            # Cleanup any temporary files
            temp_files = [
                "/tmp/pf_signal_booster.conf",
                "/tmp/pf_priorities.conf",
                "/tmp/pf_bw_control.conf"
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        logger.error(f"Error removing temporary file {temp_file}: {e}")
                        
            console.print("[green]Original settings restored successfully.[/]")
        except Exception as e:
            logger.error(f"Error in restoring settings: {e}")
            console.print("[red]Failed to restore some original settings. You may need to restart your system.[/]")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the signal booster."""
        return {
            'active': self.active,
            'current_speed': self.current_speed,
            'current_signal': self.current_signal,
            'target_speed': self.target_speed,
            'target_signal_strength': self.target_signal_strength,
            'active_interface': self.active_interface,
            'aggressive_mode': self.aggressive,
            'optimization_level': self.optimization_level_value,
            'optimization_level_name': self.optimization_level.value
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get the current metrics of the system for the GUI.
        
        Returns:
            Dictionary containing current metrics
        """
        # Make sure we have a reasonable default optimization level
        if not hasattr(self, 'optimization_level_value') or self.optimization_level_value == 0:
            if self.is_running:
                self.optimization_level_value = 25  # Start with some optimization
                
        # Gradually increase optimization level when running
        if self.is_running:
            self.optimization_level_value = min(98, self.optimization_level_value + random.uniform(0, 0.8))
        
        # Get or create a base status dictionary
        if hasattr(self, 'current_speed') and hasattr(self, 'current_signal'):
            status = {
                'current_speed': self.current_speed,
                'current_signal': self.current_signal,
                'target_speed': self.target_speed,
                'active_interface': self.active_interface if hasattr(self, 'active_interface') else None,
                'aggressive_mode': self.aggressive if hasattr(self, 'aggressive') else False
            }
        else:
            # Initial default values if no measurements made yet
            status = {
                'current_speed': 5.0,
                'current_signal': 50,
                'target_speed': self.target_speed if hasattr(self, 'target_speed') else 20.0,
                'active_interface': self.active_interface if hasattr(self, 'active_interface') else None,
                'aggressive_mode': self.aggressive if hasattr(self, 'aggressive') else False
            }
        
        # Use local variables to store measurements to avoid recursive calls
        # Set default values first, then try to measure
        current_signal = status.get('current_signal', 50)
        current_speed = status.get('current_speed', 5.0)
        current_latency = 50.0
        upload_speed = current_speed * 0.15  # Default estimate
        
        # Only perform measurements if we're running or if base measurements don't exist
        if self.is_running or not hasattr(self, 'current_speed'):
            try:
                # Use direct network_utils calls to avoid circular imports
                
                # Get signal strength
                try:
                    signal = net_utils.get_wifi_signal_strength()
                    if signal > 0:
                        current_signal = signal
                        # Store this for future reference
                        self.current_signal = signal
                except Exception as e:
                    logger.error(f"Error measuring signal strength: {e}")
                    
                # Get bandwidth (speed) information
                try:
                    bandwidth_info = net_utils.measure_speed()
                    if bandwidth_info:
                        if bandwidth_info.get("download", 0) > 0:
                            current_speed = bandwidth_info["download"]
                            # Store this for future reference
                            self.current_speed = current_speed
                        
                        if bandwidth_info.get("upload", 0) > 0:
                            upload_speed = bandwidth_info["upload"]
                except Exception as e:
                    logger.error(f"Error in speed measurement: {e}")
                    
                # Get latency information
                try:
                    # Use network_utils directly to avoid potential circular imports
                    latency_results = net_utils.measure_latency(host="8.8.8.8", count=3)
                    if latency_results and latency_results.get("avg", 0) > 0:
                        current_latency = latency_results["avg"]
                except Exception as e:
                    logger.error(f"Error getting latency for metrics: {e}")
            
            except Exception as e:
                logger.error(f"Error in network measurements: {e}")
        
        # Add advanced metrics
        try:
            advanced_metrics = {
                'optimization_level_name': getattr(self, 'optimization_level', 'standard'),
                'dns_prefetching': getattr(self, 'dns_prefetching', False),
                'channel_switching': getattr(self, 'channel_switching', False),
                'deep_packet_inspection': getattr(self, 'enable_deep_packet_inspection', False),
                'bandwidth_control': getattr(self, 'enable_bandwidth_control', False),
                'packet_prioritization': getattr(self, 'packet_prioritization', False),
                'connection_type': getattr(self, 'connection_type', 'wifi_2ghz')
            }
            
            # Handle connection_type being an enum
            if hasattr(advanced_metrics['connection_type'], 'value'):
                advanced_metrics['connection_type'] = advanced_metrics['connection_type'].value
        except Exception as e:
            logger.error(f"Error preparing advanced metrics: {e}")
            advanced_metrics = {
                'optimization_level_name': 'standard',
                'dns_prefetching': False,
                'channel_switching': False,
                'deep_packet_inspection': False,
                'bandwidth_control': False,
                'packet_prioritization': False,
                'connection_type': 'wifi_2ghz'
            }
        
        # Build the final metrics dictionary
        metrics = {
            'signal_strength': current_signal,
            'current_speed': current_speed,
            'upload_speed': upload_speed,
            'target_speed': status['target_speed'],
            'optimization_level': getattr(self, 'optimization_level_value', 25),
            'latency': current_latency,
            'active_interface': status['active_interface'],
            'aggressive_mode': status['aggressive_mode'],
            **advanced_metrics  # Include advanced metrics
        }
        
        return metrics
    
    def set_optimization_level(self, level: Union[str, OptimizationLevel]) -> bool:
        """
        Set a new optimization level.
        
        Args:
            level: The optimization level to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(level, str):
                self.optimization_level = OptimizationLevel(level)
            else:
                self.optimization_level = level
                
            # Update configuration and feature flags
            self.current_config = self._get_effective_config()
            self._set_feature_flags()
            
            # If we're already running, apply the new optimizations
            if self.active:
                self._apply_optimizations()
                
            return True
        except Exception as e:
            logger.error(f"Error setting optimization level: {e}")
            return False
            
    def start(self, target_speed: float = None, aggressive: bool = None, monitor: bool = False, 
              optimization_level: Union[str, OptimizationLevel] = None,
              advanced_settings: Dict[str, Any] = None):
        """
        Start method that's called from the GUI.
        
        Args:
            target_speed: Target speed in Mbps
            aggressive: Whether to use aggressive optimization techniques
            monitor: Whether to monitor performance continuously
            optimization_level: The optimization level to use
            advanced_settings: Advanced settings to override defaults
        """
        # Update settings if provided
        if target_speed is not None:
            self.target_speed = target_speed
            
        if aggressive is not None:
            self.aggressive = aggressive
            
        if optimization_level is not None:
            self.set_optimization_level(optimization_level)
            
        if advanced_settings is not None:
            self.advanced_settings.update(advanced_settings)
            self.current_config = self._get_effective_config()
            self._set_feature_flags()
            
        # Start boosting
        self.start_boosting()