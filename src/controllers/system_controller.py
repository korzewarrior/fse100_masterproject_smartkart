#!/usr/bin/env python3
"""
System Controller
----------------
Main controller for the Smart Kart system. This module integrates all
hardware and software components and handles the overall system logic.
"""

import time
import logging
import threading
from pathlib import Path

from src.sensors.weight_sensor import WeightSensor, WeightState
from src.sensors.barcode_scanner import BarcodeScanner, BarcodeType
from src.utils.logger import get_logger

# Conditionally import other components
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    
logger = get_logger(__name__)

class SystemController:
    """
    Main controller for the Smart Kart system.
    This class integrates all hardware and software components.
    """
    
    def __init__(self, config, simulation_mode=False):
        """
        Initialize the system controller.
        
        Args:
            config: Configuration object
            simulation_mode: If True, operate in simulation mode without hardware
        """
        self.config = config
        self.simulation_mode = simulation_mode
        self.running = False
        self.system_thread = None
        
        # Product tracking
        self.scanned_products = {}  # barcode -> product info
        self.cart_items = []        # list of items in cart
        self.total_weight = 0.0     # total weight of items in cart
        self.expected_weight = 0.0  # expected weight of all scanned items
        
        # Initialize components
        self._init_components()
        
        logger.info("System controller initialized")
    
    def _init_components(self):
        """Initialize all system components."""
        try:
            # Initialize weight sensor
            self.weight_sensor = WeightSensor(self.config, self.simulation_mode)
            
            # Initialize barcode scanner
            self.barcode_scanner = BarcodeScanner(self.config, self.simulation_mode)
            
            # TODO: Initialize other components as needed
            # self.rfid_reader = ...
            # self.display = ...
            # self.audio = ...
            # self.network = ...
            
            logger.info("All components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            logger.exception("Exception details:")
    
    def start(self):
        """Start the Smart Kart system."""
        if self.running:
            logger.warning("System already running")
            return
        
        logger.info("Starting Smart Kart system")
        self.running = True
        
        try:
            # Start weight sensor monitoring
            self.weight_sensor.start_monitoring(
                callback=self._on_weight_change
            )
            
            # Start barcode scanner
            self.barcode_scanner.start_scanning(
                callback=self._on_barcode_scanned
            )
            
            # Start main system thread
            self.system_thread = threading.Thread(
                target=self._system_loop,
                daemon=True
            )
            self.system_thread.start()
            
            logger.info("Smart Kart system started")
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            self.shutdown()
            raise
    
    def shutdown(self):
        """Gracefully shut down the system."""
        if not self.running:
            return
        
        logger.info("Shutting down Smart Kart system")
        self.running = False
        
        # Shut down all components
        if hasattr(self, 'weight_sensor'):
            self.weight_sensor.shutdown()
            
        if hasattr(self, 'barcode_scanner'):
            self.barcode_scanner.shutdown()
        
        # TODO: Shutdown other components
        
        if self.system_thread and self.system_thread.is_alive():
            self.system_thread.join(timeout=2.0)
        
        logger.info("Smart Kart system shut down")
    
    def _system_loop(self):
        """Main system loop running in a separate thread."""
        logger.info("System loop started")
        
        while self.running:
            # Main system logic
            self._check_cart_state()
            
            # Check if items in cart match scanned items
            self._verify_cart_contents()
            
            # Sleep to avoid consuming CPU
            time.sleep(0.5)
    
    def _check_cart_state(self):
        """Check the overall cart state."""
        pass  # Placeholder for system state checks
    
    def _verify_cart_contents(self):
        """Verify that items in cart match scanned items based on weight."""
        if not self.weight_sensor.enabled:
            return
        
        actual_weight = self.weight_sensor.current_weight
        weight_difference = abs(actual_weight - self.expected_weight)
        tolerance = self.config.get('features.weight_verification.tolerance', 0.1)
        
        # Calculate tolerance based on percentage of expected weight
        allowed_difference = self.expected_weight * tolerance
        
        if weight_difference > allowed_difference:
            # Weight discrepancy detected
            logger.warning(f"Weight discrepancy detected: Expected {self.expected_weight}g, "
                          f"Actual {actual_weight}g, Difference {weight_difference}g")
            # TODO: Alert user about discrepancy
        else:
            # Weights match within tolerance
            logger.debug(f"Cart weight verified: {actual_weight}g matches expected {self.expected_weight}g "
                        f"within tolerance of {allowed_difference}g")
    
    def _on_weight_change(self, state, current_weight, previous_weight):
        """
        Callback function for weight sensor changes.
        
        Args:
            state: WeightState indicating what changed
            current_weight: Current weight reading
            previous_weight: Previous stable weight reading
        """
        self.total_weight = current_weight
        
        if state == WeightState.ITEM_ADDED:
            logger.info(f"Item added: {current_weight - previous_weight}g, Total: {current_weight}g")
            # TODO: Verify that item was scanned before being added
            
        elif state == WeightState.ITEM_REMOVED:
            logger.info(f"Item removed: {previous_weight - current_weight}g, Total: {current_weight}g")
            # TODO: Update cart contents
    
    def _on_barcode_scanned(self, barcode_data, barcode_type):
        """
        Callback function for barcode scans.
        
        Args:
            barcode_data: Data from the barcode
            barcode_type: Type of barcode scanned
        """
        logger.info(f"Barcode scanned: {barcode_data} ({barcode_type.value})")
        
        # Look up product information (placeholder - would connect to a database)
        product_info = self._lookup_product(barcode_data)
        
        if product_info:
            # Add to scanned products
            self.scanned_products[barcode_data] = product_info
            
            # Add to cart items
            self.cart_items.append({
                'barcode': barcode_data,
                'product': product_info,
                'time_added': time.time()
            })
            
            # Update expected weight
            self.expected_weight += product_info.get('weight', 0)
            
            logger.info(f"Added product to cart: {product_info.get('name', 'Unknown')}")
            
            # TODO: Update display, play sound confirmation, etc.
        else:
            logger.warning(f"Product not found for barcode: {barcode_data}")
            # TODO: Alert user that product was not found
    
    def _lookup_product(self, barcode):
        """
        Look up product information from barcode.
        In a real system, this would query a database.
        
        Args:
            barcode: Product barcode
            
        Returns:
            Dictionary of product information or None if not found
        """
        # This is a placeholder. In a real implementation, this would query
        # a database or API for product information.
        
        # Dummy product database for testing
        dummy_products = {
            "9780201379624": {
                "name": "Design Patterns",
                "price": 49.99,
                "weight": 950,  # grams
                "description": "Elements of Reusable Object-Oriented Software"
            },
            "7501234567890": {
                "name": "Apple",
                "price": 1.99,
                "weight": 200,  # grams
                "description": "Fresh apple"
            },
            "5901234123457": {
                "name": "Milk",
                "price": 3.49,
                "weight": 1000,  # grams
                "description": "1L Milk carton"
            }
        }
        
        return dummy_products.get(barcode, None)
    
    def get_cart_summary(self):
        """
        Get a summary of the cart contents.
        
        Returns:
            Dictionary with cart summary information
        """
        total_price = sum(item['product'].get('price', 0) for item in self.cart_items)
        
        return {
            'items': len(self.cart_items),
            'total_weight': self.total_weight,
            'total_price': total_price,
            'products': [item['product'].get('name', 'Unknown') for item in self.cart_items]
        }
    
    def tare_scale(self):
        """Tare the weight scale to zero."""
        if self.weight_sensor.enabled:
            result = self.weight_sensor.tare()
            if result:
                logger.info("Scale tared successfully")
                self.total_weight = 0.0
                return True
            else:
                logger.error("Failed to tare scale")
                return False
        return False
    
    def verify_ingredient(self, ingredient_name):
        """
        Verify if a specific ingredient is present in any of the cart items.
        This would connect to an AI-based ingredient analysis system in a real implementation.
        
        Args:
            ingredient_name: Name of ingredient to verify
            
        Returns:
            List of products containing the ingredient
        """
        # Placeholder for ingredient verification
        # In a real implementation, this would connect to an AI system
        # that analyzes product labels for ingredients
        
        # Dummy implementation for testing
        containing_products = []
        
        for item in self.cart_items:
            product = item.get('product', {})
            # In a real implementation, product would have an 'ingredients' field
            # that would be checked against the requested ingredient
            if 'ingredients' in product and ingredient_name.lower() in [
                i.lower() for i in product['ingredients']
            ]:
                containing_products.append(product['name'])
        
        return containing_products
    
    def simulate_product_scan(self, barcode, product_info=None):
        """
        Simulate scanning a product (for testing).
        
        Args:
            barcode: Barcode to simulate
            product_info: Optional product info to add to database
        """
        if not self.simulation_mode:
            logger.warning("simulate_product_scan() only available in simulation mode")
            return
        
        # Add product to dummy database if provided
        if product_info:
            # In a real implementation, this would add to a database
            pass
        
        # Simulate barcode scan
        self.barcode_scanner.simulate_scan(barcode)
        
        # Simulate weight change if product info has weight
        product = self._lookup_product(barcode)
        if product and 'weight' in product:
            new_weight = self.weight_sensor.current_weight + product['weight']
            self.weight_sensor.simulate_weight_change(new_weight)


# Example usage
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Simple config for testing
    from src.utils.config import Config
    config = Config()
    
    # Create system controller in simulation mode
    controller = SystemController(config, simulation_mode=True)
    
    # Start the system
    controller.start()
    
    # Simulate scanning some products
    time.sleep(1)
    controller.simulate_product_scan("9780201379624")  # Design Patterns book
    time.sleep(1)
    controller.simulate_product_scan("7501234567890")  # Apple
    time.sleep(1)
    
    # Get cart summary
    summary = controller.get_cart_summary()
    print(f"Cart Summary: {summary}")
    
    # Shut down
    time.sleep(1)
    controller.shutdown() 