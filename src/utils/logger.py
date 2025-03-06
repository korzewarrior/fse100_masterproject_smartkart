#!/usr/bin/env python3
"""
Logging module for Smart Kart
----------------------------
Configures and provides logging functionality for the system.
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

def setup_logger(level=logging.INFO, log_file=None, console=True):
    """
    Configure the logging system for Smart Kart.
    
    Args:
        level: Logging level
        log_file: Path to log file (if None, defaults to logs/smartkart_YYYY-MM-DD.log)
        console: Whether to log to console
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(module)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if requested or use default
    if log_file is None:
        # Default log file path
        log_dir = Path(__file__).parent.parent.parent / 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = log_dir / f"smartkart_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    
    # Create rotating file handler (10 MB max, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Log startup message
    logging.info(f"Logging initialized at level {logging.getLevelName(level)}")
    logging.info(f"Log file: {log_file}")
    
    return logger

def get_logger(name):
    """
    Get a named logger.
    
    Args:
        name: Name for the logger
        
    Returns:
        Named logger instance
    """
    return logging.getLogger(name) 