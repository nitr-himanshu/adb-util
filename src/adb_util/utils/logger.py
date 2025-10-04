"""
Logging Utility

Centralized logging configuration and utilities for the ADB-UTIL application.
Provides console and optional file logging with timestamp-based file names.
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import os

from .constants import (
    APP_NAME, APP_VERSION, DEFAULT_LOG_DIR, LOG_FORMAT, LOG_DATE_FORMAT,
    MAX_LOG_FILE_SIZE, LOG_BACKUP_COUNT, DEFAULT_FILE_LOGGING
)


class LoggerManager:
    """Manages application-wide logging configuration."""
    
    _instance: Optional['LoggerManager'] = None
    _loggers: Dict[str, logging.Logger] = {}
    _file_logging_enabled: bool = DEFAULT_FILE_LOGGING
    _log_directory: Path = DEFAULT_LOG_DIR
    _file_handler: Optional[logging.handlers.RotatingFileHandler] = None
    
    def __new__(cls) -> 'LoggerManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger manager."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._setup_log_directory()
    
    def _setup_log_directory(self):
        """Create log directory if it doesn't exist."""
        try:
            self._log_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create log directory {self._log_directory}: {e}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the specified name.
        
        Args:
            name: Logger name (typically module name)
            
        Returns:
            Configured logger instance
        """
        if name not in self._loggers:
            self._loggers[name] = self._create_logger(name)
        return self._loggers[name]
    
    def _create_logger(self, name: str) -> logging.Logger:
        """
        Create and configure a new logger.
        
        Args:
            name: Logger name
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(f"{APP_NAME}.{name}")
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if enabled
        if self._file_logging_enabled:
            self._add_file_handler(logger)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def _add_file_handler(self, logger: logging.Logger):
        """
        Add file handler to logger.
        
        Args:
            logger: Logger to add file handler to
        """
        if self._file_handler is None:
            # Create timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"{APP_NAME}_{timestamp}.log"
            log_filepath = self._log_directory / log_filename
            
            try:
                # Create rotating file handler
                self._file_handler = logging.handlers.RotatingFileHandler(
                    log_filepath,
                    maxBytes=MAX_LOG_FILE_SIZE,
                    backupCount=LOG_BACKUP_COUNT,
                    encoding='utf-8'
                )
                self._file_handler.setLevel(logging.DEBUG)
                
                file_formatter = logging.Formatter(
                    LOG_FORMAT,
                    datefmt=LOG_DATE_FORMAT
                )
                self._file_handler.setFormatter(file_formatter)
                
                # Log the initial message
                self._file_handler.emit(logging.LogRecord(
                    name=f"{APP_NAME}.system",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=f"Logging started - {APP_NAME} v{APP_VERSION} - Log file: {log_filename}",
                    args=(),
                    exc_info=None
                ))
                
            except Exception as e:
                print(f"Warning: Could not create file handler: {e}")
                self._file_handler = None
                return
        
        if self._file_handler:
            logger.addHandler(self._file_handler)
    
    def enable_file_logging(self, log_dir: Optional[Path] = None):
        """
        Enable file logging for all loggers.
        
        Args:
            log_dir: Custom log directory (optional)
        """
        if log_dir:
            self._log_directory = log_dir
            self._setup_log_directory()
        
        self._file_logging_enabled = True
        
        # Add file handler to existing loggers
        for logger in self._loggers.values():
            if self._file_handler not in logger.handlers:
                self._add_file_handler(logger)
        
        # Reset file handler to create new one with current timestamp
        self._file_handler = None
        for logger in self._loggers.values():
            self._add_file_handler(logger)
    
    def disable_file_logging(self):
        """Disable file logging for all loggers."""
        self._file_logging_enabled = False
        
        # Remove file handler from all loggers
        for logger in self._loggers.values():
            if self._file_handler and self._file_handler in logger.handlers:
                logger.removeHandler(self._file_handler)
        
        # Close and reset file handler
        if self._file_handler:
            self._file_handler.close()
            self._file_handler = None
    
    def set_console_level(self, level: int):
        """
        Set console logging level for all loggers.
        
        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        for logger in self._loggers.values():
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.setLevel(level)
    
    def set_file_level(self, level: int):
        """
        Set file logging level.
        
        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        if self._file_handler:
            self._file_handler.setLevel(level)
    
    def get_log_directory(self) -> Path:
        """Get current log directory."""
        return self._log_directory
    
    def is_file_logging_enabled(self) -> bool:
        """Check if file logging is enabled."""
        return self._file_logging_enabled
    
    def get_current_log_file(self) -> Optional[Path]:
        """Get path to current log file."""
        if self._file_handler and hasattr(self._file_handler, 'baseFilename'):
            return Path(self._file_handler.baseFilename)
        return None


# Global logger manager instance
_logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the specified module/component.
    
    Args:
        name: Logger name (typically __name__ for module loggers)
        
    Returns:
        Configured logger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("Application started")
    """
    # Extract just the module name from full path
    if '.' in name:
        name = name.split('.')[-1]
    
    return _logger_manager.get_logger(name)


def enable_file_logging(log_dir: Optional[Path] = None):
    """
    Enable file logging globally.
    
    Args:
        log_dir: Custom log directory (optional)
    """
    _logger_manager.enable_file_logging(log_dir)


def disable_file_logging():
    """Disable file logging globally."""
    _logger_manager.disable_file_logging()


def set_console_level(level: int):
    """
    Set console logging level globally.
    
    Args:
        level: Logging level (logging.DEBUG, logging.INFO, etc.)
    """
    _logger_manager.set_console_level(level)


def set_file_level(level: int):
    """
    Set file logging level globally.
    
    Args:
        level: Logging level (logging.DEBUG, logging.INFO, etc.)
    """
    _logger_manager.set_file_level(level)


def get_log_info() -> Dict[str, Any]:
    """
    Get current logging configuration information.
    
    Returns:
        Dictionary with logging configuration details
    """
    return {
        'file_logging_enabled': _logger_manager.is_file_logging_enabled(),
        'log_directory': str(_logger_manager.get_log_directory()),
        'current_log_file': str(_logger_manager.get_current_log_file()) if _logger_manager.get_current_log_file() else None,
        'active_loggers': list(_logger_manager._loggers.keys())
    }


# Convenience functions for quick logging
def log_startup():
    """Log application startup."""
    logger = get_logger('startup')
    logger.info(f"{APP_NAME} application starting...")


def log_shutdown():
    """Log application shutdown."""
    logger = get_logger('shutdown')
    logger.info(f"{APP_NAME} application shutting down...")


def log_error(message: str, exc_info: bool = True, logger_name: str = 'error'):
    """
    Log an error message with optional exception info.
    
    Args:
        message: Error message
        exc_info: Include exception traceback
        logger_name: Logger name to use
    """
    logger = get_logger(logger_name)
    logger.error(message, exc_info=exc_info)


def log_device_operation(device_id: str, operation: str, details: str = ""):
    """
    Log device-related operations.
    
    Args:
        device_id: Device identifier
        operation: Operation type
        details: Additional details
    """
    logger = get_logger('device')
    message = f"Device {device_id}: {operation}"
    if details:
        message += f" - {details}"
    logger.info(message)


def log_file_operation(operation: str, source: str, destination: str = "", status: str = ""):
    """
    Log file operations.
    
    Args:
        operation: Operation type (push, pull, copy, etc.)
        source: Source path
        destination: Destination path
        status: Operation status
    """
    logger = get_logger('file_ops')
    message = f"File {operation}: {source}"
    if destination:
        message += f" -> {destination}"
    if status:
        message += f" [{status}]"
    logger.info(message)
