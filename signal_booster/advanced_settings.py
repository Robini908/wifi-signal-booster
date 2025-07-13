"""
Advanced settings for Signal Booster.
This module provides configuration options for network optimizations.
"""

import os
import sys
import platform
import logging
import json
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional, Union

logger = logging.getLogger(__name__)

class OptimizationLevel(Enum):
    """Optimization level enum."""
    LIGHT = "light"
    STANDARD = "standard" 
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"


class ConnectionType(Enum):
    """Connection type enum."""
    WIFI_2GHZ = "wifi_2ghz"
    WIFI_5GHZ = "wifi_5ghz"
    ETHERNET = "ethernet"
    MOBILE = "mobile"
    UNKNOWN = "unknown"


class AdvancedSettings:
    """Advanced settings manager for network optimizations."""
    
    def __init__(self, custom_config_file: Optional[str] = None):
        """
        Initialize the advanced settings manager.
        
        Args:
            custom_config_file: Path to a custom configuration file
        """
        self.config_path = custom_config_file or self._get_config_path()
        self.configs = self._load_default_configs()
        self.custom_configs = self._load_custom_configs()
        self.is_admin = self._check_admin_privileges()
        
    def _get_config_path(self) -> str:
        """Get the path to store configuration files."""
        if platform.system() == "Windows":
            base_dir = os.path.join(os.environ.get("APPDATA", ""), "SignalBooster")
        else:  # Linux/macOS
            base_dir = os.path.join(os.path.expanduser("~"), ".config", "signal-booster")
            
        # Ensure directory exists
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "advanced_config.json")
    
    def _check_admin_privileges(self) -> bool:
        """Check if the script is running with admin privileges."""
        try:
            if platform.system() == "Windows":
                try:
                    # Check for admin rights
                    import ctypes
                    return ctypes.windll.shell32.IsUserAnAdmin() != 0
                except:
                    return False
            else:  # Linux/macOS
                return os.geteuid() == 0
        except:
            return False
    
    def _load_default_configs(self) -> Dict[str, Any]:
        """Load default configurations for different optimization levels and connection types."""
        return {
            "tcp": self._get_default_tcp_configs(),
            "wifi": self._get_default_wifi_configs(),
            "dns": self._get_default_dns_configs(),
            "qos": self._get_default_qos_configs(),
            "buffer": self._get_default_buffer_configs(),
            "connection_specific": self._get_default_connection_configs(),
            "version": "1.0.0"
        }
    
    def _get_default_tcp_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default TCP configurations for different optimization levels."""
        return {
            OptimizationLevel.LIGHT.value: {
                "tcp_window_size": 65535,  # TCP window size in bytes
                "max_syn_backlog": 2048,   # SYN backlog
                "congestion_algorithm": "cubic"  # TCP congestion algorithm
            },
            OptimizationLevel.STANDARD.value: {
                "tcp_window_size": 131072,
                "max_syn_backlog": 4096,
                "congestion_algorithm": "cubic"
            },
            OptimizationLevel.AGGRESSIVE.value: {
                "tcp_window_size": 262144,
                "max_syn_backlog": 8192,
                "congestion_algorithm": "bbr"
            },
            OptimizationLevel.EXTREME.value: {
                "tcp_window_size": 524288,
                "max_syn_backlog": 16384,
                "congestion_algorithm": "bbr",
                "tcp_rmem": [4096, 131072, 6291456],
                "tcp_wmem": [4096, 16384, 4194304]
            }
        }
    
    def _get_default_wifi_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default WiFi configurations for different optimization levels."""
        return {
            OptimizationLevel.LIGHT.value: {
                "power_save": "off",
                "beacon_interval": 100,
                "txpower": "auto"
            },
            OptimizationLevel.STANDARD.value: {
                "power_save": "off",
                "beacon_interval": 50,
                "txpower": "high"
            },
            OptimizationLevel.AGGRESSIVE.value: {
                "power_save": "off",
                "beacon_interval": 30,
                "txpower": "max",
                "antenna_diversity": "on",
                "roaming_aggressiveness": "high"
            },
            OptimizationLevel.EXTREME.value: {
                "power_save": "off",
                "beacon_interval": 25,
                "txpower": "max",
                "antenna_diversity": "on",
                "roaming_aggressiveness": "highest",
                "preamble": "short",
                "channel_width": "40MHz"  # For 2.4GHz, 80MHz for 5GHz
            }
        }
    
    def _get_default_dns_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default DNS configurations for different optimization levels."""
        return {
            OptimizationLevel.LIGHT.value: {
                "nameservers": ["8.8.8.8", "8.8.4.4"],  # Google DNS
                "dns_cache_size": 512
            },
            OptimizationLevel.STANDARD.value: {
                "nameservers": ["1.1.1.1", "1.0.0.1"],  # Cloudflare DNS
                "dns_cache_size": 1024
            },
            OptimizationLevel.AGGRESSIVE.value: {
                "nameservers": ["9.9.9.9", "149.112.112.112"],  # Quad9 DNS
                "dns_cache_size": 2048,
                "dns_cache_ttl": 3600
            },
            OptimizationLevel.EXTREME.value: {
                "nameservers": ["1.1.1.1", "8.8.8.8"],  # Mix of fastest DNS servers
                "dns_cache_size": 4096,
                "dns_cache_ttl": 7200,
                "prefetch": True
            }
        }
    
    def _get_default_qos_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default QoS configurations for different optimization levels."""
        return {
            OptimizationLevel.LIGHT.value: {
                "enabled": False
            },
            OptimizationLevel.STANDARD.value: {
                "enabled": True,
                "prioritize_ack": True
            },
            OptimizationLevel.AGGRESSIVE.value: {
                "enabled": True,
                "prioritize_ack": True,
                "prioritize_dns": True,
                "priority_ports": [80, 443],  # HTTP/HTTPS
                "traffic_shaping": True
            },
            OptimizationLevel.EXTREME.value: {
                "enabled": True,
                "prioritize_ack": True,
                "prioritize_dns": True,
                "priority_ports": [80, 443, 53, 123],  # HTTP/HTTPS, DNS, NTP
                "traffic_shaping": True,
                "buffer_bloat_mitigation": True
            }
        }
    
    def _get_default_buffer_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default buffer configurations for different optimization levels."""
        return {
            OptimizationLevel.LIGHT.value: {
                "txqueuelen": 1000
            },
            OptimizationLevel.STANDARD.value: {
                "txqueuelen": 2000,
                "netdev_max_backlog": 2000
            },
            OptimizationLevel.AGGRESSIVE.value: {
                "txqueuelen": 5000,
                "netdev_max_backlog": 5000,
                "socket_buffer_size": 12582912
            },
            OptimizationLevel.EXTREME.value: {
                "txqueuelen": 10000,
                "netdev_max_backlog": 10000,
                "socket_buffer_size": 25165824,
                "tcp_moderate_rcvbuf": 0
            }
        }
    
    def _get_default_connection_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default connection-specific configurations."""
        return {
            ConnectionType.WIFI_2GHZ.value: {
                "channel_selection": "auto",
                "band_steering": False
            },
            ConnectionType.WIFI_5GHZ.value: {
                "channel_selection": "auto",
                "band_steering": True,
                "beamforming": True
            },
            ConnectionType.ETHERNET.value: {
                "jumbo_frames": False,
                "flow_control": True
            },
            ConnectionType.MOBILE.value: {
                "data_saver": False,
                "tcp_delayed_ack": False
            }
        }
    
    def _load_custom_configs(self) -> Dict[str, Any]:
        """Load custom configurations from disk."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading custom configurations: {e}")
            return {}
    
    def save_custom_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Save custom configurations to disk.
        
        Args:
            config_data: Configuration data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            self.custom_configs = config_data
            return True
        except Exception as e:
            logger.error(f"Error saving custom configurations: {e}")
            return False
    
    def get_config_for_level(self, 
                            level: Union[str, OptimizationLevel], 
                            connection_type: Union[str, ConnectionType] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific optimization level and connection type.
        
        Args:
            level: Optimization level
            connection_type: Connection type
            
        Returns:
            Configuration dictionary
        """
        # Convert string to enum if needed
        if isinstance(level, str):
            try:
                level = OptimizationLevel(level)
            except ValueError:
                logger.warning(f"Invalid optimization level: {level}. Using STANDARD.")
                level = OptimizationLevel.STANDARD
                
        if isinstance(connection_type, str) and connection_type:
            try:
                connection_type = ConnectionType(connection_type)
            except ValueError:
                logger.warning(f"Invalid connection type: {connection_type}. Using UNKNOWN.")
                connection_type = ConnectionType.UNKNOWN
        elif connection_type is None:
            connection_type = ConnectionType.UNKNOWN
            
        # Get level-specific config
        config = {}
        for category in self.configs:
            if category == "connection_specific":
                continue
            if category in self.configs and level.value in self.configs[category]:
                config[category] = self.configs[category][level.value].copy()
                
        # Add connection-specific config
        if connection_type.value in self.configs["connection_specific"]:
            config["connection_specific"] = self.configs["connection_specific"][connection_type.value].copy()
            
        # Override with custom config if available
        self._merge_configs(config, self.custom_configs)
        
        return config
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> None:
        """
        Merge override_config into base_config, modifying base_config.
        
        Args:
            base_config: Base configuration dictionary
            override_config: Override configuration dictionary
        """
        for category in base_config:
            if category in override_config:
                for key, value in override_config[category].items():
                    base_config[category][key] = value
                    
    def detect_connection_type(self) -> ConnectionType:
        """
        Detect the current connection type.
        
        Returns:
            ConnectionType enum
        """
        from signal_booster.network.interfaces import get_network_interfaces
        
        try:
            interfaces = get_network_interfaces()
            active_interface = None
            
            # Find active interface (one with IP address)
            for name, details in interfaces.items():
                if details.get('ip_address'):
                    active_interface = name
                    
                    # Check if it's wireless
                    if details.get('is_wireless'):
                        # Determine if it's 2.4GHz or 5GHz
                        # This is a simplification, in a real implementation we'd
                        # query more detailed wireless info
                        from signal_booster.network.utils import get_wifi_signal_strength
                        
                        # Try to determine band from channel number
                        # Channels 1-14 are 2.4GHz, 36+ are 5GHz
                        if platform.system() == "Windows":
                            stdout, stderr, returncode = self._run_cmd([
                                "netsh", "wlan", "show", "interfaces"
                            ])
                            
                            if stdout:
                                channel_match = re.search(r"Channel\s*:\s*(\d+)", stdout)
                                if channel_match:
                                    channel = int(channel_match.group(1))
                                    if channel <= 14:
                                        return ConnectionType.WIFI_2GHZ
                                    else:
                                        return ConnectionType.WIFI_5GHZ
                        
                        # For simplicity, assume 2.4GHz as a fallback
                        return ConnectionType.WIFI_2GHZ
                    else:
                        return ConnectionType.ETHERNET
            
            # If no interface with IP was found
            return ConnectionType.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error detecting connection type: {e}")
            return ConnectionType.UNKNOWN
            
    def _run_cmd(self, cmd: List[str]) -> Tuple[Optional[str], Optional[str], int]:
        """
        Run a system command.
        
        Args:
            cmd: Command to run
            
        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        try:
            result = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            logger.error(f"Error running command {cmd}: {e}")
            return None, str(e), 1
            
    def apply_optimizations(self, level: Union[str, OptimizationLevel],
                            connection_type: Optional[Union[str, ConnectionType]] = None) -> Dict[str, Any]:
        """
        Apply optimizations based on the specified level and connection type.
        
        Args:
            level: Optimization level
            connection_type: Connection type (if None, it will be auto-detected)
            
        Returns:
            Dictionary with results of applied optimizations
        """
        if connection_type is None:
            connection_type = self.detect_connection_type()
            
        # Get the configuration for this level and connection type
        config = self.get_config_for_level(level, connection_type)
        
        # Apply the optimizations based on the platform
        results = {
            "success": True,
            "applied_optimizations": [],
            "failed_optimizations": []
        }
        
        try:
            if platform.system() == "Windows":
                self._apply_windows_optimizations(config, results)
            elif platform.system() == "Linux":
                self._apply_linux_optimizations(config, results)
            elif platform.system() == "Darwin":  # macOS
                self._apply_macos_optimizations(config, results)
        except Exception as e:
            logger.error(f"Error applying optimizations: {e}")
            results["success"] = False
            results["error"] = str(e)
            
        return results
        
    def _apply_windows_optimizations(self, config: Dict[str, Any], results: Dict[str, Any]) -> None:
        """
        Apply optimizations on Windows.
        
        Args:
            config: Configuration dictionary
            results: Results dictionary to update
        """
        from signal_booster.network.platform.windows import set_windows_dns
        
        # Apply TCP optimizations if in config
        if "tcp" in config:
            try:
                from signal_booster.network.optimizers import optimize_tcp_settings
                if optimize_tcp_settings():
                    results["applied_optimizations"].append("TCP settings")
                else:
                    results["failed_optimizations"].append("TCP settings")
            except Exception as e:
                logger.error(f"Error applying TCP optimizations: {e}")
                results["failed_optimizations"].append("TCP settings")
                
        # Apply DNS optimizations if in config
        if "dns" in config and "nameservers" in config["dns"]:
            try:
                dns_servers = config["dns"]["nameservers"]
                if set_windows_dns(dns_servers):
                    results["applied_optimizations"].append("DNS settings")
                else:
                    results["failed_optimizations"].append("DNS settings")
            except Exception as e:
                logger.error(f"Error applying DNS optimizations: {e}")
                results["failed_optimizations"].append("DNS settings")
                
        # Apply WiFi optimizations if connection type is WiFi
        if "wifi" in config and self.detect_connection_type() in [ConnectionType.WIFI_2GHZ, ConnectionType.WIFI_5GHZ]:
            try:
                from signal_booster.network.optimizers import optimize_wifi_settings
                if optimize_wifi_settings():
                    results["applied_optimizations"].append("WiFi settings")
                else:
                    results["failed_optimizations"].append("WiFi settings")
            except Exception as e:
                logger.error(f"Error applying WiFi optimizations: {e}")
                results["failed_optimizations"].append("WiFi settings")
                
        # Apply QoS optimizations if enabled
        if "qos" in config and config["qos"].get("enabled", False):
            try:
                from signal_booster.network.optimizers import prioritize_traffic
                if prioritize_traffic():
                    results["applied_optimizations"].append("QoS settings")
                else:
                    results["failed_optimizations"].append("QoS settings")
            except Exception as e:
                logger.error(f"Error applying QoS optimizations: {e}")
                results["failed_optimizations"].append("QoS settings")
                
        # Apply system optimizations
        try:
            from signal_booster.network.optimizers import optimize_system_for_networking
            if optimize_system_for_networking():
                results["applied_optimizations"].append("System settings")
            else:
                results["failed_optimizations"].append("System settings")
        except Exception as e:
            logger.error(f"Error applying system optimizations: {e}")
            results["failed_optimizations"].append("System settings")
            
    def _apply_linux_optimizations(self, config: Dict[str, Any], results: Dict[str, Any]) -> None:
        """
        Apply optimizations on Linux.
        
        Args:
            config: Configuration dictionary
            results: Results dictionary to update
        """
        from signal_booster.network.platform.linux import set_linux_dns
        
        # Similar to Windows implementation, but with Linux-specific calls
        # Apply TCP optimizations if in config
        if "tcp" in config:
            try:
                from signal_booster.network.optimizers import optimize_tcp_settings
                if optimize_tcp_settings():
                    results["applied_optimizations"].append("TCP settings")
                else:
                    results["failed_optimizations"].append("TCP settings")
            except Exception as e:
                logger.error(f"Error applying TCP optimizations: {e}")
                results["failed_optimizations"].append("TCP settings")
                
        # Apply DNS optimizations if in config
        if "dns" in config and "nameservers" in config["dns"]:
            try:
                dns_servers = config["dns"]["nameservers"]
                if set_linux_dns(dns_servers):
                    results["applied_optimizations"].append("DNS settings")
                else:
                    results["failed_optimizations"].append("DNS settings")
            except Exception as e:
                logger.error(f"Error applying DNS optimizations: {e}")
                results["failed_optimizations"].append("DNS settings")
                
        # Apply WiFi optimizations if connection type is WiFi
        if "wifi" in config and self.detect_connection_type() in [ConnectionType.WIFI_2GHZ, ConnectionType.WIFI_5GHZ]:
            try:
                from signal_booster.network.optimizers import optimize_wifi_settings
                if optimize_wifi_settings():
                    results["applied_optimizations"].append("WiFi settings")
                else:
                    results["failed_optimizations"].append("WiFi settings")
            except Exception as e:
                logger.error(f"Error applying WiFi optimizations: {e}")
                results["failed_optimizations"].append("WiFi settings")
                
        # Apply QoS optimizations if enabled
        if "qos" in config and config["qos"].get("enabled", False):
            try:
                from signal_booster.network.optimizers import prioritize_traffic
                if prioritize_traffic():
                    results["applied_optimizations"].append("QoS settings")
                else:
                    results["failed_optimizations"].append("QoS settings")
            except Exception as e:
                logger.error(f"Error applying QoS optimizations: {e}")
                results["failed_optimizations"].append("QoS settings")
                
        # Apply system optimizations
        try:
            from signal_booster.network.optimizers import optimize_system_for_networking
            if optimize_system_for_networking():
                results["applied_optimizations"].append("System settings")
            else:
                results["failed_optimizations"].append("System settings")
        except Exception as e:
            logger.error(f"Error applying system optimizations: {e}")
            results["failed_optimizations"].append("System settings")
            
    def _apply_macos_optimizations(self, config: Dict[str, Any], results: Dict[str, Any]) -> None:
        """
        Apply optimizations on macOS.
        
        Args:
            config: Configuration dictionary
            results: Results dictionary to update
        """
        from signal_booster.network.platform.macos import set_macos_dns
        
        # Similar to Windows implementation, but with macOS-specific calls
        # Apply TCP optimizations if in config
        if "tcp" in config:
            try:
                from signal_booster.network.optimizers import optimize_tcp_settings
                if optimize_tcp_settings():
                    results["applied_optimizations"].append("TCP settings")
                else:
                    results["failed_optimizations"].append("TCP settings")
            except Exception as e:
                logger.error(f"Error applying TCP optimizations: {e}")
                results["failed_optimizations"].append("TCP settings")
                
        # Apply DNS optimizations if in config
        if "dns" in config and "nameservers" in config["dns"]:
            try:
                dns_servers = config["dns"]["nameservers"]
                if set_macos_dns(dns_servers):
                    results["applied_optimizations"].append("DNS settings")
                else:
                    results["failed_optimizations"].append("DNS settings")
            except Exception as e:
                logger.error(f"Error applying DNS optimizations: {e}")
                results["failed_optimizations"].append("DNS settings")
                
        # Apply WiFi optimizations if connection type is WiFi
        if "wifi" in config and self.detect_connection_type() in [ConnectionType.WIFI_2GHZ, ConnectionType.WIFI_5GHZ]:
            try:
                from signal_booster.network.optimizers import optimize_wifi_settings
                if optimize_wifi_settings():
                    results["applied_optimizations"].append("WiFi settings")
                else:
                    results["failed_optimizations"].append("WiFi settings")
            except Exception as e:
                logger.error(f"Error applying WiFi optimizations: {e}")
                results["failed_optimizations"].append("WiFi settings")
                
        # Apply QoS optimizations if enabled
        if "qos" in config and config["qos"].get("enabled", False):
            try:
                from signal_booster.network.optimizers import prioritize_traffic
                if prioritize_traffic():
                    results["applied_optimizations"].append("QoS settings")
                else:
                    results["failed_optimizations"].append("QoS settings")
            except Exception as e:
                logger.error(f"Error applying QoS optimizations: {e}")
                results["failed_optimizations"].append("QoS settings")
                
        # Apply system optimizations
        try:
            from signal_booster.network.optimizers import optimize_system_for_networking
            if optimize_system_for_networking():
                results["applied_optimizations"].append("System settings")
            else:
                results["failed_optimizations"].append("System settings")
        except Exception as e:
            logger.error(f"Error applying system optimizations: {e}")
            results["failed_optimizations"].append("System settings") 