#!/usr/bin/env python3
"""
Unit test for enhanced logging dark mode functionality.
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from gui.logging import Logging
from utils.theme_manager import ThemeManager


@pytest.fixture
def app():
    """Create QApplication for testing."""
    if not QApplication.instance():
        return QApplication([])
    return QApplication.instance()


@pytest.fixture
def theme_manager():
    """Create a fresh theme manager for each test."""
    return ThemeManager()


def test_logging_widget_theme_initialization(app):
    """Test that logging widget initializes with proper theme support."""
    # Create logging widget
    logging_widget = Logging("test_device")
    
    # Verify required attributes exist
    assert hasattr(logging_widget, 'refresh_theme')
    assert hasattr(logging_widget, 'log_display')
    assert hasattr(logging_widget, 'search_input')
    assert hasattr(logging_widget, 'level_checkboxes')
    
    # Test refresh_theme method doesn't crash
    try:
        logging_widget.refresh_theme()
        theme_refresh_success = True
    except Exception as e:
        theme_refresh_success = False
        print(f"Theme refresh failed: {e}")
    
    assert theme_refresh_success, "refresh_theme method should not crash"
    
    # Cleanup
    logging_widget.cleanup()


def test_dark_theme_application(app, theme_manager):
    """Test that dark theme is properly applied to logging components."""
    # Set dark theme
    theme_manager.set_theme("dark")
    
    # Create logging widget
    logging_widget = Logging("test_device")
    
    # Force theme refresh
    logging_widget.refresh_theme()
    
    # Check that log_display has dark background styling
    if hasattr(logging_widget, 'log_display') and logging_widget.log_display:
        style_sheet = logging_widget.log_display.styleSheet()
        
        # Should contain dark background color
        assert "#1e1e1e" in style_sheet or "#2b2b2b" in style_sheet, \
            "Dark theme should apply dark background to log display"
        
        # Should contain white text color  
        assert "#ffffff" in style_sheet, \
            "Dark theme should apply white text color"
        
        # Should have !important flags for critical properties
        assert "!important" in style_sheet, \
            "Critical theme properties should use !important"
    
    # Test light theme switch
    theme_manager.set_theme("light")
    logging_widget.refresh_theme()
    
    if hasattr(logging_widget, 'log_display') and logging_widget.log_display:
        style_sheet = logging_widget.log_display.styleSheet()
        
        # Should contain light background
        assert "#ffffff" in style_sheet, \
            "Light theme should apply white background"
    
    # Cleanup
    logging_widget.cleanup()


def test_comprehensive_component_styling(app, theme_manager):
    """Test that all components get proper dark mode styling."""
    # Set dark theme
    theme_manager.set_theme("dark")
    
    # Create logging widget
    logging_widget = Logging("test_device")
    
    # Force theme refresh
    logging_widget.refresh_theme()
    
    # Check various components have styling applied
    components_to_check = [
        'search_input',
        'format_combo', 
        'buffer_combo',
        'buffer_size_spin'
    ]
    
    for component_name in components_to_check:
        if hasattr(logging_widget, component_name):
            component = getattr(logging_widget, component_name)
            if component:
                style_sheet = component.styleSheet()
                # Component should have some dark theme styling
                has_dark_styling = (
                    "#363636" in style_sheet or  # input background
                    "#555555" in style_sheet or  # border color
                    "#ffffff" in style_sheet or  # text color
                    "!important" in style_sheet
                )
                assert has_dark_styling, \
                    f"Component {component_name} should have dark theme styling"
    
    # Check level checkboxes
    if hasattr(logging_widget, 'level_checkboxes'):
        for checkbox in logging_widget.level_checkboxes.values():
            style_sheet = checkbox.styleSheet()
            # Should have checkbox-specific dark styling
            has_checkbox_styling = (
                "QCheckBox" in style_sheet and
                ("color:" in style_sheet or "background-color:" in style_sheet)
            )
            assert has_checkbox_styling, \
                "Level checkboxes should have dark theme styling"
    
    # Cleanup
    logging_widget.cleanup()


def test_theme_switching_stability(app, theme_manager):
    """Test that theme switching doesn't cause errors."""
    logging_widget = Logging("test_device")
    
    # Switch themes multiple times
    themes = ["light", "dark", "light", "dark"]
    
    for theme in themes:
        try:
            theme_manager.set_theme(theme)
            # Process events to ensure theme is applied
            app.processEvents()
            logging_widget.refresh_theme()
            app.processEvents()
            theme_switch_success = True
        except Exception as e:
            theme_switch_success = False
            print(f"Theme switch to {theme} failed: {e}")
            break
    
    assert theme_switch_success, "Theme switching should be stable"
    
    # Cleanup
    logging_widget.cleanup()


def test_refresh_theme_methods(app):
    """Test that the enhanced refresh_theme method works correctly."""
    logging_widget = Logging("test_device")
    
    # Test that refresh_theme can be called multiple times without error
    for i in range(3):
        try:
            logging_widget.refresh_theme()
            success = True
        except Exception as e:
            success = False
            print(f"refresh_theme call {i+1} failed: {e}")
            break
    
    assert success, "refresh_theme should be callable multiple times"
    
    # Cleanup
    logging_widget.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
