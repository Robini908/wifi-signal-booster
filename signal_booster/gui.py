"""
Signal Booster GUI Application
Provides a modern interface for the Signal Booster using CustomTkinter.
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# UI Libraries
import customtkinter as ctk
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox

# Plotting and data libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Internal imports
from .core import SignalBooster
from .network_utils import get_network_interfaces
from .advanced_config import OptimizationLevel, ConnectionType
from .gui_components.dashboard import DashboardFrame
from .gui_components.settings import SettingsFrame
from .gui_components.status_bar import StatusBar
from .gui_components.toolbar import ToolbarFrame
from .gui_components.advanced_settings import AdvancedSettingsFrame
from .gui_utils import load_image, create_tooltip

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure appearance
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class SignalBoosterApp(ctk.CTk):
    """Main Signal Booster application window using CustomTkinter."""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Signal Booster Pro")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # Set app icon if available
        self.icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(self.icon_path):
            icon = ImageTk.PhotoImage(Image.open(self.icon_path))
            self.iconphoto(True, icon)
        
        # Initialize advanced settings
        self.advanced_settings = {}
        self.optimization_level = OptimizationLevel.STANDARD
        
        # Initialize Signal Booster backend
        self.booster = SignalBooster(
            optimization_level=self.optimization_level,
            advanced_settings=self.advanced_settings
        )
        self.booster_thread = None
        self.is_running = False
        self.update_interval = 1000  # Update interval in milliseconds
        
        # Initialize metrics data storage
        self.metrics_data = {
            'time': [],
            'signal_strength': [],
            'download_speed': [],
            'upload_speed': [],
            'latency': [],
            'optimization_level': []
        }
        
        # Add current time and initial values
        current_time = datetime.now()
        self.metrics_data['time'].append(current_time)
        self.metrics_data['signal_strength'].append(35)
        self.metrics_data['download_speed'].append(5.0)
        self.metrics_data['upload_speed'].append(1.8)
        self.metrics_data['latency'].append(50)
        self.metrics_data['optimization_level'].append(0)
        
        # Create main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Create components
        self.create_components()
        
        # Initialize with current metrics
        initial_metrics = self.booster.get_current_metrics()
        self.dashboard.update_visualizations(initial_metrics)
        
        # Set up data update timer
        self.after(self.update_interval, self.update_metrics)
    
    def create_components(self):
        """Create all GUI components."""
        # Create toolbar at the top
        self.toolbar = ToolbarFrame(
            self, 
            start_callback=self.toggle_boosting,
            is_running=self.is_running
        )
        self.toolbar.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        
        # Create tabview for main content
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Add tabs
        self.tab_dashboard = self.tabview.add("Dashboard")
        self.tab_settings = self.tabview.add("Settings")
        self.tab_advanced = self.tabview.add("Advanced")
        
        # Configure tab content
        self.tab_dashboard.grid_columnconfigure(0, weight=1)
        self.tab_dashboard.grid_rowconfigure(0, weight=1)
        self.tab_settings.grid_columnconfigure(0, weight=1)
        self.tab_settings.grid_rowconfigure(0, weight=1)
        self.tab_advanced.grid_columnconfigure(0, weight=1)
        self.tab_advanced.grid_rowconfigure(0, weight=1)
        
        # Create dashboard content
        self.dashboard = DashboardFrame(self.tab_dashboard)
        self.dashboard.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create settings content
        self.settings = SettingsFrame(
            self.tab_settings,
            interfaces=get_network_interfaces()
        )
        self.settings.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create advanced settings content
        self.advanced_settings_frame = AdvancedSettingsFrame(
            self.tab_advanced,
            callback=self.on_advanced_setting_change
        )
        self.advanced_settings_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Create status bar at the bottom
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
    
    def on_advanced_setting_change(self, name: str, value: Any):
        """Handle advanced setting changes."""
        logger.info(f"Advanced setting changed: {name} = {value}")
        
        if name == "optimization_level":
            # Convert string to enum
            try:
                self.optimization_level = OptimizationLevel(value)
                # Update the booster if it's already running
                if self.is_running:
                    self.booster.set_optimization_level(self.optimization_level)
                    self.status_bar.set_status(f"Optimization level changed to {value.upper()}")
            except ValueError:
                logger.error(f"Invalid optimization level: {value}")
                
        elif name == "all_settings":
            # Update the advanced settings
            self.advanced_settings = value
            
            # Update the booster if it's already running
            if self.is_running:
                # Restart with new settings
                self.toggle_boosting()  # Stop
                self.toggle_boosting()  # Start again with new settings
                self.status_bar.set_status("Applied new advanced settings")
        else:
            # Update individual setting
            category = None
            
            # Determine which category this setting belongs to
            if name in ["tcp_window_size", "congestion_algorithm", "tcp_autotuning"]:
                category = "tcp"
            elif name in ["channel_switching", "tx_power", "roaming_aggressiveness", "band_preference"]:
                category = "wifi"
            elif name in ["dns_prefetching", "dns_provider", "custom_dns"]:
                category = "dns"
            elif name in ["deep_packet_inspection", "bandwidth_control", "packet_prioritization", "buffer_bloat_mitigation"]:
                category = "features"
                
            if category:
                if category not in self.advanced_settings:
                    self.advanced_settings[category] = {}
                    
                self.advanced_settings[category][name] = value
                
                # Update the booster if it's already running
                if self.is_running:
                    self.booster.advanced_settings = self.advanced_settings
                    # For some settings, we need to update feature flags
                    if name in ["dns_prefetching", "channel_switching", "deep_packet_inspection", 
                               "bandwidth_control", "packet_prioritization"]:
                        self.booster._set_feature_flags()
    
    def toggle_boosting(self):
        """Start or stop the signal boosting process."""
        if not self.is_running:
            # Start boosting
            self.is_running = True
            self.toolbar.update_running_state(True)
            
            # Get settings from UI
            target_speed = self.toolbar.get_target_speed()
            aggressive = self.toolbar.get_aggressive_mode()
            
            # Update status bar
            self.status_bar.set_status("Starting signal booster...")
            
            # Start booster in a separate thread
            self.booster_thread = threading.Thread(
                target=self.booster.start,
                kwargs={
                    'target_speed': target_speed,
                    'aggressive': aggressive,
                    'monitor': True,
                    'optimization_level': self.optimization_level,
                    'advanced_settings': self.advanced_settings
                }
            )
            self.booster_thread.daemon = True
            self.booster_thread.start()
            
            # Update status bar after a short delay
            self.after(1000, lambda: self.status_bar.set_status("Signal booster running"))
        else:
            # Stop boosting
            self.is_running = False
            self.toolbar.update_running_state(False)
            self.status_bar.set_status("Stopping signal booster...")
            
            # Stop the booster
            self.booster.stop()
            
            # Update status bar after a short delay
            self.after(1000, lambda: self.status_bar.set_status("Signal booster stopped"))
    
    def update_metrics(self):
        """Update metrics and visualizations."""
        try:
            # Get current metrics from the booster
            metrics = self.booster.get_current_metrics()
            
            # Update status bar indicators
            self.status_bar.update_indicators(
                signal_strength=metrics['signal_strength'],
                current_speed=metrics['current_speed'],
                target_speed=metrics['target_speed'],
                optimization_level=metrics['optimization_level']
            )
            
            # Update dashboard visualizations
            self.dashboard.update_visualizations(metrics)
            
            # Add to metrics history for trend analysis
            current_time = datetime.now()
            
            # Add new data points
            self.metrics_data['time'].append(current_time)
            self.metrics_data['signal_strength'].append(metrics['signal_strength'])
            self.metrics_data['download_speed'].append(metrics['current_speed'])
            self.metrics_data['latency'].append(metrics['latency'])
            self.metrics_data['optimization_level'].append(metrics['optimization_level'])
            
            # For upload speed (if not available in metrics)
            if 'upload_speed' in metrics:
                self.metrics_data['upload_speed'].append(metrics['upload_speed'])
            elif len(self.metrics_data['upload_speed']) < len(self.metrics_data['time']):
                # Estimate upload as fraction of download if not available
                self.metrics_data['upload_speed'].append(metrics['current_speed'] * 0.4)
            
            # Keep only the last 60 data points (1 minute at 1-second intervals)
            if len(self.metrics_data['time']) > 60:
                for key in self.metrics_data:
                    self.metrics_data[key] = self.metrics_data[key][-60:]
            
            # Update trend charts in dashboard
            if len(self.metrics_data['time']) > 1:
                self.dashboard.update_trend_charts(self.metrics_data)
        
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            self.status_bar.set_status(f"Error: {str(e)[:50]}...", error=True)
        
        # Schedule next update
        self.after(self.update_interval, self.update_metrics)
    
    def on_closing(self):
        """Handle window closing event."""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Signal Booster is still running. Do you want to stop it and quit?"):
                self.booster.stop()
                self.destroy()
        else:
            self.destroy()

def run_gui():
    """Main entry point for the GUI application."""
    try:
        logger.info("Starting Signal Booster GUI application")
        app = SignalBoosterApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)  # Handle window close event
        app.mainloop()
    except Exception as e:
        logger.exception(f"Error in GUI application: {e}")
        messagebox.showerror("Error", f"An error occurred: {str(e)}\n\nSee log for details.")
        
if __name__ == "__main__":
    run_gui() 