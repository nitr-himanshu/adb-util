"""
ADB-UTIL - Main Application Entry Point

A comprehensive Python-based desktop application for Android Debug Bridge (ADB) operations.
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
        # Running in development
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))

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
        from utils.logger import get_logger, log_shutdown
        logger = get_logger(__name__)
        
        # Log the interrupt with detailed information
        signal_name = signal_names.get(signum, f"Signal {signum}")
        logger.warning(f"=== INTERRUPT RECEIVED ===")
        logger.warning(f"Signal: {signal_name}")
        logger.warning(f"Process ID: {os.getpid()}")
        logger.warning(f"Initiating graceful shutdown...")
        
        # Try to cleanup main window if it exists
        global _main_window
        if _main_window:
            try:
                logger.info("Closing main window...")
                _main_window.close()
            except Exception as e:
                logger.error(f"Error closing main window: {e}")
        
        # Try to get the QApplication instance and quit properly
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                logger.info("Closing Qt application...")
                app.quit()
        except Exception as e:
            logger.error(f"Error closing Qt application: {e}")
        
        logger.info("Shutdown sequence completed")
        log_shutdown()
        
    except Exception as e:
        print(f"\n=== INTERRUPT RECEIVED ===")
        print(f"Signal: {signal_names.get(signum, f'Signal {signum}')}")
        print(f"Error during shutdown: {e}")
        print("Shutting down gracefully...")
    
    # Exit cleanly
    sys.exit(0)

def main():
    """Main application entry point."""
    try:
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Initialize logging first
        from utils.logger import get_logger, log_startup, log_shutdown, log_error
        logger = get_logger(__name__)
        
        log_startup()
        logger.info("Initializing ADB-UTIL application...")
        logger.info("Signal handlers registered for graceful shutdown")
        
        from PyQt6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName("ADB-UTIL")
        app.setApplicationVersion("1.0.0")
        
        logger.info("Qt Application initialized")
        
        # Create and show main window
        global _main_window
        _main_window = MainWindow()
        _main_window.show()
        
        logger.info("Main window created and displayed")
        
        # Start event loop
        logger.info("Starting Qt event loop...")
        result = app.exec()
        
        log_shutdown()
        sys.exit(result)
        
    except ImportError as e:
        try:
            from utils.logger import log_error
            log_error(f"Import error: {e}", exc_info=True, logger_name='startup')
        except:
            pass
        print(f"Error importing required modules: {e}")
        print("Please install required dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        try:
            from utils.logger import log_error
            log_error(f"Application startup error: {e}", exc_info=True, logger_name='startup')
        except:
            pass
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
