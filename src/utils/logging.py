"""
Logging module for the Dental Email Assistant

This module provides a centralized logging configuration for the application.
It sets up console logging with a simple formatter and configurable log levels.
"""

import logging
import os
import sys
from typing import Dict, Optional

# Configure default log level
DEFAULT_LOG_LEVEL = "INFO"

# Map string log level names to their logging module constants
LOG_LEVELS: Dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Logger instances cache to avoid creating multiple loggers for the same name
_loggers: Dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name of the logger, typically __name__ of the calling module.
        
    Returns:
        A configured logger instance.
    """
    # Return cached logger if it exists
    if name in _loggers:
        return _loggers[name]
    
    # Get log level from environment or use default
    log_level_name = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    log_level = LOG_LEVELS.get(log_level_name, logging.INFO)
    
    # Create and configure logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Only add handlers if they don't exist already to prevent duplicate logs
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        # Create formatter with timestamp, level, and message
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    # Cache logger
    _loggers[name] = logger
    
    return logger


def set_log_level(level: str) -> None:
    """
    Set the log level for all loggers.
    
    Args:
        level: The log level to set (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    if level.upper() not in LOG_LEVELS:
        raise ValueError(f"Invalid log level: {level}. Must be one of {list(LOG_LEVELS.keys())}")
    
    log_level = LOG_LEVELS[level.upper()]
    
    # Update all existing loggers
    for logger in _loggers.values():
        logger.setLevel(log_level)
        for handler in logger.handlers:
            handler.setLevel(log_level) 