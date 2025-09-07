#!/usr/bin/env python3
"""
Simple verification test for theme application.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from gui.logging import Logging
from utils.theme_manager import ThemeManager


def test_theme_application():
    """Test basic theme application without GUI."""
    app = QApplication([])
    
    # Create theme manager
    theme_manager = ThemeManager()
    
    # Test dark theme
    theme_manager.set_theme("dark")
    
    # Create logging widget
    logging_widget = Logging("test_device")
    
    # Apply theme
    try:
        logging_widget.refresh_theme()
        print("✓ Dark theme refresh successful")
    except Exception as e:
        print(f"✗ Dark theme refresh failed: {e}")
        return False
    
    # Test light theme
    theme_manager.set_theme("light")
    
    try:
        logging_widget.refresh_theme()
        print("✓ Light theme refresh successful")
    except Exception as e:
        print(f"✗ Light theme refresh failed: {e}")
        return False
    
    # Check that log_display has styling
    if hasattr(logging_widget, 'log_display') and logging_widget.log_display:
        style_sheet = logging_widget.log_display.styleSheet()
        if "background-color:" in style_sheet and "color:" in style_sheet:
            print("✓ Log display has theme styling")
        else:
            print("✗ Log display missing theme styling")
            return False
    
    # Cleanup
    logging_widget.cleanup()
    print("✓ All tests passed - comprehensive theme application working")
    return True


if __name__ == "__main__":
    success = test_theme_application()
    sys.exit(0 if success else 1)
