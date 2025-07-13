"""
Toolbar component for the Signal Booster GUI.
Contains controls for starting/stopping the booster and setting parameters.
"""

import logging
import customtkinter as ctk
from typing import Callable

from ..gui_utils import create_tooltip

logger = logging.getLogger(__name__)

class ToolbarFrame(ctk.CTkFrame):
    """Toolbar frame containing controls for the Signal Booster."""
    
    def __init__(self, master, start_callback: Callable, is_running: bool = False, **kwargs):
        """
        Initialize the toolbar.
        
        Args:
            master: Parent widget
            start_callback: Function to call when start/stop button is clicked
            is_running: Initial state (running or not)
        """
        super().__init__(master, **kwargs)
        
        self.start_callback = start_callback
        self.is_running = is_running
        
        # Configure grid
        self.grid_columnconfigure((1, 2, 3), weight=1)
        
        # Create components
        self._create_components()
    
    def _create_components(self):
        """Create toolbar components."""
        # Start/Stop Button
        self.start_button = ctk.CTkButton(
            self,
            text="Start Boosting" if not self.is_running else "Stop Boosting",
            command=self.start_callback,
            fg_color="#4CAF50" if not self.is_running else "#F44336",
            hover_color="#45a049" if not self.is_running else "#d32f2f",
            font=("Segoe UI", 12, "bold"),
            height=36,
            corner_radius=8
        )
        self.start_button.grid(row=0, column=0, padx=(10, 20), pady=10, sticky="w")
        create_tooltip(self.start_button, "Start or stop the signal booster")
        
        # Target Speed Control
        self.target_speed_label = ctk.CTkLabel(
            self, 
            text="Target Speed (Mbps):",
            font=("Segoe UI", 12)
        )
        self.target_speed_label.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="e")
        
        self.target_speed_slider = ctk.CTkSlider(
            self,
            from_=1,
            to=100,
            number_of_steps=99,
            width=180,
            command=self._on_speed_change
        )
        self.target_speed_slider.set(20)  # Default target: 20 Mbps
        self.target_speed_slider.grid(row=0, column=2, padx=5, pady=10, sticky="ew")
        create_tooltip(self.target_speed_slider, "Set target speed for optimization")
        
        self.target_speed_value = ctk.CTkLabel(
            self,
            text="20 Mbps",
            width=60,
            font=("Segoe UI", 12, "bold")
        )
        self.target_speed_value.grid(row=0, column=3, padx=(0, 20), pady=10, sticky="w")
        
        # Aggressive Mode Checkbox
        self.aggressive_mode = ctk.CTkCheckBox(
            self,
            text="Aggressive Mode",
            font=("Segoe UI", 12),
            checkbox_width=22,
            checkbox_height=22,
            corner_radius=4
        )
        self.aggressive_mode.grid(row=0, column=4, padx=(20, 10), pady=10, sticky="w")
        create_tooltip(self.aggressive_mode, "Enable more aggressive optimization techniques")
    
    def _on_speed_change(self, value):
        """Handle target speed slider change."""
        mbps = int(value)
        self.target_speed_value.configure(text=f"{mbps} Mbps")
    
    def update_running_state(self, is_running: bool):
        """Update the visual state based on running status."""
        self.is_running = is_running
        
        if is_running:
            self.start_button.configure(
                text="Stop Boosting",
                fg_color="#F44336",
                hover_color="#d32f2f"
            )
        else:
            self.start_button.configure(
                text="Start Boosting",
                fg_color="#4CAF50",
                hover_color="#45a049"
            )
    
    def get_target_speed(self) -> float:
        """Get the current target speed value."""
        return float(self.target_speed_slider.get())
    
    def get_aggressive_mode(self) -> bool:
        """Get the aggressive mode checkbox state."""
        return bool(self.aggressive_mode.get()) 