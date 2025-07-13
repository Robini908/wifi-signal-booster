"""
Common utilities and imports for network modules.
"""

import os
import sys
import subprocess
import platform
import socket
import shutil
import re
import logging
from typing import List, Dict, Tuple, Optional, Any, Union

import psutil
import numpy as np

# Setup logger
logger = logging.getLogger(__name__)

# Try to import speedtest but don't fail if it's not available
try:
    import speedtest
    HAS_SPEEDTEST = True
except ImportError:
    logger.warning("speedtest-cli not available, speed testing functionality will be limited")
    HAS_SPEEDTEST = False

# Try to import netifaces but don't fail if it's not available
try:
    import netifaces
    HAS_NETIFACES = True
except ImportError:
    logger.warning("netifaces not available, network interface detection will be limited")
    HAS_NETIFACES = False

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import winreg
    except ImportError:
        import _winreg as winreg

def run_command(command, check=False, capture_output=True, universal_lines=True):
    """
    Run a system command and handle errors.
    
    Args:
        command: Command to run (list)
        check: Raise exception on failure
        capture_output: Capture stdout/stderr
        universal_lines: Return strings instead of bytes
        
    Returns:
        Tuple of (stdout, stderr, returncode)
    """
    try:
        if capture_output:
            result = subprocess.run(
                command,
                check=check,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=universal_lines
            )
            return result.stdout, result.stderr, result.returncode
        else:
            result = subprocess.run(
                command,
                check=check
            )
            return None, None, result.returncode
    except Exception as e:
        logger.error(f"Error running command {command}: {e}")
        return None, str(e), 1 