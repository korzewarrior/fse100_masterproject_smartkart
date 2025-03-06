#!/usr/bin/env python3
"""
Barcode Scanner Module
---------------------
Provides functionality for scanning and reading barcodes/QR codes.
"""

import time
import logging
import threading
import cv2
import numpy as np
from pyzbar import pyzbar
from enum import Enum
from datetime import datetime

# Conditionally import picamera
try:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
    PICAMERA_AVAILABLE = True
except (ImportError, RuntimeError):
    PICAMERA_AVAILABLE = False

logger = logging.getLogger(__name__)

class BarcodeType(Enum):
    """Types of supported barcodes."""
    EAN13 = "EAN-13"
    EAN8 = "EAN-8"
    UPC = "UPC-A"
    UPCE = "UPC-E"
    CODE39 = "CODE39"
    CODE128 = "CODE128"
    QR = "QRCODE"
    UNKNOWN = "UNKNOWN"

class BarcodeScanner:
    """
    Class for handling barcode scanning operations using
    either the Raspberry Pi Camera or a USB camera.
    """
    
    def __init__(self, config, simulation_mode=False):
        """
        Initialize the barcode scanner.
        
        Args:
            config: Configuration object with barcode scanner settings
            simulation_mode: If True, operate in simulation mode
        """
        self.config = config
        self.simulation_mode = simulation_mode
        
        # Configuration
        self.enabled = config.get('hardware.barcode_scanner.enabled', True)
        self.scanner_type = config.get('hardware.barcode_scanner.type', 'camera')
        self.camera_device = config.get('hardware.barcode_scanner.device', '/dev/video0')
        self.timeout = config.get('hardware.barcode_scanner.timeout', 5)
        
        # Camera settings
        self.resolution = tuple(config.get('hardware.camera.resolution', [640, 480]))
        self.framerate = config.get('hardware.camera.framerate', 30)
        self.rotation = config.get('hardware.camera.rotation', 0)
        
        # Initialize variables
        self.camera = None
        self.video_capture = None
        self.scanning = False
        self.scan_thread = None
        self.last_scan_time = 0
        self.last_barcode = None
        self.last_image = None
        
        # Callback for scan events
        self.barcode_callback = None
        
        # Initialize the camera if enabled
        if self.enabled and not self.simulation_mode:
            self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize the camera based on configuration."""
        if self.simulation_mode:
            logger.info("Barcode scanner running in simulation mode")
            return
        
        try:
            if self.scanner_type == 'camera' and PICAMERA_AVAILABLE:
                # Use PiCamera
                self.camera = PiCamera()
                self.camera.resolution = self.resolution
                self.camera.framerate = self.framerate
                self.camera.rotation = self.rotation
                
                # Allow camera to warm up
                time.sleep(2)
                logger.info("PiCamera initialized for barcode scanning")
                
            else:
                # Use OpenCV with USB camera
                self.video_capture = cv2.VideoCapture(self.camera_device)
                self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                
                if not self.video_capture.isOpened():
                    logger.error(f"Failed to open camera device {self.camera_device}")
                    return
                
                logger.info(f"USB camera {self.camera_device} initialized for barcode scanning")
                
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            self.camera = None
            self.video_capture = None
    
    def scan_once(self):
        """
        Perform a single scan for barcodes.
        
        Returns:
            Tuple of (barcode_data, barcode_type) or (None, None) if no barcode found
        """
        if self.simulation_mode:
            logger.debug("Simulation: No real scanning performed")
            return None, None
        
        image = self._capture_image()
        if image is None:
            return None, None
        
        # Save the last image for debugging
        self.last_image = image
        
        # Process the image to detect barcodes
        return self._process_image(image)
    
    def _capture_image(self):
        """
        Capture an image from the camera.
        
        Returns:
            NumPy array containing the image data or None on error
        """
        try:
            if self.camera:  # PiCamera
                # Capture image to a NumPy array
                raw_capture = PiRGBArray(self.camera, size=self.resolution)
                self.camera.capture(raw_capture, format="bgr")
                return raw_capture.array
                
            elif self.video_capture:  # USB camera
                ret, frame = self.video_capture.read()
                if not ret:
                    logger.error("Failed to capture image from USB camera")
                    return None
                return frame
                
            else:
                logger.error("No camera initialized")
                return None
                
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None
    
    def _process_image(self, image):
        """
        Process an image to detect barcodes.
        
        Args:
            image: NumPy array with the image data
            
        Returns:
            Tuple of (barcode_data, barcode_type) or (None, None) if no barcode found
        """
        try:
            # Decode barcodes
            barcodes = pyzbar.decode(image)
            
            if barcodes:
                # We only handle the first detected barcode
                barcode = barcodes[0]
                
                # Extract data
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = BarcodeType.UNKNOWN
                
                # Determine the barcode type
                if barcode.type == 'QRCODE':
                    barcode_type = BarcodeType.QR
                elif barcode.type == 'EAN13':
                    barcode_type = BarcodeType.EAN13
                elif barcode.type == 'EAN8':
                    barcode_type = BarcodeType.EAN8
                elif barcode.type == 'UPCA':
                    barcode_type = BarcodeType.UPC
                elif barcode.type == 'CODE39':
                    barcode_type = BarcodeType.CODE39
                elif barcode.type == 'CODE128':
                    barcode_type = BarcodeType.CODE128
                
                logger.info(f"Detected {barcode_type.value} barcode: {barcode_data}")
                
                # Save the last scanned barcode
                self.last_barcode = (barcode_data, barcode_type)
                self.last_scan_time = time.time()
                
                # Optionally draw bounding box on image
                self._draw_barcode_box(image, barcode)
                
                return barcode_data, barcode_type
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error processing barcode image: {e}")
            return None, None
    
    def _draw_barcode_box(self, image, barcode):
        """
        Draw bounding box around the detected barcode (for debugging).
        
        Args:
            image: Image to draw on
            barcode: Detected barcode from pyzbar
        """
        # Extract bounding box information
        (x, y, w, h) = barcode.rect
        
        # Draw the bounding box
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Draw barcode data
        text = f"{barcode.type}: {barcode.data.decode('utf-8')}"
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 255, 0), 2)
    
    def start_scanning(self, callback=None, interval=0.5):
        """
        Start continuous scanning for barcodes.
        
        Args:
            callback: Function to call when a barcode is detected
            interval: Time between scans in seconds
        """
        if callback:
            self.barcode_callback = callback
        
        if self.scanning:
            logger.warning("Barcode scanning already active")
            return
        
        self.scanning = True
        self.scan_thread = threading.Thread(
            target=self._scanning_loop, 
            args=(interval,),
            daemon=True
        )
        self.scan_thread.start()
        logger.info("Continuous barcode scanning started")
    
    def _scanning_loop(self, interval):
        """Background thread for continuous barcode scanning."""
        while self.scanning:
            barcode_data, barcode_type = self.scan_once()
            
            # If we found a barcode and have a callback, call it
            if barcode_data and self.barcode_callback:
                self.barcode_callback(barcode_data, barcode_type)
            
            time.sleep(interval)
    
    def stop_scanning(self):
        """Stop the continuous barcode scanning."""
        self.scanning = False
        if self.scan_thread:
            self.scan_thread.join(timeout=1.0)
            logger.info("Barcode scanning stopped")
    
    def simulate_scan(self, barcode_data, barcode_type=BarcodeType.EAN13):
        """
        Simulate a barcode scan (for testing or simulation mode).
        
        Args:
            barcode_data: Barcode data to simulate
            barcode_type: Type of barcode to simulate
        """
        logger.debug(f"Simulated barcode scan: {barcode_data} ({barcode_type.value})")
        self.last_barcode = (barcode_data, barcode_type)
        self.last_scan_time = time.time()
        
        # If scanning and have a callback, call it
        if self.scanning and self.barcode_callback:
            self.barcode_callback(barcode_data, barcode_type)
    
    def save_last_image(self, filename=None):
        """
        Save the last captured image to a file (for debugging).
        
        Args:
            filename: Filename to save the image to
        
        Returns:
            Path to the saved image or None if no image
        """
        if self.last_image is None:
            logger.warning("No image to save")
            return None
        
        if filename is None:
            # Generate a filename based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"barcode_scan_{timestamp}.jpg"
        
        try:
            cv2.imwrite(filename, self.last_image)
            logger.info(f"Image saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return None
    
    def shutdown(self):
        """Clean shutdown of the barcode scanner."""
        self.stop_scanning()
        
        if self.camera:
            self.camera.close()
            logger.info("PiCamera closed")
            
        if self.video_capture:
            self.video_capture.release()
            logger.info("Video capture released")
        
        logger.info("Barcode scanner shut down cleanly")


# Example usage
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Simple config for testing
    from src.utils.config import Config
    config = Config()
    
    # Create scanner instance in simulation mode
    scanner = BarcodeScanner(config, simulation_mode=True)
    
    # Define a callback function
    def barcode_callback(barcode_data, barcode_type):
        print(f"Scanned barcode: {barcode_data} ({barcode_type.value})")
    
    # Start scanning
    scanner.start_scanning(callback=barcode_callback)
    
    # Simulate a few scans
    time.sleep(1)
    scanner.simulate_scan("9780201379624", BarcodeType.EAN13)
    time.sleep(1)
    scanner.simulate_scan("7501234567890", BarcodeType.EAN13)
    time.sleep(1)
    scanner.simulate_scan("https://example.com", BarcodeType.QR)
    time.sleep(1)
    
    # Stop scanning and shutdown
    scanner.stop_scanning()
    scanner.shutdown() 