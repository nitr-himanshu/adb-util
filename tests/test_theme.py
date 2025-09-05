#!/usr/bin/env python3
"""
Quick test to verify dark mode text visibility.
"""
import sys
import os
from PyQt6.QtWidgets import QApplication

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.theme_manager import ThemeManager

def test_themes():
    """Test that themes contain the correct home page styling."""
    app = QApplication([])
    theme_manager = ThemeManager()
    
    # Test light theme
    light_theme = theme_manager._get_light_theme()
    print("Light theme stylesheet includes:")
    if "QLabel#subtitle_label" in light_theme['stylesheet']:
        print("✓ Subtitle label styling")
    else:
        print("✗ Missing subtitle label styling")
        
    if "QLabel#instructions_label" in light_theme['stylesheet']:
        print("✓ Instructions label styling")
    else:
        print("✗ Missing instructions label styling")
    
    # Test dark theme
    dark_theme = theme_manager._get_dark_theme()
    print("\nDark theme stylesheet includes:")
    if "QLabel#subtitle_label" in dark_theme['stylesheet']:
        print("✓ Subtitle label styling")
    else:
        print("✗ Missing subtitle label styling")
        
    if "QLabel#instructions_label" in dark_theme['stylesheet']:
        print("✓ Instructions label styling")
    else:
        print("✗ Missing instructions label styling")
    
    # Check dark mode subtitle color
    if "color: #bbbbbb;" in dark_theme['stylesheet']:
        print("✓ Dark mode uses light gray text for subtitle")
    else:
        print("✗ Dark mode subtitle color not found")

if __name__ == "__main__":
    test_themes()
