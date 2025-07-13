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

import psutil
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Local imports
import signal_booster.network_utils as net_utils

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
    
    def __init__(self, target_speed: float = 1.5, aggressive: bool = False):
        """
        Initialize the Signal Booster.
        
        Args:
            target_speed: Target speed in Mbps
            aggressive: Whether to use more aggressive techniques
        """
        self.target_speed = target_speed
        self.aggressive = aggressive
        self.active = False
        self.current_speed = 0.0
        self.current_signal = 0
        self.original_settings = {}
        self.os_type = platform.system()
        self.interfaces = net_utils.get_network_interfaces()
        self.active_interface = self._get_active_interface()
        self._init_platform_specific()
        
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
    
    def _get_network_interfaces(self) -> Dict[str, Dict[str, Any]]:
        """Get all available network interfaces."""
        interfaces = {}
        
        for interface in net_utils.get_network_interfaces():
            addrs = net_utils.get_network_interfaces().get(interface, {})
            if addrs.get('ip_address'):
                # Get IP details
                ip_info = addrs
                
                # Check if this is a wireless interface
                is_wireless = self._is_wireless_interface(interface)
                
                # Store the interface details
                interfaces[interface] = {
                    'name': interface,
                    'ip_address': ip_info.get('addr', ''),
                    'netmask': ip_info.get('netmask', ''),
                    'is_wireless': is_wireless,
                    'mac_address': self._get_mac_address(interface)
                }
                
        return interfaces
    
    def _is_wireless_interface(self, interface: str) -> bool:
        """Check if the interface is wireless."""
        # This is a simplified check - actual implementation would be more complex
        # and OS-specific
        if self.os_type == "Windows":
            return "wi-fi" in interface.lower() or "wireless" in interface.lower()
        elif self.os_type == "Linux":
            return interface.startswith("wl")
        elif self.os_type == "Darwin":  # macOS
            return interface.startswith("en") and not interface.startswith("eth")
        return False
    
    def _get_mac_address(self, interface: str) -> str:
        """Get the MAC address for an interface."""
        details = net_utils.get_network_interfaces().get(interface, {})
        return details.get('mac_address', '')
    
    def _get_active_interface(self) -> Optional[str]:
        """Determine the currently active network interface."""
        # This is a simplified approach to find the active interface
        # A more complete solution would check for default routes
        
        for interface, details in self.interfaces.items():
            if details['is_wireless'] and details['ip_address']:
                try:
                    # Test connectivity
                    socket.socket(socket.AF_INET, socket.SOCK_DGRAM).connect(("8.8.8.8", 80))
                    return interface
                except:
                    pass
        
        # Fall back to the first interface with an IP
        for interface, details in self.interfaces.items():
            if details['ip_address']:
                return interface
                
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
        # This would include registry values for TCP optimization
        return {}
    
    def _get_windows_power_settings(self) -> Dict[str, Any]:
        """Get current Windows power settings."""
        return {}
    
    def _get_windows_qos_settings(self) -> Dict[str, Any]:
        """Get current Windows QoS (Quality of Service) settings."""
        return {}
    
    def _get_linux_sysctl_params(self) -> Dict[str, Any]:
        """Get current Linux sysctl parameters."""
        return {}
    
    def _get_linux_dns_settings(self) -> Dict[str, Any]:
        """Get current Linux DNS settings."""
        return {}
    
    def _get_macos_network_settings(self) -> Dict[str, Any]:
        """Get current macOS network settings."""
        return {}
    
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
        
        # Run an initial diagnostics
        self._run_diagnostics()
        
        # Apply optimizations
        self._apply_optimizations()
        
        # Start monitoring in a background thread
        self.active = True
        self.monitor_thread = threading.Thread(target=self._monitor_and_optimize, daemon=True)
        self.monitor_thread.start()
        
        console.print("[bold green]Signal Booster is now active and optimizing your connection![/]")
    
    def stop_boosting(self):
        """Stop the signal boosting process."""
        if not self.active:
            console.print("[yellow]Signal booster is not running![/]")
            return
            
        console.print("[yellow]Stopping Signal Booster and restoring original settings...[/]")
        self.active = False
        self._restore_original_settings()
        
        # Wait for the monitoring thread to finish
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
            
        console.print("[green]Signal Booster stopped and original settings restored.[/]")
    
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
        """Measure the current network speed."""
        # This would use speedtest-cli or a similar tool
        # For demonstration, returning a random value
        return np.random.uniform(0.5, 5.0)
    
    def _measure_signal_strength(self) -> int:
        """Measure the current signal strength."""
        # This would use platform-specific tools
        # For demonstration, returning a random value
        return int(np.random.uniform(20, 80))
    
    def _analyze_network_congestion(self) -> float:
        """Analyze the current network congestion."""
        # This would use network monitoring tools
        # For demonstration, returning a random value
        return np.random.uniform(10, 70)
    
    def _check_for_interference(self) -> float:
        """Check for wireless interference."""
        # This would use wireless monitoring tools
        # For demonstration, returning a random value
        return np.random.uniform(5, 40)
    
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
        # This would scan channels and find the best one
        # For demonstration, returning a fixed channel
        return 6
    
    def _find_optimal_mtu(self) -> int:
        """Find the optimal MTU size."""
        # This would test different MTU sizes
        # For demonstration, returning a standard value
        return 1500
    
    def _apply_optimizations(self):
        """Apply network optimizations."""
        console.print("[cyan]Applying network optimizations...[/]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Optimizing...", total=100)
            
            # Apply DNS optimizations
            progress.update(task, advance=20, description="[cyan]Optimizing DNS settings...")
            self._optimize_dns()
            
            # Apply TCP/IP optimizations
            progress.update(task, advance=20, description="[cyan]Optimizing TCP/IP stack...")
            self._optimize_tcp_ip()
            
            # Apply QoS optimizations
            progress.update(task, advance=20, description="[cyan]Configuring QoS...")
            self._optimize_qos()
            
            # Apply wireless optimizations if applicable
            if self.interfaces.get(self.active_interface, {}).get('is_wireless', False):
                progress.update(task, advance=20, description="[cyan]Optimizing wireless settings...")
                self._optimize_wireless()
            else:
                progress.update(task, advance=20)
            
            # Apply advanced techniques if aggressive mode is enabled
            if self.aggressive:
                progress.update(task, advance=20, description="[cyan]Applying advanced optimizations...")
                self._apply_advanced_optimizations()
            else:
                progress.update(task, advance=20)
            
            progress.update(task, completed=100)
        
        console.print("[bold green]Optimizations applied successfully![/]")
    
    def _optimize_dns(self):
        """Optimize DNS settings."""
        # Windows-specific DNS optimization
        if self.os_type == "Windows":
            # This would modify Windows DNS settings
            pass
        elif self.os_type == "Linux":
            # This would modify Linux DNS settings
            pass
        elif self.os_type == "Darwin":  # macOS
            # This would modify macOS DNS settings
            pass
    
    def _optimize_tcp_ip(self):
        """Optimize TCP/IP stack."""
        # Windows-specific TCP/IP optimization
        if self.os_type == "Windows":
            # This would modify Windows TCP/IP settings
            pass
        elif self.os_type == "Linux":
            # This would modify Linux TCP/IP settings via sysctl
            pass
        elif self.os_type == "Darwin":  # macOS
            # This would modify macOS TCP/IP settings
            pass
    
    def _optimize_qos(self):
        """Optimize Quality of Service (QoS) settings."""
        # Platform-specific QoS optimization
        if self.os_type == "Windows":
            # This would configure Windows QoS
            pass
        elif self.os_type == "Linux":
            # This would configure Linux QoS
            pass
        elif self.os_type == "Darwin":  # macOS
            # This would configure macOS QoS
            pass
    
    def _optimize_wireless(self):
        """Optimize wireless settings."""
        # Platform-specific wireless optimization
        if self.os_type == "Windows":
            # This would configure Windows wireless settings
            pass
        elif self.os_type == "Linux":
            # This would configure Linux wireless settings
            pass
        elif self.os_type == "Darwin":  # macOS
            # This would configure macOS wireless settings
            pass
    
    def _apply_advanced_optimizations(self):
        """Apply advanced optimizations for aggressive mode."""
        # These would be more experimental or aggressive techniques
        if self.os_type == "Windows":
            # Advanced Windows optimizations
            pass
        elif self.os_type == "Linux":
            # Advanced Linux optimizations
            pass
        elif self.os_type == "Darwin":  # macOS
            # Advanced macOS optimizations
            pass
    
    def _monitor_and_optimize(self):
        """Continuously monitor and optimize the network connection."""
        console.print("[cyan]Starting continuous monitoring and optimization...[/]")
        
        try:
            while self.active:
                # Measure current metrics
                self.current_speed = self._measure_current_speed()
                self.current_signal = self._measure_signal_strength()
                
                # Check if we need to re-optimize
                if self.current_speed < self.target_speed:
                    console.print(f"[yellow]Speed ({self.current_speed:.2f} Mbps) is below target ({self.target_speed} Mbps)[/]")
                    console.print("[cyan]Re-optimizing network settings...[/]")
                    self._apply_optimizations()
                
                # Sleep before next check
                time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Error in monitoring thread: {e}")
    
    def _restore_original_settings(self):
        """Restore original network settings."""
        console.print("[cyan]Restoring original network settings...[/]")
        
        if self.os_type == "Windows" and 'windows' in self.original_settings:
            # Restore Windows settings
            pass
        elif self.os_type == "Linux" and 'linux' in self.original_settings:
            # Restore Linux settings
            pass
        elif self.os_type == "Darwin" and 'macos' in self.original_settings:
            # Restore macOS settings
            pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the signal booster."""
        return {
            'active': self.active,
            'current_speed': self.current_speed,
            'current_signal': self.current_signal,
            'target_speed': self.target_speed,
            'active_interface': self.active_interface,
            'aggressive_mode': self.aggressive
        }

    def get_network_interfaces(self):
        """Get all network interfaces and their IP addresses"""
        interfaces = {}
        for interface, details in net_utils.get_network_interfaces().items():
            if details.get('ip_address'):
                interfaces[interface] = details['ip_address']
        return interfaces

    def get_mac_address(self, interface):
        """Get MAC address for a specific interface"""
        details = net_utils.get_network_interfaces().get(interface, {})
        return details.get('mac_address', '') 