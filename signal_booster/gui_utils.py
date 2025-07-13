"""
GUI Utilities for Signal Booster
Contains helper functions for the GUI components.
"""

import os
import logging
from typing import Optional, Tuple, Union
import tkinter as tk
from PIL import Image, ImageTk
import customtkinter as ctk

logger = logging.getLogger(__name__)

def load_image(path: str, size: Tuple[int, int] = None) -> Optional[ctk.CTkImage]:
    """
    Load an image from the specified path and return a CTkImage object.
    
    Args:
        path: Path to the image file
        size: Optional tuple of (width, height) to resize the image
    
    Returns:
        CTkImage object or None if loading fails
    """
    try:
        if os.path.exists(path):
            image = Image.open(path)
            if size:
                image = image.resize(size)
            return ctk.CTkImage(light_image=image, dark_image=image, size=size)
        else:
            logger.warning(f"Image not found: {path}")
            return None
    except Exception as e:
        logger.error(f"Error loading image {path}: {e}")
        return None

def create_tooltip(widget, text):
    """
    Create a tooltip for a given widget.
    
    Args:
        widget: The widget to add a tooltip to
        text: The text to display in the tooltip
    """
    tooltip = None
    
    def enter(event):
        nonlocal tooltip
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 25
        
        # Create a toplevel window
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            tooltip, text=text, background="#ffffe0", relief="solid", 
            borderwidth=1, padx=5, pady=2, font=("Segoe UI", 10)
        )
        label.pack()
    
    def leave(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None
    
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

def format_speed(speed: float) -> str:
    """
    Format speed values with appropriate units.
    
    Args:
        speed: Speed value in Mbps
    
    Returns:
        Formatted string with appropriate unit
    """
    if speed < 1:
        return f"{speed * 1000:.1f} Kbps"
    elif speed < 100:
        return f"{speed:.1f} Mbps"
    else:
        return f"{speed:.0f} Mbps"

def format_latency(latency: float) -> str:
    """
    Format latency values with appropriate units.
    
    Args:
        latency: Latency value in ms
    
    Returns:
        Formatted string with ms unit
    """
    return f"{latency:.0f} ms"

def get_quality_color(value: float, good_threshold: float = 70, medium_threshold: float = 40) -> str:
    """
    Get a color representing the quality level.
    
    Args:
        value: The value to evaluate (0-100)
        good_threshold: Threshold for good quality
        medium_threshold: Threshold for medium quality
    
    Returns:
        Hex color code
    """
    if value >= good_threshold:
        return "#4CAF50"  # Green
    elif value >= medium_threshold:
        return "#FFC107"  # Amber
    else:
        return "#F44336"  # Red

def get_signal_quality_text(signal_strength: float) -> str:
    """
    Convert signal strength to a quality text.
    
    Args:
        signal_strength: Signal strength value (0-100)
    
    Returns:
        Quality description
    """
    if signal_strength >= 80:
        return "Excellent"
    elif signal_strength >= 60:
        return "Good"
    elif signal_strength >= 40:
        return "Fair"
    elif signal_strength >= 20:
        return "Poor"
    else:
        return "Very Poor" 