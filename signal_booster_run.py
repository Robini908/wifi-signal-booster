#!/usr/bin/env python3
"""
Standalone script to run the Signal Booster GUI
with enhanced error handling
"""

import os
import sys
import logging
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("signal_booster.log", mode="a")
    ]
)
logger = logging.getLogger("SignalBoosterLauncher")

def check_and_install_dependencies():
    """Check and install required dependencies."""
    try:
        # Basic dependencies
        dependencies = [
            "customtkinter>=5.2.0",
            "matplotlib>=3.7.0",
            "pandas>=2.0.0",
            "pillow>=9.5.0",
            "plotly>=5.14.0",
            "kaleido>=0.2.1",
            "darkdetect>=0.8.0"
        ]
        
        # Try importing essential modules
        try:
            import customtkinter
            import matplotlib
            import pandas
            logger.info("Basic dependencies are already installed")
        except ImportError as e:
            logger.warning(f"Missing dependency: {e}")
            logger.info("Installing required dependencies...")
            
            # Install dependencies
            import subprocess
            cmd = [sys.executable, "-m", "pip", "install"] + dependencies
            logger.debug(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Failed to install dependencies: {result.stderr}")
                return False
            
            logger.info("Dependencies installed successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error checking dependencies: {e}")
        return False

def run_application():
    """Run the Signal Booster GUI application."""
    logger.info("Starting Signal Booster Pro GUI")
    
    try:
        # Add current directory to path
        current_dir = Path(__file__).parent.absolute()
        sys.path.insert(0, str(current_dir))
        
        # Import and run the GUI
        try:
            from signal_booster.gui import run_gui
            logger.info("Launching GUI...")
            run_gui()
        except ImportError:
            logger.error("Failed to import signal_booster.gui module")
            print("\nError: Could not find the Signal Booster module.")
            print("Please make sure the application is properly installed.")
            print("You can reinstall it using: pip install -e .")
            return False
    except Exception as e:
        logger.error(f"Error running Signal Booster: {e}")
        print(f"\nError running Signal Booster: {e}")
        traceback.print_exc()
        return False
    
    return True

def main():
    """Main entry point."""
    print("\n=======================================")
    print("   Signal Booster Pro Launcher")
    print("=======================================\n")
    
    # Check and install dependencies
    if not check_and_install_dependencies():
        print("\nFailed to set up dependencies. Please check signal_booster.log for details.")
        input("Press Enter to exit...")
        return 1
    
    # Run the application
    if not run_application():
        print("\nSignal Booster failed to start. Please check signal_booster.log for details.")
        input("Press Enter to exit...")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 