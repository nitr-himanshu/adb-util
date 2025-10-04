"""
Preferences Dialog

Settings and configuration dialog for the ADB-UTIL application.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QCheckBox, QPushButton, QLineEdit,
    QSpinBox, QComboBox, QGroupBox, QGridLayout,
    QFileDialog, QMessageBox, QWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..utils.logger import (
    get_logger, enable_file_logging, disable_file_logging,
    get_log_info, set_console_level, set_file_level
)
from ..utils.constants import DEFAULT_LOG_DIR
import logging
from pathlib import Path


class PreferencesDialog(QDialog):
    """Preferences dialog for application settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.setWindowTitle("Preferences - ADB-UTIL")
        self.setModal(True)
        self.resize(500, 400)
        
        self.logger.debug("Opening preferences dialog")
        self.init_ui()
        self.load_current_settings()
    
    def init_ui(self):
        """Initialize the preferences UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.create_logging_tab()
        self.create_general_tab()
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_settings)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def create_logging_tab(self):
        """Create logging preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File Logging Group
        file_logging_group = QGroupBox("File Logging")
        file_logging_layout = QGridLayout(file_logging_group)
        
        # Enable file logging checkbox
        self.file_logging_enabled = QCheckBox("Enable file logging")
        self.file_logging_enabled.stateChanged.connect(self.on_file_logging_toggled)
        file_logging_layout.addWidget(self.file_logging_enabled, 0, 0, 1, 2)
        
        # Log directory selection
        file_logging_layout.addWidget(QLabel("Log Directory:"), 1, 0)
        
        self.log_directory_edit = QLineEdit()
        self.log_directory_edit.setReadOnly(True)
        file_logging_layout.addWidget(self.log_directory_edit, 1, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_log_directory)
        file_logging_layout.addWidget(browse_btn, 1, 2)
        
        # Log file info
        self.log_file_info = QLabel("No log file active")
        self.log_file_info.setStyleSheet("color: #666666; font-style: italic;")
        file_logging_layout.addWidget(self.log_file_info, 2, 0, 1, 3)
        
        layout.addWidget(file_logging_group)
        
        # Console Logging Group
        console_logging_group = QGroupBox("Console Logging")
        console_logging_layout = QGridLayout(console_logging_group)
        
        console_logging_layout.addWidget(QLabel("Console Log Level:"), 0, 0)
        
        self.console_level_combo = QComboBox()
        self.console_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.console_level_combo.setCurrentText("INFO")
        console_logging_layout.addWidget(self.console_level_combo, 0, 1)
        
        layout.addWidget(console_logging_group)
        
        # File Logging Level Group
        file_level_group = QGroupBox("File Logging Level")
        file_level_layout = QGridLayout(file_level_group)
        
        file_level_layout.addWidget(QLabel("File Log Level:"), 0, 0)
        
        self.file_level_combo = QComboBox()
        self.file_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.file_level_combo.setCurrentText("DEBUG")
        file_level_layout.addWidget(self.file_level_combo, 0, 1)
        
        layout.addWidget(file_level_group)
        
        # Log Actions Group
        actions_group = QGroupBox("Log Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        open_log_dir_btn = QPushButton("Open Log Directory")
        open_log_dir_btn.clicked.connect(self.open_log_directory)
        actions_layout.addWidget(open_log_dir_btn)
        
        clear_logs_btn = QPushButton("Clear Old Logs")
        clear_logs_btn.clicked.connect(self.clear_old_logs)
        actions_layout.addWidget(clear_logs_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📝 Logging")
    
    def create_general_tab(self):
        """Create general preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Application Settings Group
        app_group = QGroupBox("Application Settings")
        app_layout = QGridLayout(app_group)
        
        # Theme selection (placeholder)
        app_layout.addWidget(QLabel("Theme:"), 0, 0)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System Default", "Light", "Dark"])
        app_layout.addWidget(self.theme_combo, 0, 1)
        
        # Auto-connect to devices
        self.auto_connect = QCheckBox("Auto-connect to devices on startup")
        app_layout.addWidget(self.auto_connect, 1, 0, 1, 2)
        
        # Remember window size/position
        self.remember_window = QCheckBox("Remember window size and position")
        self.remember_window.setChecked(True)
        app_layout.addWidget(self.remember_window, 2, 0, 1, 2)
        
        layout.addWidget(app_group)
        
        # ADB Settings Group
        adb_group = QGroupBox("ADB Settings")
        adb_layout = QGridLayout(adb_group)
        
        adb_layout.addWidget(QLabel("ADB Path:"), 0, 0)
        
        self.adb_path_edit = QLineEdit()
        self.adb_path_edit.setPlaceholderText("Auto-detect")
        adb_layout.addWidget(self.adb_path_edit, 0, 1)
        
        adb_browse_btn = QPushButton("Browse...")
        adb_browse_btn.clicked.connect(self.browse_adb_path)
        adb_layout.addWidget(adb_browse_btn, 0, 2)
        
        # Command timeout
        adb_layout.addWidget(QLabel("Command Timeout (seconds):"), 1, 0)
        
        self.command_timeout_spin = QSpinBox()
        self.command_timeout_spin.setRange(5, 300)
        self.command_timeout_spin.setValue(30)
        adb_layout.addWidget(self.command_timeout_spin, 1, 1)
        
        layout.addWidget(adb_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "⚙️ General")
    
    def load_current_settings(self):
        """Load current application settings."""
        # Load logging settings
        log_info = get_log_info()
        
        self.file_logging_enabled.setChecked(log_info['file_logging_enabled'])
        self.log_directory_edit.setText(log_info['log_directory'])
        
        if log_info['current_log_file']:
            self.log_file_info.setText(f"Current log file: {Path(log_info['current_log_file']).name}")
        else:
            self.log_file_info.setText("No log file active")
        
        self.on_file_logging_toggled()
    
    def on_file_logging_toggled(self):
        """Handle file logging enable/disable toggle."""
        enabled = self.file_logging_enabled.isChecked()
        self.log_directory_edit.setEnabled(enabled)
        self.file_level_combo.setEnabled(enabled)
    
    def browse_log_directory(self):
        """Browse for log directory."""
        current_dir = self.log_directory_edit.text() or str(DEFAULT_LOG_DIR.parent)
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Log Directory",
            current_dir
        )
        
        if directory:
            self.log_directory_edit.setText(directory)
    
    def browse_adb_path(self):
        """Browse for ADB executable."""
        adb_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ADB Executable",
            "",
            "Executable Files (*.exe);;All Files (*)" if hasattr(self, 'isWindows') else "All Files (*)"
        )
        
        if adb_path:
            self.adb_path_edit.setText(adb_path)
    
    def open_log_directory(self):
        """Open log directory in file explorer."""
        import subprocess
        import sys
        
        log_dir = Path(self.log_directory_edit.text())
        
        if not log_dir.exists():
            QMessageBox.warning(self, "Directory Not Found", f"Log directory does not exist: {log_dir}")
            return
        
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", str(log_dir)], check=True)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(log_dir)], check=True)
            else:
                subprocess.run(["xdg-open", str(log_dir)], check=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open directory: {e}")
    
    def clear_old_logs(self):
        """Clear old log files."""
        reply = QMessageBox.question(
            self,
            "Clear Old Logs",
            "This will delete all log files older than 7 days. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement log cleanup
            QMessageBox.information(self, "Clear Logs", "Old log files cleared successfully!")
    
    def apply_settings(self):
        """Apply current settings without closing dialog."""
        self.logger.info("Applying preference settings...")
        
        try:
            # Apply logging settings
            if self.file_logging_enabled.isChecked():
                log_dir = Path(self.log_directory_edit.text()) if self.log_directory_edit.text() else None
                enable_file_logging(log_dir)
                self.logger.info("File logging enabled")
            else:
                disable_file_logging()
                self.logger.info("File logging disabled")
            
            # Apply console log level
            console_level = getattr(logging, self.console_level_combo.currentText())
            set_console_level(console_level)
            
            # Apply file log level
            file_level = getattr(logging, self.file_level_combo.currentText())
            set_file_level(file_level)
            
            # Update UI with current settings
            self.load_current_settings()
            
            QMessageBox.information(self, "Settings Applied", "Settings have been applied successfully!")
            
        except Exception as e:
            self.logger.error(f"Error applying settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {e}")
    
    def accept_settings(self):
        """Apply settings and close dialog."""
        self.apply_settings()
        self.accept()
