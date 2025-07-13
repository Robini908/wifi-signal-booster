"""
Advanced settings component for the Signal Booster GUI.
Provides access to advanced optimization configurations.
"""

import logging
import json
import platform
from typing import Dict, List, Any, Callable, Optional, Union

import customtkinter as ctk
# Import CTkToolTip with proper error handling
try:
    from CTkToolTip import CTkToolTip
except ImportError:
    # Create a dummy tooltip class if not available
    class CTkToolTip:
        def __init__(self, widget=None, message=""):
            pass

from ..advanced_config import OptimizationLevel, ConnectionType
from ..gui_utils import create_tooltip

logger = logging.getLogger(__name__)

class AdvancedSettingsFrame(ctk.CTkFrame):
    """Advanced settings frame for configuring advanced optimization options."""
    
    def __init__(self, master, callback: Callable = None, **kwargs):
        """
        Initialize the advanced settings frame.
        
        Args:
            master: Parent widget
            callback: Function to call when settings are changed
        """
        super().__init__(master, **kwargs)
        
        self.callback = callback
        self.os_type = platform.system()
        
        # Store all settings widgets for easy access
        self.settings_widgets = {}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1)  # Make the last row expandable
        
        # Create components
        self._create_components()
    
    def _create_components(self):
        """Create advanced settings components."""
        # Title label
        self.title_label = ctk.CTkLabel(
            self,
            text="Advanced Optimization Settings",
            font=("Segoe UI", 18, "bold"),
            anchor="w"
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Description label
        self.desc_label = ctk.CTkLabel(
            self,
            text="Configure advanced settings to fine-tune network optimization. These settings can significantly impact performance.",
            font=("Segoe UI", 12),
            anchor="w",
            wraplength=600
        )
        self.desc_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")
        
        # Optimization level frame
        self.optim_frame = ctk.CTkFrame(self)
        self.optim_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.optim_frame.grid_columnconfigure(1, weight=1)
        
        self.optim_label = ctk.CTkLabel(
            self.optim_frame,
            text="Optimization Level:",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.optim_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Create segmented button for optimization levels
        self.optim_level = ctk.CTkSegmentedButton(
            self.optim_frame,
            values=["Light", "Standard", "Aggressive", "Extreme"],
            command=self._on_optimization_level_change
        )
        self.optim_level.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.optim_level.set("Standard")  # Default value
        
        # Replace CTkToolTip with a help label explaining the optimization levels
        self.optim_level_help = ctk.CTkLabel(
            self.optim_frame,
            text=(
                "Light: Basic optimizations with minimal system impact\n"
                "Standard: Balanced optimizations for most users\n"
                "Aggressive: Stronger optimizations that may affect other applications\n"
                "Extreme: Maximum optimizations that may cause instability"
            ),
            font=("Segoe UI", 10),
            text_color="gray75",
            justify="left",
            wraplength=400
        )
        self.optim_level_help.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
        
        # TCP optimization frame
        self.tcp_frame = self._create_section_frame("TCP Optimization Settings", 3)
        
        # Create TCP optimization settings
        tcp_settings = [
            {
                "name": "tcp_window_size",
                "label": "TCP Window Size (bytes):",
                "default": 131072,
                "type": "slider",
                "min": 65535,
                "max": 524288,
                "step": 65535,
                "tooltip": "Size of the TCP receive window. Larger values can improve throughput on high-latency connections.",
                "format_func": lambda x: f"{int(x):,}"
            },
            {
                "name": "congestion_algorithm",
                "label": "Congestion Algorithm:",
                "default": "cubic",
                "type": "dropdown",
                "values": ["cubic", "bbr", "reno", "vegas"],
                "tooltip": "TCP congestion control algorithm. BBR is optimized for high-speed networks but may cause issues with some routers."
            },
            {
                "name": "tcp_autotuning",
                "label": "TCP Autotuning:",
                "default": True,
                "type": "switch",
                "tooltip": "Automatically adjust TCP parameters based on network conditions."
            }
        ]
        
        self._add_settings_to_frame(self.tcp_frame, tcp_settings, row_offset=1)
        
        # WiFi optimization frame
        self.wifi_frame = self._create_section_frame("WiFi Optimization Settings", 4)
        
        # Create WiFi optimization settings
        wifi_settings = [
            {
                "name": "channel_switching",
                "label": "Automatic Channel Switching:",
                "default": True,
                "type": "switch",
                "tooltip": "Automatically switch to the best WiFi channel with least interference."
            },
            {
                "name": "tx_power",
                "label": "Transmit Power:",
                "default": "high",
                "type": "dropdown",
                "values": ["auto", "low", "medium", "high", "max"],
                "tooltip": "WiFi transmit power. Higher values increase range but may cause interference and drain battery faster."
            },
            {
                "name": "roaming_aggressiveness",
                "label": "Roaming Aggressiveness:",
                "default": "medium",
                "type": "dropdown",
                "values": ["low", "medium", "high"],
                "tooltip": "How aggressively to switch between WiFi access points. Higher values may cause more frequent disconnections."
            },
            {
                "name": "band_preference",
                "label": "Band Preference:",
                "default": "5GHz",
                "type": "dropdown",
                "values": ["auto", "2.4GHz", "5GHz"],
                "tooltip": "Preferred WiFi frequency band. 5GHz is faster but has shorter range. 2.4GHz has better range but more interference."
            }
        ]
        
        self._add_settings_to_frame(self.wifi_frame, wifi_settings, row_offset=1)
        
        # DNS optimization frame
        self.dns_frame = self._create_section_frame("DNS Settings", 5)
        
        # Create DNS optimization settings
        dns_settings = [
            {
                "name": "dns_prefetching",
                "label": "DNS Prefetching:",
                "default": True,
                "type": "switch",
                "tooltip": "Preemptively resolve domain names to speed up browsing."
            },
            {
                "name": "dns_provider",
                "label": "DNS Provider:",
                "default": "cloudflare",
                "type": "dropdown",
                "values": ["auto", "cloudflare", "google", "quad9", "opendns", "custom"],
                "tooltip": "DNS provider to use. Different providers offer various speeds and privacy features."
            },
            {
                "name": "custom_dns",
                "label": "Custom DNS Servers:",
                "default": "1.1.1.1, 1.0.0.1",
                "type": "entry",
                "tooltip": "Comma-separated list of custom DNS server IP addresses (only used if DNS Provider is set to 'custom')."
            }
        ]
        
        self._add_settings_to_frame(self.dns_frame, dns_settings, row_offset=1)
        
        # Advanced features frame
        self.features_frame = self._create_section_frame("Advanced Features", 6)
        
        # Create advanced features settings
        feature_settings = [
            {
                "name": "deep_packet_inspection",
                "label": "Deep Packet Inspection:",
                "default": False,
                "type": "switch",
                "tooltip": "Analyze network traffic patterns to optimize performance. May impact privacy."
            },
            {
                "name": "bandwidth_control",
                "label": "Bandwidth Control:",
                "default": True,
                "type": "switch",
                "tooltip": "Manage bandwidth allocation between applications for better performance."
            },
            {
                "name": "packet_prioritization",
                "label": "Packet Prioritization:",
                "default": True,
                "type": "switch",
                "tooltip": "Prioritize important network traffic over background data."
            },
            {
                "name": "buffer_bloat_mitigation",
                "label": "Buffer Bloat Mitigation:",
                "default": True,
                "type": "switch",
                "tooltip": "Reduce network buffering that can cause lag and high latency."
            }
        ]
        
        self._add_settings_to_frame(self.features_frame, feature_settings, row_offset=1)
        
        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.grid(row=7, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(2, weight=1)
        
        # Create buttons
        self.reset_button = ctk.CTkButton(
            self.buttons_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
            fg_color="#F44336",
            hover_color="#D32F2F",
            width=150
        )
        self.reset_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.save_button = ctk.CTkButton(
            self.buttons_frame,
            text="Save Settings",
            command=self._save_settings,
            width=150
        )
        self.save_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        # Warning label
        self.warning_label = ctk.CTkLabel(
            self,
            text="⚠️ Warning: Extreme settings may cause network instability.\nSome settings may require administrator privileges to apply.",
            font=("Segoe UI", 12),
            text_color="#FFC107",
            anchor="w"
        )
        self.warning_label.grid(row=8, column=0, padx=20, pady=10, sticky="sw")
    
    def _create_section_frame(self, title: str, row: int) -> ctk.CTkFrame:
        """Create a section frame with a title."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=row, column=0, padx=20, pady=(10, 10), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        separator = ctk.CTkFrame(frame, height=1, fg_color="#555555")
        separator.grid(row=0, column=0, columnspan=2, padx=10, pady=(30, 0), sticky="ew")
        
        return frame
    
    def _add_settings_to_frame(self, frame: ctk.CTkFrame, settings: List[Dict[str, Any]], row_offset: int = 0):
        """Add settings to a frame."""
        for i, setting in enumerate(settings):
            row = i + row_offset
            name = setting["name"]
            label_text = setting["label"]
            default = setting["default"]
            tooltip = setting.get("tooltip", "")
            
            # Create label
            label = ctk.CTkLabel(
                frame,
                text=label_text,
                font=("Segoe UI", 12),
                anchor="w"
            )
            label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            # Create widget based on type
            if setting["type"] == "switch":
                widget = ctk.CTkSwitch(
                    frame,
                    text="",
                    command=lambda n=name: self._on_setting_change(n)
                )
                widget.grid(row=row, column=1, padx=10, pady=5, sticky="e")
                if default:
                    widget.select()
                else:
                    widget.deselect()
            
            elif setting["type"] == "dropdown":
                widget = ctk.CTkOptionMenu(
                    frame,
                    values=setting["values"],
                    command=lambda v, n=name: self._on_setting_change(n, v)
                )
                widget.grid(row=row, column=1, padx=10, pady=5, sticky="e")
                widget.set(default)
            
            elif setting["type"] == "slider":
                value_label = ctk.CTkLabel(
                    frame,
                    text=setting.get("format_func", str)(default),
                    font=("Segoe UI", 12)
                )
                value_label.grid(row=row, column=1, padx=(10, 80), pady=5, sticky="e")
                
                widget = ctk.CTkSlider(
                    frame,
                    from_=setting["min"],
                    to=setting["max"],
                    number_of_steps=int((setting["max"] - setting["min"]) / setting["step"]),
                    command=lambda v, n=name, l=value_label, f=setting.get("format_func", str): 
                        self._on_slider_change(n, v, l, f)
                )
                widget.grid(row=row, column=1, padx=(120, 10), pady=5, sticky="w")
                widget.set(default)
                
            elif setting["type"] == "entry":
                widget = ctk.CTkEntry(
                    frame,
                    width=220
                )
                widget.grid(row=row, column=1, padx=10, pady=5, sticky="e")
                widget.insert(0, default)
                widget.bind("<FocusOut>", lambda e, n=name: self._on_entry_change(n, e))
            
            # Store widget for later access
            self.settings_widgets[name] = widget
            
            # Add tooltip if provided
            if tooltip:
                try:
                    CTkToolTip(widget, message=tooltip)
                except (ImportError, NotImplementedError, AttributeError) as e:
                    # Some widgets like CTkSegmentedButton don't support bind method
                    # Skip tooltip for these widgets
                    logger.debug(f"Could not add tooltip to widget: {e}")
                
                try:
                    CTkToolTip(label, message=tooltip)
                except (ImportError, NotImplementedError, AttributeError) as e:
                    # Skip tooltip if it fails
                    logger.debug(f"Could not add tooltip to label: {e}")
    
    def _on_setting_change(self, name: str, value=None):
        """Handle setting change event."""
        if self.callback:
            # Get the current value
            widget = self.settings_widgets[name]
            
            if isinstance(widget, ctk.CTkSwitch):
                value = widget.get() == 1
            elif isinstance(widget, ctk.CTkOptionMenu):
                value = widget.get()
            elif isinstance(widget, ctk.CTkSlider):
                value = widget.get()
            elif isinstance(widget, ctk.CTkEntry):
                value = widget.get()
            
            # Call the callback with name and value
            self.callback(name, value)
    
    def _on_slider_change(self, name: str, value: float, label: ctk.CTkLabel, format_func: Callable):
        """Handle slider change event."""
        # Update the label
        label.configure(text=format_func(value))
        
        # Call the callback
        if self.callback:
            self.callback(name, value)
    
    def _on_entry_change(self, name: str, event):
        """Handle entry change event."""
        if self.callback:
            widget = self.settings_widgets[name]
            value = widget.get()
            self.callback(name, value)
    
    def _on_optimization_level_change(self, value: str):
        """Handle optimization level change."""
        # Update settings based on optimization level
        level = value.lower()
        
        # Different presets for different levels
        if level == "light":
            self._set_preset_values({
                "tcp_window_size": 65535,
                "congestion_algorithm": "cubic",
                "tcp_autotuning": True,
                "channel_switching": True,
                "tx_power": "auto",
                "roaming_aggressiveness": "low",
                "band_preference": "auto",
                "dns_prefetching": True,
                "dns_provider": "auto",
                "deep_packet_inspection": False,
                "bandwidth_control": False,
                "packet_prioritization": False,
                "buffer_bloat_mitigation": True
            })
        elif level == "standard":
            self._set_preset_values({
                "tcp_window_size": 131072,
                "congestion_algorithm": "cubic",
                "tcp_autotuning": True,
                "channel_switching": True,
                "tx_power": "high",
                "roaming_aggressiveness": "medium",
                "band_preference": "5GHz",
                "dns_prefetching": True,
                "dns_provider": "cloudflare",
                "deep_packet_inspection": False,
                "bandwidth_control": True,
                "packet_prioritization": True,
                "buffer_bloat_mitigation": True
            })
        elif level == "aggressive":
            self._set_preset_values({
                "tcp_window_size": 262144,
                "congestion_algorithm": "bbr",
                "tcp_autotuning": True,
                "channel_switching": True,
                "tx_power": "high",
                "roaming_aggressiveness": "high",
                "band_preference": "5GHz",
                "dns_prefetching": True,
                "dns_provider": "cloudflare",
                "deep_packet_inspection": True,
                "bandwidth_control": True,
                "packet_prioritization": True,
                "buffer_bloat_mitigation": True
            })
        elif level == "extreme":
            self._set_preset_values({
                "tcp_window_size": 524288,
                "congestion_algorithm": "bbr",
                "tcp_autotuning": False,
                "channel_switching": True,
                "tx_power": "max",
                "roaming_aggressiveness": "high",
                "band_preference": "5GHz",
                "dns_prefetching": True,
                "dns_provider": "cloudflare",
                "deep_packet_inspection": True,
                "bandwidth_control": True,
                "packet_prioritization": True,
                "buffer_bloat_mitigation": True
            })
        
        # Call the callback for the optimization level
        if self.callback:
            self.callback("optimization_level", level)
    
    def _set_preset_values(self, values: Dict[str, Any]):
        """Set preset values for all settings."""
        for name, value in values.items():
            if name in self.settings_widgets:
                widget = self.settings_widgets[name]
                
                if isinstance(widget, ctk.CTkSwitch):
                    if value:
                        widget.select()
                    else:
                        widget.deselect()
                elif isinstance(widget, ctk.CTkOptionMenu):
                    widget.set(value)
                elif isinstance(widget, ctk.CTkSlider):
                    widget.set(value)
                    # Find and update the associated label
                    for child in widget.master.winfo_children():
                        if isinstance(child, ctk.CTkLabel) and child != widget.master.winfo_children()[0]:
                            format_func = lambda x: f"{int(x):,}"
                            child.configure(text=format_func(value))
                            break
                elif isinstance(widget, ctk.CTkEntry):
                    widget.delete(0, "end")
                    widget.insert(0, value)
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        # Set the optimization level back to Standard
        self.optim_level.set("Standard")
        
        # This will trigger the optimization level change event,
        # which will reset all other settings to their defaults
        self._on_optimization_level_change("Standard")
    
    def _save_settings(self):
        """Save all settings and apply them."""
        settings = self.get_all_settings()
        
        # Create a formatted string to summarize settings
        settings_text = "Settings saved:\n"
        for category, values in settings.items():
            settings_text += f"\n{category.upper()}:\n"
            for name, value in values.items():
                settings_text += f"  - {name}: {value}\n"
        
        # Show a dialog with the settings
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings Saved")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal
        
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        
        label = ctk.CTkLabel(
            dialog,
            text="Settings have been saved and will be applied on the next optimization run.",
            font=("Segoe UI", 14),
            wraplength=460
        )
        label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        text = ctk.CTkTextbox(dialog, font=("Segoe UI", 12))
        text.grid(row=1, column=0, padx=20, pady=(10, 10), sticky="nsew")
        text.insert("1.0", settings_text)
        text.configure(state="disabled")
        
        button = ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
            width=100
        )
        button.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="e")
        
        # Call the callback with all settings
        if self.callback:
            self.callback("all_settings", settings)
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get all settings as a dictionary."""
        # Get optimization level
        optimization_level = self.optim_level.get().lower()
        
        # Get all other settings
        tcp_settings = {}
        wifi_settings = {}
        dns_settings = {}
        advanced_features = {}
        
        for name, widget in self.settings_widgets.items():
            value = None
            
            if isinstance(widget, ctk.CTkSwitch):
                value = widget.get() == 1
            elif isinstance(widget, ctk.CTkOptionMenu):
                value = widget.get()
            elif isinstance(widget, ctk.CTkSlider):
                value = widget.get()
            elif isinstance(widget, ctk.CTkEntry):
                value = widget.get()
            
            # Categorize settings
            if name in ["tcp_window_size", "congestion_algorithm", "tcp_autotuning"]:
                tcp_settings[name] = value
            elif name in ["channel_switching", "tx_power", "roaming_aggressiveness", "band_preference"]:
                wifi_settings[name] = value
            elif name in ["dns_prefetching", "dns_provider", "custom_dns"]:
                dns_settings[name] = value
            elif name in ["deep_packet_inspection", "bandwidth_control", "packet_prioritization", "buffer_bloat_mitigation"]:
                advanced_features[name] = value
        
        return {
            "optimization_level": optimization_level,
            "tcp": tcp_settings,
            "wifi": wifi_settings,
            "dns": dns_settings,
            "features": advanced_features
        }
    
    def set_settings(self, settings: Dict[str, Any]):
        """Set settings from a dictionary."""
        # Set optimization level
        if "optimization_level" in settings:
            level = settings["optimization_level"]
            self.optim_level.set(level.capitalize())
        
        # Set all other settings
        for category, values in settings.items():
            if category == "optimization_level":
                continue
                
            for name, value in values.items():
                if name in self.settings_widgets:
                    widget = self.settings_widgets[name]
                    
                    if isinstance(widget, ctk.CTkSwitch):
                        if value:
                            widget.select()
                        else:
                            widget.deselect()
                    elif isinstance(widget, ctk.CTkOptionMenu):
                        widget.set(value)
                    elif isinstance(widget, ctk.CTkSlider):
                        widget.set(value)
                    elif isinstance(widget, ctk.CTkEntry):
                        widget.delete(0, "end")
                        widget.insert(0, value) 