"""
Theme Manager

Handles application themes including dark mode and light mode.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from typing import Dict, Any
import json
import os


class ThemeManager(QObject):
    """Manages application themes and styling."""
    
    theme_changed = pyqtSignal(str)  # Emits theme name when changed
    
    def __init__(self):
        super().__init__()
        self.current_theme = "light"
        self.themes = {
            "light": self._get_light_theme(),
            "dark": self._get_dark_theme()
        }
        
    def _get_light_theme(self) -> Dict[str, Any]:
        """Get light theme stylesheet and properties."""
        return {
            "name": "Light",
            "stylesheet": """
                QMainWindow {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                
                QMenuBar {
                    background-color: #e0e0e0;
                    color: #000000;
                    border-bottom: 1px solid #c0c0c0;
                    padding: 4px;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                
                QMenuBar::item:selected {
                    background-color: #d0d0d0;
                }
                
                QMenu {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    padding: 4px;
                }
                
                QMenu::item {
                    padding: 6px 20px;
                    border-radius: 4px;
                }
                
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                
                QTabWidget::pane {
                    border: 1px solid #c0c0c0;
                    background-color: #ffffff;
                }
                
                QTabBar::tab {
                    background-color: #e0e0e0;
                    color: #000000;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    border-bottom: 2px solid #007acc;
                }
                
                QPushButton {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: normal;
                }
                
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border-color: #a0a0a0;
                }
                
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
                
                QListWidget {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                }
                
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #e0e0e0;
                }
                
                QListWidget::item:selected {
                    background-color: #007acc;
                    color: #ffffff;
                }
                
                QTreeView {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    alternate-background-color: #f8f9fa;
                    selection-background-color: #007acc;
                    selection-color: #ffffff;
                }
                
                QTreeView::item {
                    padding: 4px;
                    border-bottom: 1px solid #e0e0e0;
                }
                
                QTreeView::item:selected {
                    background-color: #007acc;
                    color: #ffffff;
                }
                
                QTreeView::item:hover {
                    background-color: #f0f0f0;
                }
                
                QTreeView::branch {
                    background-color: #ffffff;
                }
                
                QTreeView::branch:has-children:!has-siblings:closed,
                QTreeView::branch:closed:has-children:has-siblings {
                    border-image: none;
                    image: none;
                }
                
                QTreeView::branch:open:has-children:!has-siblings,
                QTreeView::branch:open:has-children:has-siblings {
                    border-image: none;
                    image: none;
                }
                
                QHeaderView::section {
                    background-color: #f0f0f0;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 6px;
                    font-weight: bold;
                }
                
                QHeaderView::section:hover {
                    background-color: #e0e0e0;
                }
                
                QTextEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    selection-background-color: #007acc;
                    selection-color: #ffffff;
                }
                
                QTextEdit:focus {
                    border-color: #007acc;
                }
                
                QLineEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 6px;
                    border-radius: 4px;
                }
                
                QComboBox {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 6px;
                    border-radius: 4px;
                }
                
                QStatusBar {
                    background-color: #e0e0e0;
                    color: #000000;
                    border-top: 1px solid #c0c0c0;
                }
                
                QFrame {
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                }
                
                QCheckBox {
                    color: #000000;
                }
                
                QLabel {
                    color: #000000;
                }
                
                /* Home page specific styling */
                QLabel#subtitle_label {
                    color: #666666;
                }
                
                QLabel#instructions_label {
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                }
                
                /* Popup and dialog styling */
                QToolTip {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c0c0c0;
                    padding: 4px;
                    border-radius: 4px;
                }
                
                QMessageBox {
                    background-color: #ffffff;
                    color: #000000;
                }
                
                QMessageBox QLabel {
                    color: #000000;
                }
                
                QMessageBox QPushButton {
                    min-width: 60px;
                    padding: 6px 12px;
                }
                
                QDialog {
                    background-color: #ffffff;
                    color: #000000;
                }
                
                QProgressBar {
                    background-color: #f0f0f0;
                    border: 1px solid #c0c0c0;
                    border-radius: 4px;
                    text-align: center;
                    color: #000000;
                }
                
                QProgressBar::chunk {
                    background-color: #007acc;
                    border-radius: 2px;
                }
                
                QSplitter::handle {
                    background-color: #c0c0c0;
                }
                
                QSplitter::handle:horizontal {
                    width: 3px;
                }
                
                QSplitter::handle:vertical {
                    height: 3px;
                }
                
                /* Tab widget specific improvements */
                QTabWidget::tab-bar {
                    alignment: left;
                }
                
                QTabBar::tab:!selected {
                    background-color: #e0e0e0;
                    color: #666666;
                }
                
                QTabBar::tab:!selected:hover {
                    background-color: #d0d0d0;
                    color: #000000;
                }
                
                /* Better scrollbar styling */
                QScrollBar:horizontal {
                    background-color: #f0f0f0;
                    height: 12px;
                    border-radius: 6px;
                }
                
                QScrollBar::handle:horizontal {
                    background-color: #c0c0c0;
                    border-radius: 6px;
                    min-width: 20px;
                }
                
                QScrollBar::handle:horizontal:hover {
                    background-color: #a0a0a0;
                }
                
                QScrollBar::add-line, QScrollBar::sub-line {
                    background: none;
                    border: none;
                }
                
                QScrollBar::add-page, QScrollBar::sub-page {
                    background: none;
                }
            """,
            "colors": {
                "primary": "#007acc",
                "secondary": "#6c757d",
                "success": "#28a745",
                "warning": "#ffc107",
                "danger": "#dc3545",
                "background": "#f0f0f0",
                "surface": "#ffffff",
                "text": "#000000"
            }
        }
    
    def _get_dark_theme(self) -> Dict[str, Any]:
        """Get dark theme stylesheet and properties."""
        return {
            "name": "Dark",
            "stylesheet": """
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                
                QMenuBar {
                    background-color: #363636;
                    color: #ffffff;
                    border-bottom: 1px solid #555555;
                    padding: 4px;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                
                QMenuBar::item:selected {
                    background-color: #484848;
                }
                
                QMenu {
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 4px;
                }
                
                QMenu::item {
                    padding: 6px 20px;
                    border-radius: 4px;
                }
                
                QMenu::item:selected {
                    background-color: #484848;
                }
                
                QTabWidget::pane {
                    border: 1px solid #555555;
                    background-color: #2b2b2b;
                }
                
                QTabBar::tab {
                    background-color: #363636;
                    color: #ffffff;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                
                QTabBar::tab:selected {
                    background-color: #2b2b2b;
                    border-bottom: 2px solid #007acc;
                }
                
                QPushButton {
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: normal;
                }
                
                QPushButton:hover {
                    background-color: #484848;
                    border-color: #777777;
                }
                
                QPushButton:pressed {
                    background-color: #555555;
                }
                
                QListWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                }
                
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #404040;
                }
                
                QListWidget::item:selected {
                    background-color: #007acc;
                    color: #ffffff;
                }
                
                QTreeView {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    alternate-background-color: #363636;
                    selection-background-color: #007acc;
                    selection-color: #ffffff;
                }
                
                QTreeView::item {
                    padding: 4px;
                    border-bottom: 1px solid #404040;
                }
                
                QTreeView::item:selected {
                    background-color: #007acc;
                    color: #ffffff;
                }
                
                QTreeView::item:hover {
                    background-color: #484848;
                }
                
                QTreeView::branch {
                    background-color: #2b2b2b;
                }
                
                QTreeView::branch:has-children:!has-siblings:closed,
                QTreeView::branch:closed:has-children:has-siblings {
                    border-image: none;
                    image: none;
                }
                
                QTreeView::branch:open:has-children:!has-siblings,
                QTreeView::branch:open:has-children:has-siblings {
                    border-image: none;
                    image: none;
                }
                
                QHeaderView::section {
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px;
                    font-weight: bold;
                }
                
                QHeaderView::section:hover {
                    background-color: #484848;
                }
                
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    selection-background-color: #007acc;
                    selection-color: #ffffff;
                }
                
                QTextEdit:focus {
                    border-color: #007acc;
                }
                
                QLineEdit {
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px;
                    border-radius: 4px;
                }
                
                QLineEdit:focus {
                    border-color: #007acc;
                }
                
                QComboBox {
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px;
                    border-radius: 4px;
                }
                
                QComboBox::drop-down {
                    border: none;
                    background-color: #484848;
                    border-radius: 2px;
                }
                
                QComboBox::down-arrow {
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 4px solid #ffffff;
                }
                
                QComboBox QAbstractItemView {
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                }
                
                QStatusBar {
                    background-color: #363636;
                    color: #ffffff;
                    border-top: 1px solid #555555;
                }
                
                QFrame {
                    border: 1px solid #555555;
                    border-radius: 4px;
                }
                
                QCheckBox {
                    color: #ffffff;
                }
                
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    background-color: #363636;
                    border: 1px solid #555555;
                    border-radius: 2px;
                }
                
                QCheckBox::indicator:checked {
                    background-color: #007acc;
                    border-color: #007acc;
                }
                
                QLabel {
                    color: #ffffff;
                }
                
                QSpinBox {
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 4px;
                    border-radius: 4px;
                }
                
                QGroupBox {
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    margin: 8px 0px;
                    padding-top: 16px;
                }
                
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 8px;
                    padding: 0px 8px;
                    background-color: #2b2b2b;
                }
                
                QScrollBar:vertical {
                    background-color: #363636;
                    width: 12px;
                    border-radius: 6px;
                }
                
                QScrollBar::handle:vertical {
                    background-color: #555555;
                    border-radius: 6px;
                    min-height: 20px;
                }
                
                QScrollBar::handle:vertical:hover {
                    background-color: #777777;
                }
                
                /* Home page specific styling */
                QLabel#subtitle_label {
                    color: #bbbbbb;
                }
                
                QLabel#instructions_label {
                    background-color: #363636;
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #555555;
                }
                
                /* Popup and dialog styling */
                QToolTip {
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 4px;
                    border-radius: 4px;
                }
                
                QMessageBox {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                
                QMessageBox QLabel {
                    color: #ffffff;
                }
                
                QMessageBox QPushButton {
                    min-width: 60px;
                    padding: 6px 12px;
                    background-color: #363636;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                
                QMessageBox QPushButton:hover {
                    background-color: #484848;
                }
                
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                
                QProgressBar {
                    background-color: #363636;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    text-align: center;
                    color: #ffffff;
                }
                
                QProgressBar::chunk {
                    background-color: #007acc;
                    border-radius: 2px;
                }
                
                QSplitter::handle {
                    background-color: #555555;
                }
                
                QSplitter::handle:horizontal {
                    width: 3px;
                }
                
                QSplitter::handle:vertical {
                    height: 3px;
                }
                
                /* Tab widget specific improvements */
                QTabWidget::tab-bar {
                    alignment: left;
                }
                
                QTabBar::tab:!selected {
                    background-color: #363636;
                    color: #bbbbbb;
                }
                
                QTabBar::tab:!selected:hover {
                    background-color: #484848;
                    color: #ffffff;
                }
                
                /* Better scrollbar styling */
                QScrollBar:horizontal {
                    background-color: #363636;
                    height: 12px;
                    border-radius: 6px;
                }
                
                QScrollBar::handle:horizontal {
                    background-color: #555555;
                    border-radius: 6px;
                    min-width: 20px;
                }
                
                QScrollBar::handle:horizontal:hover {
                    background-color: #777777;
                }
                
                QScrollBar::add-line, QScrollBar::sub-line {
                    background: none;
                    border: none;
                }
                
                QScrollBar::add-page, QScrollBar::sub-page {
                    background: none;
                }
            """,
            "colors": {
                "primary": "#007acc",
                "secondary": "#6c757d",
                "success": "#28a745",
                "warning": "#ffc107",
                "danger": "#dc3545",
                "background": "#2b2b2b",
                "surface": "#363636",
                "text": "#ffffff"
            }
        }
    
    def set_theme(self, theme_name: str):
        """Set the current theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self._apply_theme()
            self.theme_changed.emit(theme_name)
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.set_theme(new_theme)
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self.current_theme
    
    def get_theme_colors(self, theme_name: str = None) -> Dict[str, str]:
        """Get color palette for the specified theme."""
        theme_name = theme_name or self.current_theme
        return self.themes.get(theme_name, {}).get("colors", {})
    
    def _apply_theme(self):
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if app:
            theme_data = self.themes[self.current_theme]
            app.setStyleSheet(theme_data["stylesheet"])
    
    def save_theme_preference(self, config_file: str = None):
        """Save theme preference to config file."""
        if not config_file:
            config_file = os.path.expanduser("~/.adb-util-config.json")
        
        try:
            config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            
            config['theme'] = self.current_theme
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save theme preference: {e}")
    
    def load_theme_preference(self, config_file: str = None):
        """Load theme preference from config file."""
        if not config_file:
            config_file = os.path.expanduser("~/.adb-util-config.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    theme = config.get('theme', 'light')
                    self.set_theme(theme)
        except Exception as e:
            print(f"Failed to load theme preference: {e}")
            self.set_theme('light')  # Default to light theme


# Global theme manager instance
theme_manager = ThemeManager()
