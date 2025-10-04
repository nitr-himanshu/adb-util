"""
ADB-UTIL - A comprehensive Python-based desktop application for Android Debug Bridge operations.

This package provides a modern GUI interface for Android device management, file operations,
logcat monitoring, and terminal access through ADB.
"""

__version__ = "0.1.0"
__author__ = "Himanshu Keshri"
__email__ = "thehimanshukeshri@gmail.com"
__license__ = "MIT"

# Import only essential components to avoid circular imports
from .utils import get_logger

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    
    # Essential utilities
    "get_logger",
]
