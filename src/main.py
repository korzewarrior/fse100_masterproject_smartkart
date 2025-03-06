#!/usr/bin/env python3
"""
Smart Kart - Main Application
-----------------------------
This is the main entry point for the Smart Kart application.
It initializes all necessary components and starts the system.
"""

import os
import sys
import time
import logging
import argparse
import signal
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import Smart Kart modules
from src.controllers.system_controller import SystemController
from src.utils.config import Config
from src.utils.logger import setup_logger

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    """Handle termination signals and shut down gracefully."""
    logging.info("Shutdown signal received. Exiting...")
    if 'controller' in globals():
        controller.shutdown()
    sys.exit(0)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Smart Kart - Intelligent Shopping Cart System")
    parser.add_argument('-c', '--config', default='config.yaml', help='Path to config file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-s', '--simulation', action='store_true', help='Run in simulation mode (no hardware)')
    return parser.parse_args()

def main():
    """Main application entry point."""
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(level=log_level)
    
    logging.info("Starting Smart Kart system...")
    
    try:
        # Load configuration
        config_path = os.path.join(project_root, args.config)
        config = Config(config_path)
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Initialize the system controller
        global controller
        controller = SystemController(config, simulation_mode=args.simulation)
        
        # Start the system
        controller.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        logging.exception("Exception details:")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 