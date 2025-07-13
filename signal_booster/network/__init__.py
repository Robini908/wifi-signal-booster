"""
Network optimization package for Signal Booster.
This package provides specialized functions for network optimization and analysis.
"""

from signal_booster.network.utils import (
    get_default_gateway,
    measure_latency,
    measure_speed,
    get_network_interfaces,
    set_dns_servers,
    find_optimal_mtu,
    get_wifi_signal_strength,
    find_best_wifi_channel
)

from signal_booster.network.optimizers import (
    optimize_tcp_settings,
    optimize_wifi_settings,
    prioritize_traffic,
    optimize_system_for_networking
)

from signal_booster.network.diagnostics import (
    check_for_malware,
    check_network_drivers
)

# Add new platform-specific measurement functions
from signal_booster.network.platform.dispatcher import (
    measure_jitter,
    measure_packet_loss,
    measure_bandwidth,
    analyze_network_congestion,
    clear_network_buffers,
    get_detailed_network_interfaces
) 