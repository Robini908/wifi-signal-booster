"""
Settings component for the Signal Booster GUI.
Allows users to configure network interfaces and optimization settings.
"""

import logging
import customtkinter as ctk
from typing import Dict, Any, List, Optional

from ..gui_utils import create_tooltip

logger = logging.getLogger(__name__)

class SettingsFrame(ctk.CTkFrame):
    """Settings frame for configuring the Signal Booster."""
    
    def __init__(self, master, interfaces: Dict[str, Dict[str, Any]] = None, **kwargs):
        """
        Initialize the settings frame.
        
        Args:
            master: Parent widget
            interfaces: Dictionary of available network interfaces
        """
        super().__init__(master, **kwargs)
        
        self.interfaces = interfaces or {}
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Add some space at the bottom
        
        # Create components
        self._create_components()
    
    def _create_components(self):
        """Create settings components."""
        # Network interface settings
        self.interface_frame = ctk.CTkFrame(self)
        self.interface_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.interface_frame.grid_columnconfigure(1, weight=1)
        
        # Interface frame title
        self.interface_title = ctk.CTkLabel(
            self.interface_frame,
            text="Network Interface",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.interface_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        # Interface selection
        self.interface_label = ctk.CTkLabel(
            self.interface_frame,
            text="Select Interface:",
            font=("Segoe UI", 12),
            anchor="w"
        )
        self.interface_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        interface_values = list(self.interfaces.keys()) if self.interfaces else ["No interfaces found"]
        
        self.interface_combo = ctk.CTkOptionMenu(
            self.interface_frame,
            values=interface_values,
            width=200,
            font=("Segoe UI", 12),
            dropdown_font=("Segoe UI", 12)
        )
        self.interface_combo.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        create_tooltip(self.interface_combo, "Select the network interface to optimize")
        
        # Interface details
        self.details_label = ctk.CTkLabel(
            self.interface_frame,
            text="Interface Details:",
            font=("Segoe UI", 12),
            anchor="w"
        )
        self.details_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        detail_text = "No interface selected"
        if self.interfaces and interface_values[0] != "No interfaces found":
            details = self.interfaces[interface_values[0]]
            ip = details.get('ip_address', 'Unknown')
            mac = details.get('mac_address', 'Unknown')
            is_wireless = "Yes" if details.get('is_wireless', False) else "No"
            detail_text = f"IP: {ip}\nMAC: {mac}\nWireless: {is_wireless}"
        
        self.details_text = ctk.CTkTextbox(
            self.interface_frame,
            height=60,
            font=("Segoe UI", 12),
            activate_scrollbars=False
        )
        self.details_text.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.details_text.insert("1.0", detail_text)
        self.details_text.configure(state="disabled")
        
        # Auto-start with Windows
        self.autostart_var = ctk.BooleanVar(value=False)
        self.autostart_check = ctk.CTkCheckBox(
            self.interface_frame,
            text="Start with Windows",
            font=("Segoe UI", 12),
            variable=self.autostart_var
        )
        self.autostart_check.grid(row=3, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="w")
        create_tooltip(self.autostart_check, "Start Signal Booster automatically when Windows starts")
        
        # Optimization settings
        self.optimization_frame = ctk.CTkFrame(self)
        self.optimization_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.optimization_frame.grid_columnconfigure(1, weight=1)
        
        # Optimization frame title
        self.optimization_title = ctk.CTkLabel(
            self.optimization_frame,
            text="Optimization Settings",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.optimization_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        
        # Enable specific optimizations
        self.dns_var = ctk.BooleanVar(value=True)
        self.dns_check = ctk.CTkCheckBox(
            self.optimization_frame,
            text="Optimize DNS Settings",
            font=("Segoe UI", 12),
            variable=self.dns_var
        )
        self.dns_check.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        create_tooltip(self.dns_check, "Configure faster DNS servers for better performance")
        
        self.tcp_var = ctk.BooleanVar(value=True)
        self.tcp_check = ctk.CTkCheckBox(
            self.optimization_frame,
            text="Optimize TCP/IP Stack",
            font=("Segoe UI", 12),
            variable=self.tcp_var
        )
        self.tcp_check.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        create_tooltip(self.tcp_check, "Optimize TCP settings for better throughput")
        
        self.wifi_var = ctk.BooleanVar(value=True)
        self.wifi_check = ctk.CTkCheckBox(
            self.optimization_frame,
            text="Optimize WiFi Settings",
            font=("Segoe UI", 12),
            variable=self.wifi_var
        )
        self.wifi_check.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        create_tooltip(self.wifi_check, "Optimize WiFi adapter settings for better signal")
        
        self.qos_var = ctk.BooleanVar(value=True)
        self.qos_check = ctk.CTkCheckBox(
            self.optimization_frame,
            text="Enable QoS (Quality of Service)",
            font=("Segoe UI", 12),
            variable=self.qos_var
        )
        self.qos_check.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        create_tooltip(self.qos_check, "Prioritize important network traffic")
        
        self.system_var = ctk.BooleanVar(value=True)
        self.system_check = ctk.CTkCheckBox(
            self.optimization_frame,
            text="System-level Optimizations",
            font=("Segoe UI", 12),
            variable=self.system_var
        )
        self.system_check.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        create_tooltip(self.system_check, "Optimize system settings for better network performance")
        
        # Apply button
        self.apply_button = ctk.CTkButton(
            self.optimization_frame,
            text="Apply Settings",
            font=("Segoe UI", 12, "bold"),
            height=32,
            corner_radius=8
        )
        self.apply_button.grid(row=6, column=1, padx=10, pady=(10, 10), sticky="e")
        create_tooltip(self.apply_button, "Apply these settings")
        
        # Advanced settings
        self.advanced_frame = ctk.CTkFrame(self)
        self.advanced_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Advanced frame title
        self.advanced_title = ctk.CTkLabel(
            self.advanced_frame,
            text="Advanced Settings",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.advanced_title.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Advanced frame description
        self.advanced_desc = ctk.CTkLabel(
            self.advanced_frame,
            text="These settings are for advanced users. Incorrect settings may cause network issues.",
            font=("Segoe UI", 11),
            text_color="gray70",
            anchor="w",
            wraplength=600
        )
        self.advanced_desc.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
    
    def get_selected_interface(self) -> str:
        """Get the selected network interface."""
        return self.interface_combo.get()
    
    def get_optimization_settings(self) -> Dict[str, bool]:
        """Get all optimization settings as a dictionary."""
        return {
            'dns': self.dns_var.get(),
            'tcp': self.tcp_var.get(),
            'wifi': self.wifi_var.get(),
            'qos': self.qos_var.get(),
            'system': self.system_var.get(),
            'autostart': self.autostart_var.get()
        }
    
    def update_interface_details(self, interface_name: str):
        """
        Update the interface details when a new interface is selected.
        
        Args:
            interface_name: Name of the selected interface
        """
        if interface_name in self.interfaces:
            details = self.interfaces[interface_name]
            ip = details.get('ip_address', 'Unknown')
            mac = details.get('mac_address', 'Unknown')
            is_wireless = "Yes" if details.get('is_wireless', False) else "No"
            detail_text = f"IP: {ip}\nMAC: {mac}\nWireless: {is_wireless}"
            
            self.details_text.configure(state="normal")
            self.details_text.delete("1.0", "end")
            self.details_text.insert("1.0", detail_text)
            self.details_text.configure(state="disabled") 