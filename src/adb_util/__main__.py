"""
ADB-UTIL - Main Application Entry Point

A comprehensive Python-based desktop application for Android Debug Bridge (ADB) operations.
This module serves as the entry point when running the package with python -m adb_util.
"""

import sys
import signal
import os
from pathlib import Path

def setup_path():
    """Setup module path for both development and PyInstaller environments."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        application_path = Path(sys.executable).parent
        src_path = application_path / "src"
        if src_path.exists():
            sys.path.insert(0, str(src_path))
        # Also add the bundle's internal src path
        bundle_src = Path(sys._MEIPASS) / "src" if hasattr(sys, '_MEIPASS') else None
        if bundle_src and bundle_src.exists():
            sys.path.insert(0, str(bundle_src))
    else:
        # Running in development - src path is already set up by package structure
        pass

setup_path()

# Global reference to main window for signal handler
_main_window = None

def signal_handler(signum, frame):
    """Handle keyboard interrupt (Ctrl+C) gracefully."""
    signal_names = {
        signal.SIGINT: "SIGINT (Ctrl+C)",
        signal.SIGTERM: "SIGTERM (Termination)"
    }
    
    try:
        from .utils.logger import get_logger, log_shutdown
        logger = get_logger(__name__)
        
        # Log the interrupt with detailed information
        signal_name = signal_names.get(signum, f"Signal {signum}")
        logger.warning(f"=== INTERRUPT RECEIVED ===")
        logger.warning(f"Signal: {signal_name}")
        logger.warning(f"Process ID: {os.getpid()}")
        logger.warning(f"Initiating graceful shutdown...")
        
        # Try to close the main window gracefully
        global _main_window
        if _main_window and hasattr(_main_window, 'close'):
            logger.info("Closing main window...")
            _main_window.close()
        
        log_shutdown("Application terminated by user interrupt")
        
    except Exception as e:
        print(f"Error during shutdown: {e}")
    
    finally:
        # Force exit
        sys.exit(0)

def main():
    """Main application entry point."""
    try:
        from .utils.logger import get_logger, log_startup, log_shutdown
        from .ui.main_window import MainWindow
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger = get_logger(__name__)
        log_startup()
        
        logger.info("Initializing ADB-UTIL application...")
        logger.info("Signal handlers registered for graceful shutdown")
        
        # Initialize Qt Application
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        import qasync
        
        app = QApplication(sys.argv)
        app.setApplicationName("ADB-UTIL")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("ADB-UTIL")
        
        # Set application attributes for better appearance
        # Note: High DPI scaling is handled automatically in PyQt6
        
        logger.info("Qt Application initialized")
        
        # Create main window
        global _main_window
        _main_window = MainWindow()
        logger.info("Main window created and displayed")
        
        logger.info("Starting Qt event loop...")
        
        # Show main window and start event loop
        _main_window.show()
        result = app.exec()
        
        log_shutdown()
        sys.exit(result)
            
    except ImportError as e:
        try:
            from .utils.logger import log_error
            log_error(f"Import error: {e}", exc_info=True, logger_name='startup')
        except:
            pass
        print(f"Error importing required modules: {e}")
        print("Please install required dependencies: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        try:
            from .utils.logger import log_error
            log_error(f"Unexpected error: {e}", exc_info=True, logger_name='startup')
        except:
            pass
        print(f"Unexpected error: {e}")
        sys.exit(1)
    
    finally:
        try:
            from .utils.logger import log_shutdown
            log_shutdown("ADB-UTIL application shutting down...")
        except:
            pass

if __name__ == "__main__":
    import asyncio
    main()
