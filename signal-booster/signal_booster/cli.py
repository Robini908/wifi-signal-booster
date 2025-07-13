"""
Command-line interface for Signal Booster.
This module provides the main entry point for the application.
"""

import os
import sys
import time
import logging
import platform
import argparse
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.align import Align

from signal_booster.core import SignalBooster
import signal_booster.network_utils as net_utils

# Setup console and logger
console = Console()
logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def show_welcome():
    """Display welcome message."""
    console.print(Panel.fit(
        "[bold blue]Signal Booster[/] [yellow]v1.0.0[/]\n"
        "[cyan]Advanced Network Signal & Speed Optimization Suite[/]",
        title="Welcome", 
        border_style="green",
        padding=(1, 2)
    ))
    
    console.print("[yellow]DISCLAIMER: This software attempts to optimize network settings for better performance. "
                 "It requires administrative privileges to function properly. Use at your own risk.[/]")
    console.print()

def check_admin_privileges() -> bool:
    """Check if the script is running with admin privileges."""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:  # Linux/macOS
            return os.geteuid() == 0
    except:
        return False

def display_system_info():
    """Display system information."""
    table = Table(title="System Information")
    
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Operating System", platform.system() + " " + platform.version())
    table.add_row("Python Version", platform.python_version())
    
    # Network interfaces
    network_interfaces = []
    interfaces = net_utils.get_network_interfaces()
    
    for interface, details in interfaces.items():
        if details.get('ip_address'):
            network_interfaces.append(f"{interface}: {details['ip_address']}")
    
    table.add_row("Network Interfaces", "\n".join(network_interfaces))
    
    # Default gateway
    gateway = net_utils.get_default_gateway()
    if gateway:
        table.add_row("Default Gateway", gateway)
    
    console.print(table)
    console.print()

