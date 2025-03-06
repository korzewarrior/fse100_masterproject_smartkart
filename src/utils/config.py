#!/usr/bin/env python3
"""
Configuration module for Smart Kart
----------------------------------
Handles loading, parsing and accessing configuration settings.
"""

import os
import yaml
import logging
from pathlib import Path

class Config:
    """Configuration manager for the Smart Kart system."""
    
    DEFAULT_CONFIG = {
        'system': {
            'name': 'Smart Kart',
            'version': '0.1.0',
            'debug': False,
            'log_level': 'INFO',
            'simulation': False
        },
        'hardware': {
            'weight_sensor': {
                'enabled': True,
                'type': 'hx711',
                'dout_pin': 5,
                'sck_pin': 6,
                'reference_unit': 1,  # Calibration value
                'offset': 0,
                'threshold': 10  # Minimum weight difference to detect
            },
            'barcode_scanner': {
                'enabled': True,
                'type': 'camera',  # 'camera' or 'usb'
                'device': '/dev/video0',
                'timeout': 5
            },
            'rfid_reader': {
                'enabled': True,
                'type': 'mfrc522',
                'spi_bus': 0,
                'spi_device': 0,
                'reset_pin': 25
            },
            'camera': {
                'enabled': True,
                'resolution': [640, 480],
                'framerate': 30,
                'rotation': 0
            },
            'display': {
                'enabled': True,
                'type': 'lcd',  # 'lcd' or 'oled'
                'width': 800,
                'height': 480,
                'rotation': 0
            },
            'audio': {
                'enabled': True,
                'volume': 80
            },
            'button': {
                'enabled': True,
                'pins': [17, 18, 19]  # GPIO pins for buttons
            }
        },
        'network': {
            'wifi': {
                'enabled': True,
                'ssid': '',
                'password': ''
            },
            'bluetooth': {
                'enabled': False
            },
            'api': {
                'enabled': True,
                'host': '0.0.0.0',
                'port': 5000
            }
        },
        'features': {
            'ingredient_verification': {
                'enabled': True,
                'confidence_threshold': 0.7
            },
            'weight_verification': {
                'enabled': True,
                'tolerance': 0.1  # 10% tolerance
            }
        },
        'paths': {
            'data': 'data',
            'audio': 'assets/audio',
            'images': 'assets/images',
            'models': 'models'
        }
    }
    
    def __init__(self, config_file=None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration from file if provided
        if config_file and os.path.exists(config_file):
            self._load_from_file(config_file)
            logging.info(f"Configuration loaded from {config_file}")
        else:
            logging.warning(f"Config file not found or not specified. Using default configuration.")
            
        # Ensure paths are absolute
        self._resolve_paths()
    
    def _load_from_file(self, config_file):
        """Load configuration from YAML file and merge with defaults."""
        try:
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                
            # Deep merge with default config
            self._deep_update(self.config, file_config)
        except Exception as e:
            logging.error(f"Error loading config file: {e}")
    
    def _deep_update(self, target, source):
        """Recursively update nested dictionaries."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _resolve_paths(self):
        """Convert relative paths to absolute paths."""
        project_root = Path(__file__).parent.parent.parent
        paths = self.config['paths']
        
        for key, path in paths.items():
            if not os.path.isabs(path):
                paths[key] = os.path.join(project_root, path)
                
        # Ensure directories exist
        for path in paths.values():
            os.makedirs(path, exist_ok=True)
    
    def get(self, key_path, default=None):
        """
        Get a configuration value using dot notation path.
        
        Args:
            key_path: Dot-separated path to the config value (e.g., 'hardware.camera.enabled')
            default: Default value to return if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path, value):
        """Set a configuration value using dot notation path."""
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the nested dictionary
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
    
    def save(self, config_file):
        """Save current configuration to file."""
        try:
            with open(config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logging.info(f"Configuration saved to {config_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving config file: {e}")
            return False 