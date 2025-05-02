"""
Tests for the logging module.
"""

import logging
import os
from unittest.mock import patch

import pytest

from src.utils.logging import get_logger, set_log_level, LOG_LEVELS


def test_get_logger_returns_logger_instance():
    """Test that get_logger returns a Logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


def test_get_logger_caches_loggers():
    """Test that get_logger caches loggers by name."""
    logger1 = get_logger("test_caching")
    logger2 = get_logger("test_caching")
    
    # Should be the same object
    assert logger1 is logger2


def test_get_logger_respects_environment_log_level():
    """Test that get_logger respects the LOG_LEVEL environment variable."""
    with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
        logger = get_logger("test_env_level")
        assert logger.level == logging.DEBUG
    
    with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
        logger = get_logger("test_env_level_error")
        assert logger.level == logging.ERROR


def test_set_log_level_changes_all_loggers():
    """Test that set_log_level changes the level of all existing loggers."""
    logger1 = get_logger("test_set_level_1")
    logger2 = get_logger("test_set_level_2")
    
    # Initial level should be INFO (default)
    assert logger1.level == logging.INFO
    assert logger2.level == logging.INFO
    
    # Change the level
    set_log_level("DEBUG")
    
    # Both loggers should have the new level
    assert logger1.level == logging.DEBUG
    assert logger2.level == logging.DEBUG
    
    # Reset to default level for other tests
    set_log_level("INFO")


def test_set_log_level_raises_value_error_for_invalid_level():
    """Test that set_log_level raises ValueError for invalid level."""
    with pytest.raises(ValueError):
        set_log_level("INVALID_LEVEL")


def test_logger_handlers_not_duplicated():
    """Test that get_logger doesn't add duplicate handlers."""
    logger_name = "test_no_duplicate_handlers"
    
    # Get logger initially
    logger = get_logger(logger_name)
    initial_handler_count = len(logger.handlers)
    
    # Get logger again
    logger = get_logger(logger_name)
    
    # Handler count should remain the same
    assert len(logger.handlers) == initial_handler_count 