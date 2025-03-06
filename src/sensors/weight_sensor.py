#!/usr/bin/env python3
"""
Weight Sensor Module
-------------------
Interfaces with load cells for detecting and verifying product weight.
"""

import time
import logging
import threading
from enum import Enum

# Import the appropriate HX711 library depending on simulation mode
try:
    import RPi.GPIO as GPIO
    from adafruit_hx711 import HX711
    SIMULATION_MODE = False
except (ImportError, RuntimeError):
    SIMULATION_MODE = True
    
logger = logging.getLogger(__name__)

class WeightState(Enum):
    """Possible states of the weight sensor."""
    STABLE = 0
    CHANGING = 1
    ITEM_ADDED = 2
    ITEM_REMOVED = 3
    ERROR = 4

class WeightSensor:
    """
    Interface for weight sensors using HX711 load cell amplifier.
    Designed to detect weight changes when items are added or removed.
    """
    
    def __init__(self, config, simulation_mode=False):
        """
        Initialize the weight sensor.
        
        Args:
            config: Configuration object with weight sensor settings
            simulation_mode: If True, operate in simulation mode
        """
        self.config = config
        self.simulation_mode = simulation_mode or SIMULATION_MODE
        
        # Current sensor data
        self.current_weight = 0.0
        self.last_stable_weight = 0.0
        self.state = WeightState.STABLE
        self.last_measurement_time = 0
        
        # Configuration values
        self.enabled = config.get('hardware.weight_sensor.enabled', True)
        self.threshold = config.get('hardware.weight_sensor.threshold', 10)
        self.reference_unit = config.get('hardware.weight_sensor.reference_unit', 1)
        self.offset = config.get('hardware.weight_sensor.offset', 0)
        
        # GPIO pins
        self.dout_pin = config.get('hardware.weight_sensor.dout_pin', 5)
        self.sck_pin = config.get('hardware.weight_sensor.sck_pin', 6)
        
        # HX711 object
        self.hx = None
        
        # Callback function for weight changes
        self.weight_change_callback = None
        
        # Threading for continuous monitoring
        self.monitoring = False
        self.monitoring_thread = None
        
        # Initialize sensor if enabled
        if self.enabled:
            self._initialize_sensor()
    
    def _initialize_sensor(self):
        """Initialize the HX711 sensor."""
        if self.simulation_mode:
            logger.info("Weight sensor running in simulation mode")
            return
        
        try:
            # Initialize the HX711 module
            GPIO.setmode(GPIO.BCM)
            self.hx = HX711(self.dout_pin, self.sck_pin)
            
            # Set the scale and tare
            if self.reference_unit != 1:
                self.hx.set_scale(self.reference_unit)
            
            logger.info("Taring weight sensor...")
            self.tare()
            logger.info("Weight sensor initialized and tared")
            
        except Exception as e:
            logger.error(f"Failed to initialize weight sensor: {e}")
            self.hx = None
    
    def tare(self):
        """Tare the scale (set current weight as zero)."""
        if self.simulation_mode or not self.hx:
            self.current_weight = 0
            self.last_stable_weight = 0
            logger.debug("Simulation: Taring weight sensor")
            return
        
        try:
            # Take multiple readings for accuracy
            self.hx.tare()
            self.current_weight = 0
            self.last_stable_weight = 0
            logger.info("Weight sensor tared successfully")
            return True
        except Exception as e:
            logger.error(f"Error taring weight sensor: {e}")
            return False
    
    def get_weight(self):
        """
        Get the current weight reading.
        
        Returns:
            Current weight in grams
        """
        if self.simulation_mode or not self.hx:
            # In simulation mode, return the current simulated weight
            logger.debug(f"Simulation: Current weight is {self.current_weight}g")
            return self.current_weight
        
        try:
            # Get weight from sensor
            raw_weight = self.hx.get_weight()
            
            # Apply offset and calibration
            weight = raw_weight - self.offset
            
            self.current_weight = weight
            self.last_measurement_time = time.time()
            
            logger.debug(f"Current weight: {weight}g")
            return weight
        except Exception as e:
            logger.error(f"Error reading weight: {e}")
            self.state = WeightState.ERROR
            return None
    
    def detect_weight_change(self):
        """
        Detect if there has been a significant weight change.
        
        Returns:
            WeightState indicating the current state
        """
        # Get current weight
        current = self.get_weight()
        if current is None:
            return WeightState.ERROR
        
        # Calculate absolute difference from last stable weight
        diff = current - self.last_stable_weight
        
        # Determine state based on weight difference
        if abs(diff) < self.threshold:
            # No significant change
            if self.state == WeightState.CHANGING:
                # Weight was changing but has now stabilized
                self.last_stable_weight = current
            
            self.state = WeightState.STABLE
        else:
            # Significant change detected
            if diff > 0:
                # Weight increase (item added)
                self.state = WeightState.ITEM_ADDED
            else:
                # Weight decrease (item removed)
                self.state = WeightState.ITEM_REMOVED
            
            # If weight change is first detected, update state to changing
            if self.state != WeightState.CHANGING:
                self.state = WeightState.CHANGING
        
        return self.state
    
    def start_monitoring(self, callback=None, interval=0.5):
        """
        Start continuous monitoring of weight changes.
        
        Args:
            callback: Function to call when weight change is detected
            interval: Time between weight checks in seconds
        """
        if callback:
            self.weight_change_callback = callback
        
        if self.monitoring:
            logger.warning("Weight monitoring already active")
            return
        
        self.monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Weight monitoring started")
    
    def _monitoring_loop(self, interval):
        """Background thread for continuous weight monitoring."""
        while self.monitoring:
            state = self.detect_weight_change()
            
            # Call callback if weight changed and callback exists
            if state in [WeightState.ITEM_ADDED, WeightState.ITEM_REMOVED]:
                if self.weight_change_callback:
                    self.weight_change_callback(state, self.current_weight, self.last_stable_weight)
            
            # If state is stable now, update the last stable weight
            if state == WeightState.STABLE:
                self.last_stable_weight = self.current_weight
            
            time.sleep(interval)
    
    def stop_monitoring(self):
        """Stop the continuous weight monitoring."""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)
            logger.info("Weight monitoring stopped")
    
    def simulate_weight_change(self, weight):
        """
        Simulate a weight change (for testing or simulation mode).
        
        Args:
            weight: New weight to simulate
        """
        old_weight = self.current_weight
        self.current_weight = weight
        logger.debug(f"Simulated weight change: {old_weight}g -> {weight}g")
        
        # If monitoring, trigger the callback
        if self.monitoring and self.weight_change_callback:
            if weight > old_weight + self.threshold:
                self.weight_change_callback(
                    WeightState.ITEM_ADDED, weight, old_weight
                )
            elif weight < old_weight - self.threshold:
                self.weight_change_callback(
                    WeightState.ITEM_REMOVED, weight, old_weight
                )
    
    def shutdown(self):
        """Clean shutdown of the weight sensor."""
        self.stop_monitoring()
        
        if not self.simulation_mode and self.hx:
            try:
                # Clean up GPIO
                GPIO.cleanup()
                logger.info("Weight sensor shut down cleanly")
            except Exception as e:
                logger.error(f"Error shutting down weight sensor: {e}")


# Example usage
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Simple config for testing
    from src.utils.config import Config
    config = Config()
    
    # Create sensor instance in simulation mode
    sensor = WeightSensor(config, simulation_mode=True)
    
    # Define a callback function
    def weight_callback(state, current, previous):
        print(f"Weight changed: {state}, Current: {current}g, Previous: {previous}g")
    
    # Start monitoring
    sensor.start_monitoring(callback=weight_callback)
    
    # Simulate weight changes
    time.sleep(1)
    sensor.simulate_weight_change(100)
    time.sleep(1)
    sensor.simulate_weight_change(250)
    time.sleep(1)
    sensor.simulate_weight_change(200)
    time.sleep(1)
    
    # Stop monitoring and shutdown
    sensor.stop_monitoring()
    sensor.shutdown() 