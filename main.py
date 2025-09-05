"""
ADB-UTIL - Main Application Entry Point

A comprehensive Python-based desktop application for Android Debug Bridge (ADB) operations.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

"""
ADB-UTIL - Main Application Entry Point

A comprehensive Python-based desktop application for Android Debug Bridge (ADB) operations.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main application entry point."""
    try:
        # Initialize logging first
        from utils.logger import get_logger, log_startup, log_shutdown, log_error
        logger = get_logger(__name__)
        
        log_startup()
        logger.info("Initializing ADB-UTIL application...")
        
        from PyQt6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName("ADB-UTIL")
        app.setApplicationVersion("1.0.0")
        
        logger.info("Qt Application initialized")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
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
