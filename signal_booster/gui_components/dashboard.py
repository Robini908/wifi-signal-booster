"""
Dashboard component for the Signal Booster GUI.
Provides real-time visualizations and metrics.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import customtkinter as ctk

from ..gui_utils import format_speed, format_latency, get_quality_color, get_signal_quality_text

logger = logging.getLogger(__name__)

class MetricsCard(ctk.CTkFrame):
    """Card widget displaying a single metric with label and value."""
    
    def __init__(self, master, title: str, value: str = "-", unit: str = "", 
                 icon: Optional[ctk.CTkImage] = None, **kwargs):
        """
        Initialize a metrics card.
        
        Args:
            master: Parent widget
            title: Title of the metric
            value: Initial value to display
            unit: Unit of measurement
            icon: Optional icon to display
        """
        super().__init__(master, corner_radius=10, fg_color="#2d3748", **kwargs)
        
        self.title = title
        self.value = value
        self.unit = unit
        self.icon = icon
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Create components
        self._create_components()
    
    def _create_components(self):
        """Create card components."""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=self.title,
            font=("Segoe UI", 14),
            text_color="gray80",
            anchor="w"
        )
        self.title_label.grid(row=0, column=0, padx=15, pady=(10, 0), sticky="w")
        
        # Value
        self.value_label = ctk.CTkLabel(
            self,
            text=f"{self.value}",
            font=("Segoe UI", 24, "bold"),
            anchor="w"
        )
        self.value_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")
    
    def update_value(self, value, color: Optional[str] = None):
        """
        Update the displayed value.
        
        Args:
            value: New value to display
            color: Optional color for the value text
        """
        self.value = value
        self.value_label.configure(
            text=f"{value}",
            text_color=color if color else None
        )

class GaugeWidget(ctk.CTkFrame):
    """A gauge widget displaying a value as a circular progress indicator."""
    
    def __init__(self, master, title: str, min_value: float = 0, max_value: float = 100,
                 initial_value: float = 0, unit: str = "%", **kwargs):
        """
        Initialize the gauge widget.
        
        Args:
            master: Parent widget
            title: Title of the gauge
            min_value: Minimum value
            max_value: Maximum value
            initial_value: Initial value
            unit: Unit of measurement
        """
        super().__init__(master, corner_radius=10, fg_color="#2d3748", **kwargs)
        
        self.title = title
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.unit = unit
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Create components
        self._create_components()
    
    def _create_components(self):
        """Create gauge components."""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=self.title,
            font=("Segoe UI", 14, "bold"),
            anchor="center"
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        
        # Create circular progress indicator
        self.canvas_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.canvas_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Value display with color based on level
        self.value_label = ctk.CTkLabel(
            self,
            text=f"{self.value:.0f}{self.unit}",
            font=("Segoe UI", 24, "bold"),
            anchor="center"
        )
        self.value_label.grid(row=2, column=0, padx=10, pady=(0, 5), sticky="ew")
        
        # Progress indicator
        self.progress = ctk.CTkProgressBar(
            self,
            width=120,
            height=20,
            corner_radius=5,
            mode="determinate"
        )
        self.progress.grid(row=3, column=0, padx=30, pady=(0, 10), sticky="ew")
        
        # Status text (Excellent, Good, Fair, Poor)
        self.status_text = ctk.CTkLabel(
            self,
            text=self._get_status_text(self.value),
            font=("Segoe UI", 16),
            anchor="center"
        )
        self.status_text.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Set initial values
        self.update_value(self.value)
    
    def _get_status_text(self, value: float) -> str:
        """Get a status text based on the value."""
        normalized_value = (value - self.min_value) / (self.max_value - self.min_value) * 100
        
        if normalized_value >= 80:
            return "Excellent"
        elif normalized_value >= 60:
            return "Good"
        elif normalized_value >= 40:
            return "Fair"
        elif normalized_value >= 20:
            return "Poor"
        else:
            return "Very Poor"
    
    def update_value(self, value: float):
        """
        Update the gauge value.
        
        Args:
            value: New value for the gauge
        """
        self.value = max(self.min_value, min(value, self.max_value))
        
        # Calculate normalized value (0-1)
        normalized_value = (self.value - self.min_value) / (self.max_value - self.min_value)
        
        # Get color based on value
        color = self._get_color_for_value(normalized_value)
        
        # Update value label
        self.value_label.configure(
            text=f"{self.value:.0f}{self.unit}",
            text_color=color
        )
        
        # Update progress bar
        self.progress.set(normalized_value)
        self.progress.configure(progress_color=color)
        
        # Update status text
        status = self._get_status_text(self.value)
        self.status_text.configure(
            text=status,
            text_color=color
        )
    
    def _get_color_for_value(self, normalized_value: float) -> str:
        """Get a color for a normalized value (0-1)."""
        if normalized_value >= 0.8:
            return "#4CAF50"  # Green
        elif normalized_value >= 0.6:
            return "#8BC34A"  # Light Green
        elif normalized_value >= 0.4:
            return "#FFC107"  # Amber
        elif normalized_value >= 0.2:
            return "#FF9800"  # Orange
        else:
            return "#F44336"  # Red

class DashboardFrame(ctk.CTkFrame):
    """Main dashboard frame showing visualizations and metrics."""
    
    def __init__(self, master, **kwargs):
        """
        Initialize the dashboard.
        
        Args:
            master: Parent widget
        """
        super().__init__(master, **kwargs)
        
        # Configure grid
        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=1)
        
        # Create components
        self._create_components()
        
        # Create a placeholder for trend data
        self.trend_data = {
            'time': [],
            'signal_strength': [],
            'download_speed': [],
            'upload_speed': [],
            'latency': [],
            'optimization_level': []
        }
    
    def _create_components(self):
        """Create dashboard components."""
        # Metrics cards row
        self.signal_card = MetricsCard(
            self,
            title="Signal Strength",
            value="-",
            unit="%"
        )
        self.signal_card.grid(row=0, column=0, padx=10, pady=10, sticky="new")
        
        self.speed_card = MetricsCard(
            self,
            title="Current Speed",
            value="-",
            unit="Mbps"
        )
        self.speed_card.grid(row=0, column=1, padx=10, pady=10, sticky="new")
        
        self.latency_card = MetricsCard(
            self,
            title="Latency",
            value="-",
            unit="ms"
        )
        self.latency_card.grid(row=0, column=2, padx=10, pady=10, sticky="new")
        
        # Gauge indicators row
        self.signal_gauge = GaugeWidget(
            self,
            title="Signal Quality",
            min_value=0,
            max_value=100,
            initial_value=0,
            unit="%"
        )
        self.signal_gauge.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.speed_gauge = GaugeWidget(
            self,
            title="Speed Optimization",
            min_value=0,
            max_value=100,
            initial_value=0,
            unit="%"
        )
        self.speed_gauge.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        self.opt_gauge = GaugeWidget(
            self,
            title="Overall Optimization",
            min_value=0,
            max_value=100,
            initial_value=0,
            unit="%"
        )
        self.opt_gauge.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        
        # Trend charts row
        self.trend_frame = ctk.CTkFrame(self, fg_color="#2d3748", corner_radius=10)
        self.trend_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.trend_frame.grid_columnconfigure(0, weight=1)
        self.trend_frame.grid_rowconfigure(1, weight=1)
        
        self.trend_label = ctk.CTkLabel(
            self.trend_frame,
            text="Performance Trends",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.trend_label.grid(row=0, column=0, padx=15, pady=(10, 0), sticky="w")
        
        self.trend_chart_frame = ctk.CTkFrame(
            self.trend_frame,
            fg_color="transparent"
        )
        self.trend_chart_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Set up the matplotlib figure for trends
        self.fig, self.axes = plt.subplots(1, 3, figsize=(15, 4))
        self.fig.patch.set_facecolor('#2d3748')
        
        for ax in self.axes:
            ax.set_facecolor('#2d3748')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white') 
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.set_title('Initializing...', color='white')
            ax.grid(True, linestyle='--', alpha=0.7)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.trend_chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def update_visualizations(self, metrics: Dict[str, Any]):
        """
        Update all visualizations with new metrics.
        
        Args:
            metrics: Dictionary of metrics
        """
        # Update the metrics cards
        signal_strength = metrics.get('signal_strength', 0)
        current_speed = metrics.get('current_speed', 0)
        latency = metrics.get('latency', 0)
        optimization_level = metrics.get('optimization_level', 0)
        
        # Update metrics cards with formatted values
        signal_quality = get_signal_quality_text(signal_strength)
        self.signal_card.update_value(
            f"{signal_strength:.0f}% ({signal_quality})",
            color=get_quality_color(signal_strength)
        )
        
        self.speed_card.update_value(
            format_speed(current_speed),
            color=get_quality_color(current_speed / metrics.get('target_speed', 10) * 100)
        )
        
        latency_quality = 100 - min(100, max(0, latency - 20) / 2)
        self.latency_card.update_value(
            format_latency(latency),
            color=get_quality_color(latency_quality)
        )
        
        # Update the gauges
        self.signal_gauge.update_value(signal_strength)
        self.speed_gauge.update_value(current_speed / metrics.get('target_speed', 10) * 100)
        self.opt_gauge.update_value(optimization_level)
    
    def update_trend_charts(self, data: Dict[str, List]):
        """
        Update the trend charts with new data.
        
        Args:
            data: Dictionary of time series data
        """
        try:
            # Only update if we have at least 2 data points
            if len(data['time']) < 2:
                return
                
            # Clear the axes
            for ax in self.axes:
                ax.clear()
                ax.grid(True, linestyle='--', alpha=0.7)
            
            # Set background colors
            for ax in self.axes:
                ax.set_facecolor('#2d3748')
            
            # Convert to pandas DataFrame for easier handling
            df = pd.DataFrame(data)
            
            # Plot signal strength with enhanced visualization
            self.axes[0].plot(df['time'], df['signal_strength'], color='#4CAF50', linewidth=2.5)
            self.axes[0].set_title('Signal Strength', color='white', fontweight='bold')
            self.axes[0].set_ylim(0, 100)
            self.axes[0].set_ylabel('Strength (%)', color='white')
            
            # Add 85% target line and optimal zone highlighting
            self.axes[0].axhline(y=85, color='#FF5252', linestyle='--', linewidth=1.5, label='Target (85%)')
            self.axes[0].axhspan(85, 100, alpha=0.2, color='#4CAF50', label='Optimal')
            
            # Add quality zone indicators
            self.axes[0].axhspan(0, 30, alpha=0.1, color='#FF5252')
            self.axes[0].axhspan(30, 60, alpha=0.1, color='#FFC107')
            self.axes[0].axhspan(60, 85, alpha=0.1, color='#8BC34A')
            
            # Add legend with custom styling
            self.axes[0].legend(loc='lower right', facecolor='#2d3748', labelcolor='white')
            
            # Plot speeds with enhanced visualization
            self.axes[1].plot(df['time'], df['download_speed'], color='#2196F3', linewidth=2.5, label='Download')
            if 'upload_speed' in df:
                self.axes[1].plot(df['time'], df['upload_speed'], color='#FF9800', linewidth=2.5, label='Upload')
            self.axes[1].set_title('Network Speed', color='white', fontweight='bold')
            self.axes[1].set_ylabel('Speed (Mbps)', color='white')
            self.axes[1].legend(loc='upper left', facecolor='#2d3748', labelcolor='white')
            
            # Plot latency with enhanced visualization
            self.axes[2].plot(df['time'], df['latency'], color='#F44336', linewidth=2.5)
            self.axes[2].set_title('Network Latency', color='white', fontweight='bold')
            self.axes[2].set_ylabel('Latency (ms)', color='white')
            
            # Add latency threshold indicators
            self.axes[2].axhline(y=20, color='#4CAF50', linestyle='--', alpha=0.7, label='Excellent')
            self.axes[2].axhline(y=50, color='#FFC107', linestyle='--', alpha=0.7, label='Good')
            self.axes[2].axhline(y=100, color='#FF5252', linestyle='--', alpha=0.7, label='Poor')
            
            # Add legend for latency thresholds
            self.axes[2].legend(loc='upper right', facecolor='#2d3748', labelcolor='white')
            
            # Format the x-axis to show time
            for ax in self.axes:
                ax.tick_params(axis='x', colors='white', labelrotation=45)
                ax.tick_params(axis='y', colors='white')
                
                # Format time labels to show only time (HH:MM:SS)
                time_fmt = '%H:%M:%S'
                time_labels = [t.strftime(time_fmt) for t in df['time']]
                
                # Only show a subset of labels to prevent overcrowding
                if len(time_labels) > 10:
                    step = len(time_labels) // 5
                    for i in range(len(time_labels)):
                        if i % step != 0:
                            time_labels[i] = ''
                
                # Set the x-ticks and labels
                if len(time_labels) > 0:
                    ax.set_xticks(df['time'][::max(1, len(df) // 5)])
                    ax.set_xticklabels(time_labels[::max(1, len(df) // 5)])
            
            # Apply tight layout to make good use of space
            self.fig.tight_layout()
            
            # Update the canvas
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error updating trend charts: {e}") 