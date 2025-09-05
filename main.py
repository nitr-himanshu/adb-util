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
        from PyQt6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        # Create QApplication instance
        app = QApplication(sys.argv)
        app.setApplicationName("ADB-UTIL")
        app.setApplicationVersion("1.0.0")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Please install required dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
