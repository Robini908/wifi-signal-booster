"""
Status bar component for the Signal Booster GUI.
Displays current status and key metrics.
"""

import logging
import customtkinter as ctk
from typing import Optional

from ..gui_utils import get_quality_color, format_speed

logger = logging.getLogger(__name__)

class StatusBar(ctk.CTkFrame):
    """Status bar showing key information about the Signal Booster state."""
    
    def __init__(self, master, **kwargs):
        """
        Initialize the status bar.
        
        Args:
            master: Parent widget
        """
        super().__init__(master, height=40, **kwargs)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure((1, 2, 3), weight=1)
        
        # Create components
        self._create_components()
    
    def _create_components(self):
        """Create status bar components."""
        # Status message label
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=("Segoe UI", 12),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Signal strength indicator
        self.signal_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.signal_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.signal_frame.grid_columnconfigure(0, weight=1)
        self.signal_frame.grid_columnconfigure(1, weight=3)
        
        self.signal_title = ctk.CTkLabel(
            self.signal_frame,
            text="Signal:",
            font=("Segoe UI", 11)
        )
        self.signal_title.grid(row=0, column=0, sticky="w")
        
        self.signal_progress = ctk.CTkProgressBar(
            self.signal_frame,
            width=120,
            height=12,
            corner_radius=2
        )
        self.signal_progress.grid(row=0, column=1, padx=5, sticky="ew")
        self.signal_progress.set(0)
        
        # Speed indicator
        self.speed_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.speed_frame.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        self.speed_frame.grid_columnconfigure(0, weight=1)
        self.speed_frame.grid_columnconfigure(1, weight=3)
        
        self.speed_title = ctk.CTkLabel(
            self.speed_frame,
            text="Speed:",
            font=("Segoe UI", 11)
        )
        self.speed_title.grid(row=0, column=0, sticky="w")
        
        self.speed_progress = ctk.CTkProgressBar(
            self.speed_frame,
            width=120,
            height=12,
            corner_radius=2
        )
        self.speed_progress.grid(row=0, column=1, padx=5, sticky="ew")
        self.speed_progress.set(0)
        
        # Optimization level indicator
        self.opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.opt_frame.grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        self.opt_frame.grid_columnconfigure(0, weight=1)
        self.opt_frame.grid_columnconfigure(1, weight=3)
        
        self.opt_title = ctk.CTkLabel(
            self.opt_frame,
            text="Optimization:",
            font=("Segoe UI", 11)
        )
        self.opt_title.grid(row=0, column=0, sticky="w")
        
        self.opt_progress = ctk.CTkProgressBar(
            self.opt_frame,
            width=120,
            height=12,
            corner_radius=2
        )
        self.opt_progress.grid(row=0, column=1, padx=5, sticky="ew")
        self.opt_progress.set(0)
    
    def set_status(self, text: str, error: bool = False):
        """
        Update the status message.
        
        Args:
            text: Status message to display
            error: Whether this is an error message
        """
        self.status_label.configure(
            text=text,
            text_color="#F44336" if error else None
        )
    
    def update_indicators(self, signal_strength: float, current_speed: float, 
                          target_speed: float, optimization_level: float):
        """
        Update the status indicators.
        
        Args:
            signal_strength: Signal strength percentage (0-100)
            current_speed: Current speed in Mbps
            target_speed: Target speed in Mbps
            optimization_level: Optimization level percentage (0-100)
        """
        # Update signal strength
        signal_norm = max(0, min(signal_strength / 100, 1))
        self.signal_progress.set(signal_norm)
        self.signal_progress.configure(
            progress_color=get_quality_color(signal_strength)
        )
        self.signal_title.configure(
            text=f"Signal: {signal_strength:.0f}%"
        )
        
        # Update speed
        speed_norm = max(0, min(current_speed / target_speed, 1))
        self.speed_progress.set(speed_norm)
        self.speed_progress.configure(
            progress_color=get_quality_color(speed_norm * 100)
        )
        self.speed_title.configure(
            text=f"Speed: {format_speed(current_speed)}"
        )
        
        # Update optimization level
        opt_norm = max(0, min(optimization_level / 100, 1))
        self.opt_progress.set(opt_norm)
        self.opt_progress.configure(
            progress_color=get_quality_color(optimization_level)
        )
        self.opt_title.configure(
            text=f"Opt: {optimization_level:.0f}%"
        ) 