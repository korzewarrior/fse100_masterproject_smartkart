#!/usr/bin/env python3
"""
Smart Kart System Test Script
----------------------------
This script demonstrates the core functionality of the Smart Kart system
by simulating a shopping session.
"""

import os
import time
import logging
import argparse

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.controllers.system_controller import SystemController

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Smart Kart System Test")
    parser.add_argument('-c', '--config', default='config.yaml', help='Path to config file')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def main():
    """Main test function."""
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logger(level=log_level)
    
    # Print welcome message
    print("\n" + "="*60)
    print("SMART KART SYSTEM TEST")
    print("="*60)
    print("This test will simulate a shopping session with the Smart Kart system.")
    print("All sensors are simulated, no hardware required.")
    print("-"*60 + "\n")
    
    # Load configuration
    print("Loading configuration...")
    config = Config(args.config)
    
    # Always use simulation mode for this test
    config.set("system.simulation", True)
    
    # Initialize system controller
    print("Initializing Smart Kart system...")
    controller = SystemController(config, simulation_mode=True)
    
    try:
        # Start the system
        print("Starting Smart Kart system...")
        controller.start()
        time.sleep(1)
        
        # Tare the scale
        print("\nTaring the scale...")
        controller.tare_scale()
        time.sleep(1)
        
        # Simulate scanning product 1
        print("\nShopper scans a Design Patterns book...")
        controller.simulate_product_scan("9780201379624")
        time.sleep(1)
        
        # Get cart summary
        summary = controller.get_cart_summary()
        print(f"Cart contains {summary['items']} item(s):")
        for product in summary['products']:
            print(f"  - {product}")
        print(f"Total weight: {summary['total_weight']}g")
        print(f"Total price: ${summary['total_price']:.2f}")
        
        # Simulate scanning product 2
        print("\nShopper scans an Apple...")
        controller.simulate_product_scan("7501234567890")
        time.sleep(1)
        
        # Get updated cart summary
        summary = controller.get_cart_summary()
        print(f"Cart contains {summary['items']} item(s):")
        for product in summary['products']:
            print(f"  - {product}")
        print(f"Total weight: {summary['total_weight']}g")
        print(f"Total price: ${summary['total_price']:.2f}")
        
        # Simulate ingredient verification
        print("\nShopper checks if products contain milk...")
        milk_products = controller.verify_ingredient("milk")
        if milk_products:
            print(f"The following products contain milk: {', '.join(milk_products)}")
        else:
            print("None of the products in your cart contain milk.")
        
        # Simulate scanning product 3
        print("\nShopper scans a Milk carton...")
        controller.simulate_product_scan("5901234123457")
        time.sleep(1)
        
        # Get final cart summary
        summary = controller.get_cart_summary()
        print(f"Cart contains {summary['items']} item(s):")
        for product in summary['products']:
            print(f"  - {product}")
        print(f"Total weight: {summary['total_weight']}g")
        print(f"Total price: ${summary['total_price']:.2f}")
        
        # Verify milk again
        print("\nShopper checks again if products contain milk...")
        milk_products = controller.verify_ingredient("milk")
        if milk_products:
            print(f"The following products contain milk: {', '.join(milk_products)}")
        else:
            print("None of the products in your cart contain milk.")
        
        # Complete shopping
        print("\nShopping session complete!")
        print("-"*60)
        print("Final cart summary:")
        print(f"  Items: {summary['items']}")
        print(f"  Total weight: {summary['total_weight']}g")
        print(f"  Total price: ${summary['total_price']:.2f}")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError during test: {e}")
        logging.exception("Exception details:")
    finally:
        # Shutdown system
        print("\nShutting down Smart Kart system...")
        controller.shutdown()
        print("\nTest complete.")

if __name__ == "__main__":
    main() 