def monitor_dashboard(booster: SignalBooster):
    """Display a live monitoring dashboard."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3)
    )
    
    layout["header"].update(
        Panel.fit(
            "[bold blue]Signal Booster[/] - Live Monitoring",
            border_style="green"
        )
    )
    
    layout["footer"].update(
        Panel.fit(
            "Press Ctrl+C to stop monitoring",
            border_style="yellow"
        )
    )
    
    try:
        with Live(layout, refresh_per_second=1, screen=True) as live:
            while booster.active:
                # Create status table
                table = Table(title="Network Status")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                status = booster.get_status()
                
                table.add_row("Current Speed", f"{status['current_speed']:.2f} Mbps")
                table.add_row("Target Speed", f"{status['target_speed']:.2f} Mbps")
                table.add_row("Signal Strength", booster._signal_strength_to_text(status['current_signal']))
                table.add_row("Active Interface", status['active_interface'] or "None")
                table.add_row("Aggressive Mode", "Enabled" if status['aggressive_mode'] else "Disabled")
                
                # Add latency information
                try:
                    latency = net_utils.measure_latency()
                    table.add_row("Ping (min/avg/max)", f"{latency['min']:.1f}/{latency['avg']:.1f}/{latency['max']:.1f} ms")
                except:
                    pass
                
                # Update the layout
                layout["main"].update(Align.center(table))
                
                # Sleep for a second
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        console.print("[yellow]Monitoring stopped.[/]")

@click.group()
@click.option('--verbose', '-v', is_flag=True, help="Enable verbose logging")
def cli(verbose):
    """Signal Booster - Advanced Network Signal & Speed Optimization Suite"""
    setup_logging(verbose)
    show_welcome()

@cli.command()
@click.option('--target-speed', '-t', type=float, default=1.5, help="Target speed in Mbps")
@click.option('--aggressive', '-a', is_flag=True, help="Enable aggressive optimization techniques")
@click.option('--monitor', '-m', is_flag=True, help="Show live monitoring dashboard")
def start(target_speed, aggressive, monitor):
    """Start the signal boosting process"""
    # Check admin privileges
    if not check_admin_privileges():
        console.print("[bold red]Error:[/] Administrative privileges required to optimize network settings.")
        console.print("[yellow]Please run this script as administrator (Windows) or root (Linux/macOS).[/]")
        return
    
    # Display system info
    display_system_info()
    
    # Create and start the booster
    booster = SignalBooster(target_speed=target_speed, aggressive=aggressive)
    
    # Start boosting
    booster.start_boosting()
    
    # Show monitoring dashboard if requested
    if monitor:
        monitor_dashboard(booster)
    else:
        try:
            console.print("[cyan]Signal Booster is running in the background. Press Ctrl+C to stop.[/]")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            booster.stop_boosting()

@cli.command()
def test():
    """Run a network diagnostic test"""
    console.print("[cyan]Running network diagnostic test...[/]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Test latency
        task = progress.add_task("[cyan]Testing latency...", total=None)
        latency = net_utils.measure_latency()
        progress.update(task, completed=True, description="[green]Latency test completed")
        
        # Test speed
        task = progress.add_task("[cyan]Testing internet speed...", total=None)
        speed = net_utils.measure_speed()
        progress.update(task, completed=True, description="[green]Speed test completed")
        
        # Check for malware
        task = progress.add_task("[cyan]Checking for malware...", total=None)
        malware_found, malware_issues = net_utils.check_for_malware()
        progress.update(task, completed=True, description="[green]Malware check completed")
        
        # Check network drivers
        task = progress.add_task("[cyan]Checking network drivers...", total=None)
        drivers_ok, driver_issues = net_utils.check_network_drivers()
        progress.update(task, completed=True, description="[green]Driver check completed")
    
    # Display results
    console.print()
    console.print("[bold cyan]Diagnostic Results:[/]")
    
    # Speed and latency
    table = Table(title="Network Performance")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Download Speed", f"{speed['download']:.2f} Mbps")
    table.add_row("Upload Speed", f"{speed['upload']:.2f} Mbps")
    table.add_row("Ping", f"{speed['ping']:.2f} ms")
    table.add_row("Latency (min/avg/max)", f"{latency['min']:.1f}/{latency['avg']:.1f}/{latency['max']:.1f} ms")
    
    console.print(table)
    console.print()
    
    # Issues
    if malware_found or not drivers_ok:
        issues_table = Table(title="Issues Detected")
        issues_table.add_column("Issue Type", style="red")
        issues_table.add_column("Description", style="yellow")
        
        if malware_found:
            for issue in malware_issues:
                issues_table.add_row("Potential Malware", issue)
        
        if not drivers_ok:
            for issue in driver_issues:
                issues_table.add_row("Driver Issue", issue)
        
        console.print(issues_table)
        console.print()
    else:
        console.print("[green]No issues detected.[/]")

@cli.command()
def info():
    """Display system and network information"""
    display_system_info()
    
    # Show more detailed network info
    console.print("[cyan]Checking network status...[/]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Gathering information...", total=None)
        time.sleep(1)  # Simulate work
        
        # Gather information
        wifi_signal = net_utils.get_wifi_signal_strength()
        latency = net_utils.measure_latency()
        
        progress.update(task, completed=True)
    
    # Show WiFi info if available
    if wifi_signal > 0:
        wifi_table = Table(title="WiFi Information")
        wifi_table.add_column("Property", style="cyan")
        wifi_table.add_column("Value", style="green")
        
        # Signal strength
        signal_text = "Excellent" if wifi_signal >= 75 else "Good" if wifi_signal >= 50 else "Fair" if wifi_signal >= 30 else "Poor"
        wifi_table.add_row("Signal Strength", f"{wifi_signal}% ({signal_text})")
        
        # Optimal channel
        optimal_channel = net_utils.find_best_wifi_channel()
        wifi_table.add_row("Optimal Channel", str(optimal_channel))
        
        console.print(wifi_table)
        console.print()
    
    # Show latency info
    latency_table = Table(title="Network Latency")
    latency_table.add_column("Metric", style="cyan")
    latency_table.add_column("Value", style="green")
    
    latency_table.add_row("Minimum Latency", f"{latency['min']:.1f} ms")
    latency_table.add_row("Average Latency", f"{latency['avg']:.1f} ms")
    latency_table.add_row("Maximum Latency", f"{latency['max']:.1f} ms")
    
    # Latency quality assessment
    if latency['avg'] < 20:
        latency_quality = "Excellent"
    elif latency['avg'] < 50:
        latency_quality = "Good"
    elif latency['avg'] < 100:
        latency_quality = "Fair"
    else:
        latency_quality = "Poor"
    
    latency_table.add_row("Quality", latency_quality)
    
    console.print(latency_table)

def main():
    """Main entry point."""
    try:
        cli()
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/]")
        if logging.getLogger().level == logging.DEBUG:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 