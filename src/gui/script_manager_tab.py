"""
Script Manager Tab

GUI component for managing and executing scripts (host and device).
Supports Windows .bat files and Linux .sh files with async output capture.
"""

import os
from pathlib import Path
from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QComboBox, QLineEdit, QTextEdit, QFileDialog,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QSplitter, QTabWidget, QScrollArea, QFrame,
    QGroupBox, QCheckBox, QSpinBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMenu, QToolButton, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QAction, QPixmap

from services.script_manager import (
    get_script_manager, Script, ScriptType, ScriptExecution, ScriptStatus
)
from utils.logger import get_logger
from utils.theme_manager import theme_manager


class ScriptAddDialog(QDialog):
    """Dialog for adding new scripts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.script_manager = get_script_manager()
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Add New Script")
        self.setModal(True)
        self.resize(500, 400)
        
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Script name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter script name")
        form_layout.addRow("Name:", self.name_edit)
        
        # Script type
        self.type_combo = QComboBox()
        self.type_combo.addItem("Host Script (Windows .bat)", ScriptType.HOST_WINDOWS)
        self.type_combo.addItem("Host Script (Linux .sh)", ScriptType.HOST_LINUX)
        self.type_combo.addItem("Device Script (.sh)", ScriptType.DEVICE)
        
        # Set default based on OS
        if os.name == 'nt':
            self.type_combo.setCurrentIndex(0)  # Windows
        else:
            self.type_combo.setCurrentIndex(1)  # Linux
            
        form_layout.addRow("Type:", self.type_combo)
        
        # Script path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select script file")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_script)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        
        form_widget = QWidget()
        form_widget.setLayout(path_layout)
        form_layout.addRow("Script File:", form_widget)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Optional description")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addLayout(form_layout)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Connect type change to update file dialog
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
    
    def on_type_changed(self):
        """Handle script type change."""
        self.path_edit.clear()
    
    def browse_script(self):
        """Browse for script file."""
        script_type = self.type_combo.currentData()
        
        if script_type == ScriptType.HOST_WINDOWS:
            file_filter = "Batch Files (*.bat);;All Files (*)"
            title = "Select Windows Batch File"
        else:  # HOST_LINUX or DEVICE
            file_filter = "Shell Scripts (*.sh);;All Files (*)"
            title = "Select Shell Script"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, title, str(Path.home()), file_filter
        )
        
        if file_path:
            self.path_edit.setText(file_path)
            
            # Auto-fill name if empty
            if not self.name_edit.text():
                name = Path(file_path).stem
                self.name_edit.setText(name)
    
    def apply_theme(self):
        """Apply current theme."""
        if hasattr(theme_manager, 'apply_theme'):
            theme_manager.apply_theme(self)
    
    def get_script_data(self) -> Optional[Dict]:
        """Get script data from form."""
        name = self.name_edit.text().strip()
        script_path = self.path_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        script_type = self.type_combo.currentData()
        
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a script name.")
            return None
        
        if not script_path:
            QMessageBox.warning(self, "Error", "Please select a script file.")
            return None
        
        if not Path(script_path).exists():
            QMessageBox.warning(self, "Error", "Selected script file does not exist.")
            return None
        
        return {
            'name': name,
            'script_type': script_type,
            'script_path': script_path,
            'description': description
        }


class ScriptOutputDialog(QDialog):
    """Dialog for displaying script execution output."""
    
    def __init__(self, execution_id: str, parent=None):
        super().__init__(parent)
        self.execution_id = execution_id
        self.script_manager = get_script_manager()
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Script Output")
        self.setModal(False)
        self.resize(800, 600)
        
        self.setup_ui()
        self.apply_theme()
        self.load_execution_data()
        
        # Connect to script manager signals
        self.script_manager.output_received.connect(self.on_output_received)
        self.script_manager.error_received.connect(self.on_error_received)
        self.script_manager.execution_finished.connect(self.on_execution_finished)
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Info section
        info_layout = QFormLayout()
        
        self.script_label = QLabel()
        self.status_label = QLabel()
        self.start_time_label = QLabel()
        self.duration_label = QLabel()
        
        info_layout.addRow("Script:", self.script_label)
        info_layout.addRow("Status:", self.status_label)
        info_layout.addRow("Started:", self.start_time_label)
        info_layout.addRow("Duration:", self.duration_label)
        
        info_frame = QFrame()
        info_frame.setLayout(info_layout)
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        layout.addWidget(info_frame)
        
        # Output tabs
        self.output_tabs = QTabWidget()
        
        # Combined output tab
        self.combined_output = QTextBrowser()
        self.combined_output.setFont(QFont("Consolas", 10))
        self.output_tabs.addTab(self.combined_output, "Combined")
        
        # Stdout tab
        self.stdout_output = QTextBrowser()
        self.stdout_output.setFont(QFont("Consolas", 10))
        self.output_tabs.addTab(self.stdout_output, "Output")
        
        # Stderr tab
        self.stderr_output = QTextBrowser()
        self.stderr_output.setFont(QFont("Consolas", 10))
        self.output_tabs.addTab(self.stderr_output, "Errors")
        
        layout.addWidget(self.output_tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel Execution")
        self.cancel_button.clicked.connect(self.cancel_execution)
        
        self.save_button = QPushButton("Save Output")
        self.save_button.clicked.connect(self.save_output)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Timer for updating duration
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_duration)
        self.update_timer.start(1000)  # Update every second
    
    def load_execution_data(self):
        """Load execution data."""
        execution = self.script_manager.get_execution(self.execution_id)
        if not execution:
            return
        
        script = self.script_manager.get_script(execution.script_id)
        if script:
            self.script_label.setText(f"{script.name} ({script.script_type.value})")
        
        self.status_label.setText(execution.status.value.title())
        self.start_time_label.setText(execution.start_time)
        
        # Load existing output
        if execution.stdout:
            self.stdout_output.setText(execution.stdout)
            self.combined_output.append(execution.stdout)
        
        if execution.stderr:
            self.stderr_output.setText(execution.stderr)
            self.combined_output.append(f"<span style='color: red;'>{execution.stderr}</span>")
        
        # Update button states
        is_running = self.script_manager.is_execution_running(self.execution_id)
        self.cancel_button.setEnabled(is_running)
    
    def update_duration(self):
        """Update execution duration."""
        execution = self.script_manager.get_execution(self.execution_id)
        if not execution:
            return
        
        try:
            from datetime import datetime
            start_time = datetime.fromisoformat(execution.start_time)
            
            if execution.end_time:
                end_time = datetime.fromisoformat(execution.end_time)
                duration = end_time - start_time
            else:
                duration = datetime.now() - start_time
            
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes:02d}:{seconds:02d}"
            
            self.duration_label.setText(duration_str)
            
        except Exception as e:
            self.logger.error(f"Error updating duration: {e}")
    
    def on_output_received(self, execution_id: str, output: str):
        """Handle output received."""
        if execution_id != self.execution_id:
            return
        
        self.stdout_output.append(output)
        self.combined_output.append(output)
    
    def on_error_received(self, execution_id: str, error: str):
        """Handle error received."""
        if execution_id != self.execution_id:
            return
        
        self.stderr_output.append(error)
        self.combined_output.append(f"<span style='color: red;'>{error}</span>")
    
    def on_execution_finished(self, execution_id: str, exit_code: int):
        """Handle execution finished."""
        if execution_id != self.execution_id:
            return
        
        self.status_label.setText("Completed" if exit_code == 0 else "Failed")
        self.cancel_button.setEnabled(False)
        
        # Add final status message
        status_msg = f"\\n--- Execution finished with exit code {exit_code} ---"
        self.combined_output.append(status_msg)
    
    def cancel_execution(self):
        """Cancel script execution."""
        reply = QMessageBox.question(
            self, "Cancel Execution",
            "Are you sure you want to cancel this script execution?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.script_manager.cancel_execution(self.execution_id)
            if success:
                self.status_label.setText("Cancelled")
                self.cancel_button.setEnabled(False)
            else:
                QMessageBox.warning(self, "Error", "Could not cancel execution.")
    
    def save_output(self):
        """Save output to file."""
        execution = self.script_manager.get_execution(self.execution_id)
        if not execution:
            return
        
        script = self.script_manager.get_script(execution.script_id)
        script_name = script.name if script else "unknown"
        
        default_filename = f"{script_name}_output_{execution.start_time[:10]}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Script Output",
            str(Path.home() / default_filename),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Script: {script_name}\\n")
                    f.write(f"Execution ID: {execution.execution_id}\\n")
                    f.write(f"Started: {execution.start_time}\\n")
                    f.write(f"Status: {execution.status.value}\\n")
                    f.write(f"Exit Code: {execution.exit_code}\\n")
                    f.write("\\n" + "="*50 + "\\n")
                    f.write("STDOUT:\\n")
                    f.write(execution.stdout)
                    f.write("\\n" + "="*50 + "\\n")
                    f.write("STDERR:\\n")
                    f.write(execution.stderr)
                
                QMessageBox.information(self, "Success", f"Output saved to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save output: {e}")
    
    def apply_theme(self):
        """Apply current theme."""
        if hasattr(theme_manager, 'apply_theme'):
            theme_manager.apply_theme(self)
    
    def closeEvent(self, event):
        """Handle close event."""
        self.update_timer.stop()
        super().closeEvent(event)


class ScriptManagerTab(QWidget):
    """Main script manager tab widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.script_manager = get_script_manager()
        self.logger = get_logger(__name__)
        self.output_dialogs: Dict[str, ScriptOutputDialog] = {}
        
        self.setup_ui()
        self.apply_theme()
        self.load_scripts()
        
        # Connect to script manager signals
        self.script_manager.script_added.connect(self.on_script_added)
        self.script_manager.script_removed.connect(self.on_script_removed)
        self.script_manager.script_updated.connect(self.on_script_updated)
        self.script_manager.execution_started.connect(self.on_execution_started)
        self.script_manager.execution_finished.connect(self.on_execution_finished)
    
    def setup_ui(self):
        """Setup the tab UI."""
        layout = QVBoxLayout(self)
        
        # Header with actions
        header_layout = QHBoxLayout()
        
        header_layout.addWidget(QLabel("Script Manager"))
        header_layout.addStretch()
        
        # Add script button
        self.add_button = QPushButton("Add Script")
        self.add_button.clicked.connect(self.add_script)
        header_layout.addWidget(self.add_button)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_scripts)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - script list
        left_panel = self.create_script_list_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - script details and execution
        right_panel = self.create_script_details_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
    
    def create_script_list_panel(self) -> QWidget:
        """Create script list panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("All", None)
        self.type_filter.addItem("Host (Windows)", ScriptType.HOST_WINDOWS)
        self.type_filter.addItem("Host (Linux)", ScriptType.HOST_LINUX)
        self.type_filter.addItem("Device", ScriptType.DEVICE)
        self.type_filter.currentIndexChanged.connect(self.filter_scripts)
        filter_layout.addWidget(self.type_filter)
        
        layout.addLayout(filter_layout)
        
        # Script list
        self.script_list = QListWidget()
        self.script_list.currentItemChanged.connect(self.on_script_selected)
        self.script_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.script_list.customContextMenuRequested.connect(self.show_script_context_menu)
        layout.addWidget(self.script_list)
        
        return panel
    
    def create_script_details_panel(self) -> QWidget:
        """Create script details panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Script details
        details_group = QGroupBox("Script Details")
        details_layout = QFormLayout(details_group)
        
        self.details_name = QLabel()
        self.details_type = QLabel()
        self.details_path = QLabel()
        self.details_path.setWordWrap(True)
        self.details_description = QLabel()
        self.details_description.setWordWrap(True)
        self.details_created = QLabel()
        self.details_last_run = QLabel()
        self.details_run_count = QLabel()
        
        details_layout.addRow("Name:", self.details_name)
        details_layout.addRow("Type:", self.details_type)
        details_layout.addRow("Path:", self.details_path)
        details_layout.addRow("Description:", self.details_description)
        details_layout.addRow("Created:", self.details_created)
        details_layout.addRow("Last Run:", self.details_last_run)
        details_layout.addRow("Run Count:", self.details_run_count)
        
        layout.addWidget(details_group)
        
        # Execution section
        exec_group = QGroupBox("Execution")
        exec_layout = QVBoxLayout(exec_group)
        
        # Device selection for device scripts
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setEnabled(False)
        device_layout.addWidget(self.device_combo)
        device_layout.addStretch()
        
        exec_layout.addLayout(device_layout)
        
        # Execute button
        button_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("Execute Script")
        self.execute_button.clicked.connect(self.execute_script)
        self.execute_button.setEnabled(False)
        button_layout.addWidget(self.execute_button)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_script)
        self.edit_button.setEnabled(False)
        button_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_script)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)
        
        button_layout.addStretch()
        exec_layout.addLayout(button_layout)
        
        layout.addWidget(exec_group)
        
        # Recent executions
        history_group = QGroupBox("Recent Executions")
        history_layout = QVBoxLayout(history_group)
        
        self.execution_list = QListWidget()
        self.execution_list.itemDoubleClicked.connect(self.open_execution_output)
        history_layout.addWidget(self.execution_list)
        
        layout.addWidget(history_group)
        
        return panel
    
    def load_scripts(self):
        """Load scripts into the list."""
        self.script_list.clear()
        
        scripts = self.script_manager.get_all_scripts()
        for script in scripts:
            item = QListWidgetItem(script.name)
            item.setData(Qt.ItemDataRole.UserRole, script.id)
            
            # Set icon based on type
            if script.script_type == ScriptType.HOST_WINDOWS:
                item.setText(f"🖥️ {script.name}")
            elif script.script_type == ScriptType.HOST_LINUX:
                item.setText(f"🐧 {script.name}")
            else:  # DEVICE
                item.setText(f"📱 {script.name}")
            
            self.script_list.addItem(item)
        
        self.filter_scripts()
    
    def filter_scripts(self):
        """Filter scripts by type."""
        filter_type = self.type_filter.currentData()
        
        for i in range(self.script_list.count()):
            item = self.script_list.item(i)
            script_id = item.data(Qt.ItemDataRole.UserRole)
            script = self.script_manager.get_script(script_id)
            
            if filter_type is None or script.script_type == filter_type:
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def on_script_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle script selection."""
        if not current:
            self.clear_script_details()
            return
        
        script_id = current.data(Qt.ItemDataRole.UserRole)
        script = self.script_manager.get_script(script_id)
        
        if script:
            self.show_script_details(script)
            self.load_script_executions(script_id)
    
    def show_script_details(self, script: Script):
        """Show script details."""
        self.details_name.setText(script.name)
        self.details_type.setText(script.script_type.value.replace('_', ' ').title())
        self.details_path.setText(script.script_path)
        self.details_description.setText(script.description or "No description")
        self.details_created.setText(script.created_at)
        self.details_last_run.setText(script.last_run or "Never")
        self.details_run_count.setText(str(script.run_count))
        
        # Enable/disable controls
        self.execute_button.setEnabled(True)
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        
        # Setup device selection for device scripts
        if script.script_type == ScriptType.DEVICE:
            self.device_combo.setEnabled(True)
            self.load_devices()
        else:
            self.device_combo.setEnabled(False)
            self.device_combo.clear()
    
    def clear_script_details(self):
        """Clear script details."""
        self.details_name.setText("")
        self.details_type.setText("")
        self.details_path.setText("")
        self.details_description.setText("")
        self.details_created.setText("")
        self.details_last_run.setText("")
        self.details_run_count.setText("")
        
        self.execute_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.device_combo.setEnabled(False)
        self.device_combo.clear()
        self.execution_list.clear()
    
    def load_devices(self):
        """Load available devices for device scripts."""
        self.device_combo.clear()
        
        try:
            # Get devices from parent window's device manager
            parent_window = self.window()
            if hasattr(parent_window, 'devices') and parent_window.devices:
                for device in parent_window.devices:
                    if device.is_online:  # Only show online devices
                        self.device_combo.addItem(f"{device.display_name} ({device.id})", device.id)
                
                if self.device_combo.count() == 0:
                    self.device_combo.addItem("No online devices available")
            else:
                self.device_combo.addItem("No devices available")
                
        except Exception as e:
            self.logger.error(f"Error loading devices: {e}")
            self.device_combo.addItem("Error loading devices")
    
    def load_script_executions(self, script_id: str):
        """Load executions for selected script."""
        self.execution_list.clear()
        
        executions = self.script_manager.get_executions_for_script(script_id)
        executions.sort(key=lambda x: x.start_time, reverse=True)
        
        for execution in executions[:10]:  # Show last 10
            status_icon = {
                ScriptStatus.COMPLETED: "✅",
                ScriptStatus.FAILED: "❌",
                ScriptStatus.RUNNING: "🔄",
                ScriptStatus.CANCELLED: "⚠️",
                ScriptStatus.IDLE: "⏸️"
            }.get(execution.status, "❓")
            
            item_text = f"{status_icon} {execution.start_time[:19]} (Exit: {execution.exit_code})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, execution.execution_id)
            
            self.execution_list.addItem(item)
    
    def add_script(self):
        """Add new script."""
        dialog = ScriptAddDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_script_data()
            if data:
                try:
                    script_id = self.script_manager.add_script(**data)
                    self.logger.info(f"Script added: {data['name']} ({script_id})")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add script: {e}")
    
    def edit_script(self):
        """Edit selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            return
        
        script_id = current_item.data(Qt.ItemDataRole.UserRole)
        script = self.script_manager.get_script(script_id)
        
        if not script:
            return
        
        # Open script file in external editor
        try:
            if os.name == 'nt':  # Windows
                os.startfile(script.script_path)
            else:  # Linux/Mac
                os.system(f"xdg-open '{script.script_path}'")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open script file: {e}")
    
    def delete_script(self):
        """Delete selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            return
        
        script_id = current_item.data(Qt.ItemDataRole.UserRole)
        script = self.script_manager.get_script(script_id)
        
        if not script:
            return
        
        reply = QMessageBox.question(
            self, "Delete Script",
            f"Are you sure you want to delete '{script.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.script_manager.remove_script(script_id)
            if success:
                self.logger.info(f"Script deleted: {script.name}")
            else:
                QMessageBox.warning(self, "Error", "Could not delete script.")
    
    def execute_script(self):
        """Execute selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            return
        
        script_id = current_item.data(Qt.ItemDataRole.UserRole)
        script = self.script_manager.get_script(script_id)
        
        if not script:
            return
        
        # Check if script file exists
        if not Path(script.script_path).exists():
            QMessageBox.warning(
                self, "Error", 
                f"Script file not found: {script.script_path}"
            )
            return
        
        # Get device ID for device scripts
        device_id = None
        if script.script_type == ScriptType.DEVICE:
            if self.device_combo.count() == 0 or not self.device_combo.isEnabled():
                QMessageBox.warning(
                    self, "Error", 
                    "No device selected. Please connect a device first."
                )
                return
            device_id = self.device_combo.currentData()
            if not device_id:
                QMessageBox.warning(
                    self, "Error", 
                    "Please select a valid device."
                )
                return
        
        try:
            execution_id = self.script_manager.execute_script(script_id, device_id)
            
            # Open output dialog
            output_dialog = ScriptOutputDialog(execution_id, self)
            output_dialog.show()
            self.output_dialogs[execution_id] = output_dialog
            
            self.logger.info(f"Script execution started: {script.name} ({execution_id})")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to execute script: {e}")
    
    def open_execution_output(self, item: QListWidgetItem):
        """Open execution output dialog."""
        execution_id = item.data(Qt.ItemDataRole.UserRole)
        
        # Check if dialog is already open
        if execution_id in self.output_dialogs:
            dialog = self.output_dialogs[execution_id]
            dialog.raise_()
            dialog.activateWindow()
        else:
            dialog = ScriptOutputDialog(execution_id, self)
            dialog.show()
            self.output_dialogs[execution_id] = dialog
    
    def show_script_context_menu(self, position):
        """Show context menu for script list."""
        item = self.script_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        execute_action = QAction("Execute", self)
        execute_action.triggered.connect(self.execute_script)
        menu.addAction(execute_action)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self.edit_script)
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_script)
        menu.addAction(delete_action)
        
        menu.exec(self.script_list.mapToGlobal(position))
    
    def on_script_added(self, script_id: str):
        """Handle script added."""
        self.load_scripts()
    
    def on_script_removed(self, script_id: str):
        """Handle script removed."""
        self.load_scripts()
        self.clear_script_details()
    
    def on_script_updated(self, script_id: str):
        """Handle script updated."""
        current_item = self.script_list.currentItem()
        if current_item and current_item.data(Qt.ItemDataRole.UserRole) == script_id:
            script = self.script_manager.get_script(script_id)
            if script:
                self.show_script_details(script)
        self.load_scripts()
    
    def on_execution_started(self, execution_id: str):
        """Handle execution started."""
        # Refresh execution list if showing executions for this script
        current_item = self.script_list.currentItem()
        if current_item:
            script_id = current_item.data(Qt.ItemDataRole.UserRole)
            execution = self.script_manager.get_execution(execution_id)
            if execution and execution.script_id == script_id:
                self.load_script_executions(script_id)
    
    def on_execution_finished(self, execution_id: str, exit_code: int):
        """Handle execution finished."""
        # Refresh execution list
        current_item = self.script_list.currentItem()
        if current_item:
            script_id = current_item.data(Qt.ItemDataRole.UserRole)
            execution = self.script_manager.get_execution(execution_id)
            if execution and execution.script_id == script_id:
                self.load_script_executions(script_id)
        
        # Clean up dialog reference
        if execution_id in self.output_dialogs:
            dialog = self.output_dialogs[execution_id]
            if not dialog.isVisible():
                del self.output_dialogs[execution_id]
    
    def apply_theme(self):
        """Apply current theme."""
        if hasattr(theme_manager, 'apply_theme'):
            theme_manager.apply_theme(self)
    
    def showEvent(self, event):
        """Handle show event to refresh device list."""
        super().showEvent(event)
        # Refresh device list when tab is shown
        if hasattr(self, 'device_combo') and self.device_combo.isEnabled():
            self.load_devices()
    
    def closeEvent(self, event):
        """Handle close event."""
        # Close all output dialogs
        for dialog in list(self.output_dialogs.values()):
            dialog.close()
        super().closeEvent(event)
