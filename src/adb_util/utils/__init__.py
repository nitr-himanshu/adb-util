"""
Utility functions and helpers.

This module provides utility functions, constants, validators, formatters,
and other helper functions used throughout the application.
"""

# Import only the most commonly used items to avoid circular imports
from .logger import get_logger
from .constants import APP_NAME, APP_VERSION

__all__ = [
    "get_logger",
    "APP_NAME",
    "APP_VERSION",
]
