"""
Real-time visualization module for Signal Booster.
Provides professional graphs and metrics display with enhanced visualization capabilities.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
import threading
import time
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap

# Create custom colormaps for more professional visualization
signal_colors = [(0.8, 0.1, 0.1), (0.95, 0.5, 0.0), (0.0, 0.8, 0.2)]  # Red -> Orange -> Green
signal_cmap = LinearSegmentedColormap.from_list("SignalQuality", signal_colors)

console = Console()

class SignalVisualizer:
    def __init__(self, non_intrusive=True):
        """Initialize the signal visualizer
        
        Args:
            non_intrusive: If True, will use a non-intrusive visualization method
        """
        self.data = {
            'time': [],
            'signal_strength': [],
            'download_speed': [],
            'upload_speed': [],
            'latency': [],
            'optimization_level': []
        }
        self.max_points = 100  # Number of points to show in graphs
        self.fig = None
        self.axs = None
        self.running = False
        self.thread = None
        self.non_intrusive = non_intrusive
        # Only save new figures every 10 seconds to avoid too many files
        self.last_save_time = datetime.now()
        self.save_interval = 10  # seconds
        
        # Set enhanced default styling for plots
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        plt.rcParams['axes.facecolor'] = '#1e1e1e'
        plt.rcParams['figure.facecolor'] = '#1e1e1e'
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'
        plt.rcParams['grid.color'] = '#333333'
        plt.rcParams['grid.linestyle'] = '--'
        plt.rcParams['grid.alpha'] = 0.7
        
    def start(self):
        """Start the visualization thread"""
        self.running = True
        if not self.non_intrusive:
            self.thread = threading.Thread(target=self._update_visualization)
            self.thread.daemon = True
            self.thread.start()
        
    def stop(self):
        """Stop the visualization thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            # Close matplotlib figure if it exists
            if self.fig:
                plt.close(self.fig)
            
    def add_data_point(self, signal_strength, download_speed, upload_speed, latency, optimization_level):
        """Add a new data point to the visualization"""
        current_time = datetime.now()
        
        # Add new data
        self.data['time'].append(current_time)
        self.data['signal_strength'].append(signal_strength)
        self.data['download_speed'].append(download_speed)
        self.data['upload_speed'].append(upload_speed)
        self.data['latency'].append(latency)
        self.data['optimization_level'].append(optimization_level)
        
        # Keep only the last max_points
        for key in self.data:
            if len(self.data[key]) > self.max_points:
                self.data[key] = self.data[key][-self.max_points:]
        
        # In non-intrusive mode, periodically save visualizations instead of displaying in real-time
        if self.non_intrusive and (datetime.now() - self.last_save_time).total_seconds() > self.save_interval:
            self._save_current_visualizations()
            self.last_save_time = datetime.now()
                
    def _save_current_visualizations(self):
        """Save current visualizations to files instead of displaying them"""
        if len(self.data['time']) < 2:
            return
            
        try:
            # Set up the plot with a modern style that works with current matplotlib
            plt.style.use('dark_background')  # Use a built-in style instead of seaborn-darkgrid
            
            # Set seaborn style properties separately
            sns.set_style("darkgrid")
            
            fig, axs = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Signal Booster - Professional Performance Metrics', fontsize=16, fontweight='bold')
            
            # Convert to pandas DataFrame for easier plotting
            df = pd.DataFrame(self.data)
            
            # Signal Strength Plot - Enhanced with target zone highlighting
            axs[0, 0].plot(df['time'], df['signal_strength'], 'g-', linewidth=2.5)
            axs[0, 0].set_title('Signal Strength (%)', fontsize=14, fontweight='bold')
            axs[0, 0].set_ylim(0, 100)
            
            # Add target line at 85% with label
            axs[0, 0].axhline(y=85, color='r', linestyle='--', linewidth=1.5, label='Target')
            
            # Highlight the "good" zone above 85%
            axs[0, 0].axhspan(85, 100, alpha=0.2, color='green', label='Optimal Zone')
            
            # Add a gradient background to indicate signal quality zones
            axs[0, 0].axhspan(0, 30, alpha=0.1, color='red', label='Poor')
            axs[0, 0].axhspan(30, 60, alpha=0.1, color='orange', label='Fair')
            axs[0, 0].axhspan(60, 85, alpha=0.1, color='yellow', label='Good')
            
            # Annotate the current value
            if len(df['signal_strength']) > 0:
                current_signal = df['signal_strength'].iloc[-1]
                axs[0, 0].annotate(f"{current_signal:.1f}%", 
                                   xy=(df['time'].iloc[-1], current_signal),
                                   xytext=(10, 0), textcoords='offset points',
                                   fontsize=12, fontweight='bold',
                                   color='white')
            
            axs[0, 0].legend(loc='lower right')
            
            # Speed Plot - With improved visualization
            axs[0, 1].plot(df['time'], df['download_speed'], 'b-', label='Download', linewidth=2.5)
            axs[0, 1].plot(df['time'], df['upload_speed'], 'r-', label='Upload', linewidth=2.5)
            axs[0, 1].set_title('Network Speed (Mbps)', fontsize=14, fontweight='bold')
            
            # Annotate current speeds
            if len(df['download_speed']) > 0:
                axs[0, 1].annotate(f"{df['download_speed'].iloc[-1]:.1f} Mbps", 
                                 xy=(df['time'].iloc[-1], df['download_speed'].iloc[-1]),
                                 xytext=(10, 0), textcoords='offset points',
                                 fontsize=10, color='blue')
                                 
            if len(df['upload_speed']) > 0:
                axs[0, 1].annotate(f"{df['upload_speed'].iloc[-1]:.1f} Mbps", 
                                 xy=(df['time'].iloc[-1], df['upload_speed'].iloc[-1]),
                                 xytext=(10, 0), textcoords='offset points',
                                 fontsize=10, color='red')
            
            axs[0, 1].legend()
            
            # Latency Plot - With thresholds
            axs[1, 0].plot(df['time'], df['latency'], 'y-', linewidth=2.5)
            axs[1, 0].set_title('Latency (ms)', fontsize=14, fontweight='bold')
            
            # Add threshold lines for latency quality
            axs[1, 0].axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Excellent (<20ms)')
            axs[1, 0].axhline(y=50, color='yellow', linestyle='--', alpha=0.7, label='Good (<50ms)')
            axs[1, 0].axhline(y=100, color='red', linestyle='--', alpha=0.7, label='Poor (>100ms)')
            
            axs[1, 0].legend(loc='upper right')
            
            # Optimization Level Plot - Enhanced with threshold markers
            axs[1, 1].plot(df['time'], df['optimization_level'], 'm-', linewidth=2.5)
            axs[1, 1].set_title('Optimization Level', fontsize=14, fontweight='bold')
            axs[1, 1].set_ylim(0, 100)
            
            # Add target line and zone highlighting
            axs[1, 1].axhline(y=85, color='r', linestyle='--', linewidth=1.5, label='Target')
            axs[1, 1].axhspan(85, 100, alpha=0.2, color='green', label='Optimal Zone')
            
            # Annotate current optimization level
            if len(df['optimization_level']) > 0:
                current_opt = df['optimization_level'].iloc[-1]
                axs[1, 1].annotate(f"{current_opt:.1f}%", 
                                  xy=(df['time'].iloc[-1], current_opt),
                                  xytext=(10, 0), textcoords='offset points',
                                  fontsize=12, fontweight='bold', 
                                  color='white')
            
            axs[1, 1].legend(loc='lower right')
            
            # Format the x-axis to show time nicely for all plots
            for ax in axs.flat:
                ax.tick_params(axis='x', colors='white', labelrotation=45)
                ax.tick_params(axis='y', colors='white')
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Format time labels to show only time (HH:MM:SS)
                time_fmt = '%H:%M:%S'
                if len(df['time']) > 0:
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
            
            # Adjust layout and save with higher quality
            plt.tight_layout()
            plt.savefig('signal_booster_metrics.png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            console.print("[bold blue]Enhanced professional visualization saved to signal_booster_metrics.png[/]")
        except Exception as e:
            console.print(f"[dim]Error saving visualization: {e}[/]")
                
    def _update_visualization(self):
        """Update the visualization in real-time"""
        if self.non_intrusive:
            return
            
        # Set up the plot with a modern style that works with current matplotlib
        plt.style.use('dark_background')  # Use a built-in style instead of seaborn-darkgrid
        
        # Set seaborn style properties separately
        sns.set_style("darkgrid")
        
        self.fig, self.axs = plt.subplots(2, 2, figsize=(15, 10))
        self.fig.suptitle('Signal Booster - Real-time Performance Metrics', fontsize=16, fontweight='bold')
        
        while self.running:
            if len(self.data['time']) > 0:
                # Convert to pandas DataFrame for easier plotting
                df = pd.DataFrame(self.data)
                
                # Clear previous plots
                for ax in self.axs.flat:
                    ax.clear()
                    ax.grid(True, linestyle='--', alpha=0.7)
                
                # Signal Strength Plot - Enhanced with target zone highlighting
                self.axs[0, 0].plot(df['time'], df['signal_strength'], 'g-', linewidth=2.5)
                self.axs[0, 0].set_title('Signal Strength (%)', fontsize=14, fontweight='bold')
                self.axs[0, 0].set_ylim(0, 100)
                
                # Add target line at 85% with label
                self.axs[0, 0].axhline(y=85, color='r', linestyle='--', linewidth=1.5, label='Target')
                
                # Highlight the "good" zone above 85%
                self.axs[0, 0].axhspan(85, 100, alpha=0.2, color='green', label='Optimal Zone')
                
                # Add a gradient background to indicate signal quality zones
                self.axs[0, 0].axhspan(0, 30, alpha=0.1, color='red', label='Poor')
                self.axs[0, 0].axhspan(30, 60, alpha=0.1, color='orange', label='Fair')
                self.axs[0, 0].axhspan(60, 85, alpha=0.1, color='yellow', label='Good')
                
                # Annotate the current value
                if len(df['signal_strength']) > 0:
                    current_signal = df['signal_strength'].iloc[-1]
                    self.axs[0, 0].annotate(f"{current_signal:.1f}%", 
                                       xy=(df['time'].iloc[-1], current_signal),
                                       xytext=(10, 0), textcoords='offset points',
                                       fontsize=12, fontweight='bold',
                                       color='white')
                
                self.axs[0, 0].legend(loc='lower right')
                
                # Speed Plot - With improved visualization
                self.axs[0, 1].plot(df['time'], df['download_speed'], 'b-', label='Download', linewidth=2.5)
                self.axs[0, 1].plot(df['time'], df['upload_speed'], 'r-', label='Upload', linewidth=2.5)
                self.axs[0, 1].set_title('Network Speed (Mbps)', fontsize=14, fontweight='bold')
                
                # Annotate current speeds
                if len(df['download_speed']) > 0:
                    self.axs[0, 1].annotate(f"{df['download_speed'].iloc[-1]:.1f} Mbps", 
                                     xy=(df['time'].iloc[-1], df['download_speed'].iloc[-1]),
                                     xytext=(10, 0), textcoords='offset points',
                                     fontsize=10, color='blue')
                                     
                if len(df['upload_speed']) > 0:
                    self.axs[0, 1].annotate(f"{df['upload_speed'].iloc[-1]:.1f} Mbps", 
                                     xy=(df['time'].iloc[-1], df['upload_speed'].iloc[-1]),
                                     xytext=(10, 0), textcoords='offset points',
                                     fontsize=10, color='red')
                
                self.axs[0, 1].legend()
                
                # Latency Plot - With thresholds
                self.axs[1, 0].plot(df['time'], df['latency'], 'y-', linewidth=2.5)
                self.axs[1, 0].set_title('Latency (ms)', fontsize=14, fontweight='bold')
                
                # Add threshold lines for latency quality
                self.axs[1, 0].axhline(y=20, color='green', linestyle='--', alpha=0.7, label='Excellent (<20ms)')
                self.axs[1, 0].axhline(y=50, color='yellow', linestyle='--', alpha=0.7, label='Good (<50ms)')
                self.axs[1, 0].axhline(y=100, color='red', linestyle='--', alpha=0.7, label='Poor (>100ms)')
                
                self.axs[1, 0].legend(loc='upper right')
                
                # Optimization Level Plot - Enhanced with threshold markers
                self.axs[1, 1].plot(df['time'], df['optimization_level'], 'm-', linewidth=2.5)
                self.axs[1, 1].set_title('Optimization Level', fontsize=14, fontweight='bold')
                self.axs[1, 1].set_ylim(0, 100)
                
                # Add target line and zone highlighting
                self.axs[1, 1].axhline(y=85, color='r', linestyle='--', linewidth=1.5, label='Target')
                self.axs[1, 1].axhspan(85, 100, alpha=0.2, color='green', label='Optimal Zone')
                
                # Annotate current optimization level
                if len(df['optimization_level']) > 0:
                    current_opt = df['optimization_level'].iloc[-1]
                    self.axs[1, 1].annotate(f"{current_opt:.1f}%", 
                                      xy=(df['time'].iloc[-1], current_opt),
                                      xytext=(10, 0), textcoords='offset points',
                                      fontsize=12, fontweight='bold', 
                                      color='white')
                
                self.axs[1, 1].legend(loc='lower right')
                
                # Format the x-axis to show time nicely for all plots
                for ax in self.axs.flat:
                    ax.tick_params(axis='x', colors='white', labelrotation=45)
                    ax.tick_params(axis='y', colors='white')
                    
                    # Format time labels to show only time (HH:MM:SS)
                    time_fmt = '%H:%M:%S'
                    if len(df['time']) > 0:
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
                
                # Adjust layout and draw
                plt.tight_layout()
                plt.pause(0.1)
                
            time.sleep(1)
            
    def display_metrics(self):
        """Display current metrics in a simple format"""
        if len(self.data['time']) == 0:
            return
         
        # In non-intrusive mode, we don't display rich tables to avoid cluttering the terminal
        if self.non_intrusive:
            return
            
        # For rich table display
        current = {
            'Signal Strength': f"{self.data['signal_strength'][-1]:.1f}%",
            'Download Speed': f"{self.data['download_speed'][-1]:.1f} Mbps",
            'Upload Speed': f"{self.data['upload_speed'][-1]:.1f} Mbps",
            'Latency': f"{self.data['latency'][-1]:.1f} ms",
            'Optimization Level': f"{self.data['optimization_level'][-1]:.1f}%"
        }
        
        table = Table(title="Current Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for metric, value in current.items():
            table.add_row(metric, value)
            
        console.print(table)
        
    def display_optimization_progress(self, current, target):
        """Display optimization progress with a progress bar"""
        if self.non_intrusive:
            return
            
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        
        with progress:
            task = progress.add_task(
                f"Optimizing Signal Strength: {current:.1f}% → {target:.1f}%",
                total=100,
                completed=(current/target)*100
            )
            
    def display_optimization_actions(self, actions):
        """Display current optimization actions being taken"""
        if self.non_intrusive or not actions:
            return
            
        console.print(Panel.fit(
            "\n".join([f"• {action}" for action in actions]),
            title="Current Optimization Actions",
            border_style="blue"
        )) 