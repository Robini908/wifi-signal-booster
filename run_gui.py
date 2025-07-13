#!/usr/bin/env python3
"""
Standalone script to run the Signal Booster GUI
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Signal Booster Pro GUI via standalone script")
    try:
        # Add current directory to path if needed
        sys.path.insert(0, os.path.abspath('.'))
        
        # Try to install required dependencies if they're missing
        try:
            import customtkinter
            import matplotlib
            import pandas
            import plotly
        except ImportError:
            logger.warning("Missing dependencies. Attempting to install...")
            import subprocess
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "customtkinter", "matplotlib", "pandas", "plotly", "pillow", "darkdetect", "kaleido"
            ])
            logger.info("Dependencies installed successfully")
        
        # Import and run the GUI
        from signal_booster.gui import run_gui
        logger.info("Imported GUI module, launching...")
        run_gui()
    except Exception as e:
        logger.exception(f"Error running GUI: {e}")
        print(f"Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 