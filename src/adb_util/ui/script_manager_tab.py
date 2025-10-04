"""
Script Manager Tab

GUI component for managing and executing scripts (host and device).
Supports Windows .bat files and Linux .sh files with async output capture.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..services.script_manager import (
    Script,
    ScriptExecution,
    ScriptStatus,
    ScriptType,
    get_script_manager,
)
from ..utils.logger import get_logger
from ..utils.theme_manager import theme_manager


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
            self.combined_output.append(
                f"<span style='color: red;'>{execution.stderr}</span>"
            )

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
            self,
            "Cancel Execution",
            "Are you sure you want to cancel this script execution?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
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
            self,
            "Save Script Output",
            str(Path.home() / default_filename),
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"Script: {script_name}\\n")
                    f.write(f"Execution ID: {execution.execution_id}\\n")
                    f.write(f"Started: {execution.start_time}\\n")
                    f.write(f"Status: {execution.status.value}\\n")
                    f.write(f"Exit Code: {execution.exit_code}\\n")
                    f.write("\\n" + "=" * 50 + "\\n")
                    f.write("STDOUT:\\n")
                    f.write(execution.stdout)
                    f.write("\\n" + "=" * 50 + "\\n")
                    f.write("STDERR:\\n")
                    f.write(execution.stderr)

                QMessageBox.information(self, "Success", f"Output saved to {file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save output: {e}")

    def apply_theme(self):
        """Apply current theme."""
        if hasattr(theme_manager, "apply_theme"):
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

        title_label = QLabel("Script Manager")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Add script button
        self.add_button = QPushButton("📝 New Script")
        self.add_button.clicked.connect(self.add_script)
        self.add_button.setToolTip("Create a new script")
        header_layout.addWidget(self.add_button)

        # Import script button
        self.import_button = QPushButton("📁 Import")
        self.import_button.clicked.connect(self.import_script)
        self.import_button.setToolTip("Import script from file")
        header_layout.addWidget(self.import_button)

        # Export JSON button
        self.export_json_button = QPushButton("📤 Export JSON")
        self.export_json_button.clicked.connect(self.export_scripts_json)
        self.export_json_button.setToolTip("Export scripts to JSON format")
        header_layout.addWidget(self.export_json_button)

        # Import JSON button
        self.import_json_button = QPushButton("📥 Import JSON")
        self.import_json_button.clicked.connect(self.import_scripts_json)
        self.import_json_button.setToolTip("Import scripts from JSON format")
        header_layout.addWidget(self.import_json_button)

        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.load_scripts)
        self.refresh_button.setToolTip("Refresh script list")
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
        self.script_list.customContextMenuRequested.connect(
            self.show_script_context_menu
        )
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
        self.details_template = QLabel()
        self.details_visible = QLabel()

        details_layout.addRow("Name:", self.details_name)
        details_layout.addRow("Type:", self.details_type)
        details_layout.addRow("Path:", self.details_path)
        details_layout.addRow("Description:", self.details_description)
        details_layout.addRow("Template:", self.details_template)
        details_layout.addRow("Visible:", self.details_visible)
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
            # Skip hidden scripts
            if not script.is_visible:
                continue

            item = QListWidgetItem(script.name)
            item.setData(Qt.ItemDataRole.UserRole, script.id)

            # Set icon based on type and template status
            icon = ""
            if script.script_type == ScriptType.HOST_WINDOWS:
                icon = "🖥️"
            elif script.script_type == ScriptType.HOST_LINUX:
                icon = "🐧"
            else:  # DEVICE
                icon = "📱"

            # Add template indicator
            template_indicator = " 📄" if script.is_template else ""
            item.setText(f"{icon} {script.name}{template_indicator}")

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
        self.details_type.setText(script.script_type.value.replace("_", " ").title())
        self.details_path.setText(script.script_path)
        self.details_description.setText(script.description or "No description")
        self.details_template.setText("Yes" if script.is_template else "No")
        self.details_visible.setText("Yes" if script.is_visible else "No")
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
        self.details_template.setText("")
        self.details_visible.setText("")
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
            if hasattr(parent_window, "devices") and parent_window.devices:
                for device in parent_window.devices:
                    if device.is_online:  # Only show online devices
                        self.device_combo.addItem(
                            f"{device.display_name} ({device.id})", device.id
                        )

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
                ScriptStatus.IDLE: "⏸️",
            }.get(execution.status, "❓")

            item_text = f"{status_icon} {execution.start_time[:19]} (Exit: {execution.exit_code})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, execution.execution_id)

            self.execution_list.addItem(item)

    def add_script(self):
        """Add new script."""
        from .script_editor_dialog import ScriptEditorDialog

        dialog = ScriptEditorDialog(parent=self)
        dialog.script_saved.connect(self.on_script_saved)
        dialog.show()

    def edit_script(self):
        """Edit selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            return

        script_id = current_item.data(Qt.ItemDataRole.UserRole)
        script = self.script_manager.get_script(script_id)

        if not script:
            return

        from .script_editor_dialog import ScriptEditorDialog

        dialog = ScriptEditorDialog(script, parent=self)
        dialog.script_saved.connect(self.on_script_saved)
        dialog.show()

    def import_script(self):
        """Import script from file."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter(
            "Script Files (*.bat *.sh);;Batch Files (*.bat);;Shell Scripts (*.sh);;All Files (*)"
        )

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                file_path = Path(file_paths[0])

                try:
                    # Read file content
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Determine script type based on extension
                    if file_path.suffix.lower() == ".bat":
                        script_type = ScriptType.HOST_WINDOWS
                    else:
                        script_type = (
                            ScriptType.HOST_LINUX
                        )  # Default to Linux for .sh files

                    # Copy file to scripts directory
                    scripts_dir = Path.home() / ".adb-util" / "user_scripts"
                    scripts_dir.mkdir(parents=True, exist_ok=True)

                    new_path = scripts_dir / file_path.name
                    counter = 1
                    while new_path.exists():
                        stem = file_path.stem
                        suffix = file_path.suffix
                        new_path = scripts_dir / f"{stem}_{counter}{suffix}"
                        counter += 1

                    with open(new_path, "w", encoding="utf-8") as f:
                        f.write(content)

                    # Make executable if shell script on Unix
                    if (
                        script_type in [ScriptType.HOST_LINUX, ScriptType.DEVICE]
                        and os.name != "nt"
                    ):
                        os.chmod(new_path, 0o755)

                    # Add to script manager
                    script_name = file_path.stem
                    script_id = self.script_manager.add_script(
                        script_name,
                        script_type,
                        str(new_path),
                        f"Imported from {file_path.name}",
                    )

                    QMessageBox.information(
                        self,
                        "Success",
                        f"Script '{script_name}' imported successfully.",
                    )

                    self.logger.info(f"Script imported: {script_name} from {file_path}")

                except Exception as e:
                    QMessageBox.critical(
                        self, "Import Error", f"Failed to import script:\n{e}"
                    )
                    self.logger.error(f"Failed to import script: {e}")

    def on_script_saved(self, script_id: str):
        """Handle script saved from editor."""
        self.load_scripts()
        # Select the saved script
        for i in range(self.script_list.count()):
            item = self.script_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == script_id:
                self.script_list.setCurrentItem(item)
                break

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
            self,
            "Delete Script",
            f"Are you sure you want to delete '{script.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
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
                self, "Error", f"Script file not found: {script.script_path}"
            )
            return

        # Get device ID for device scripts
        device_id = None
        if script.script_type == ScriptType.DEVICE:
            if self.device_combo.count() == 0 or not self.device_combo.isEnabled():
                QMessageBox.warning(
                    self, "Error", "No device selected. Please connect a device first."
                )
                return
            device_id = self.device_combo.currentData()
            if not device_id:
                QMessageBox.warning(self, "Error", "Please select a valid device.")
                return

        try:
            execution_id = self.script_manager.execute_script(script_id, device_id)

            # Open output dialog
            output_dialog = ScriptOutputDialog(execution_id, self)
            output_dialog.show()
            self.output_dialogs[execution_id] = output_dialog

            self.logger.info(
                f"Script execution started: {script.name} ({execution_id})"
            )

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

        menu = QMenu(self)

        # Always show "New Script" action
        new_action = QAction("📝 New Script", self)
        new_action.triggered.connect(self.add_script)
        menu.addAction(new_action)

        # Show import action
        import_action = QAction("📁 Import Script", self)
        import_action.triggered.connect(self.import_script)
        menu.addAction(import_action)

        # JSON import/export actions
        menu.addSeparator()

        export_json_action = QAction("📤 Export to JSON", self)
        export_json_action.triggered.connect(self.export_scripts_json)
        menu.addAction(export_json_action)

        import_json_action = QAction("📥 Import from JSON", self)
        import_json_action.triggered.connect(self.import_scripts_json)
        menu.addAction(import_json_action)

        if item:
            menu.addSeparator()

            execute_action = QAction("▶️ Execute", self)
            execute_action.triggered.connect(self.execute_script)
            menu.addAction(execute_action)

            edit_action = QAction("✏️ Edit", self)
            edit_action.triggered.connect(self.edit_script)
            menu.addAction(edit_action)

            menu.addSeparator()

            duplicate_action = QAction("📋 Duplicate", self)
            duplicate_action.triggered.connect(self.duplicate_script)
            menu.addAction(duplicate_action)

            export_action = QAction("💾 Export", self)
            export_action.triggered.connect(self.export_script)
            menu.addAction(export_action)

            menu.addSeparator()

            delete_action = QAction("🗑️ Delete", self)
            delete_action.triggered.connect(self.delete_script)
            menu.addAction(delete_action)

        menu.exec(self.script_list.mapToGlobal(position))

    def duplicate_script(self):
        """Duplicate selected script."""
        current_item = self.script_list.currentItem()
        if not current_item:
            return

        script_id = current_item.data(Qt.ItemDataRole.UserRole)
        script = self.script_manager.get_script(script_id)

        if not script:
            return

        try:
            # Read original script content
            with open(script.script_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Create new script with "Copy" suffix
            new_name = f"{script.name} - Copy"
            scripts_dir = Path(script.script_path).parent

            # Determine file extension
            if script.script_type == ScriptType.HOST_WINDOWS:
                extension = ".bat"
            else:
                extension = ".sh"

            # Generate unique filename
            safe_name = "".join(
                c for c in new_name if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_name = safe_name.replace(" ", "_")
            new_path = scripts_dir / f"{safe_name}{extension}"

            counter = 1
            while new_path.exists():
                new_path = scripts_dir / f"{safe_name}_{counter}{extension}"
                counter += 1

            # Write content to new file
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Make executable if shell script on Unix
            if (
                script.script_type in [ScriptType.HOST_LINUX, ScriptType.DEVICE]
                and os.name != "nt"
            ):
                os.chmod(new_path, 0o755)

            # Add to script manager
            new_script_id = self.script_manager.add_script(
                new_name,
                script.script_type,
                str(new_path),
                f"Copy of: {script.description}"
                if script.description
                else "Duplicated script",
            )

            self.logger.info(f"Script duplicated: {script.name} -> {new_name}")

        except Exception as e:
            QMessageBox.critical(
                self, "Duplicate Error", f"Failed to duplicate script:\n{e}"
            )
            self.logger.error(f"Failed to duplicate script: {e}")

    def export_script(self):
        """Export script to file."""
        current_item = self.script_list.currentItem()
        if not current_item:
            return

        script_id = current_item.data(Qt.ItemDataRole.UserRole)
        script = self.script_manager.get_script(script_id)

        if not script:
            return

        # Determine file filter based on script type
        if script.script_type == ScriptType.HOST_WINDOWS:
            file_filter = "Batch Files (*.bat);;All Files (*)"
            default_ext = ".bat"
        else:
            file_filter = "Shell Scripts (*.sh);;All Files (*)"
            default_ext = ".sh"

        # Default filename
        safe_name = "".join(
            c for c in script.name if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        safe_name = safe_name.replace(" ", "_")
        default_name = f"{safe_name}{default_ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Script", str(Path.home() / default_name), file_filter
        )

        if file_path:
            try:
                # Copy script file
                import shutil

                shutil.copy2(script.script_path, file_path)

                QMessageBox.information(
                    self, "Success", f"Script exported to:\n{file_path}"
                )

                self.logger.info(f"Script exported: {script.name} to {file_path}")

            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export script:\n{e}"
                )
                self.logger.error(f"Failed to export script: {e}")

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

    def export_scripts_json(self):
        """Export scripts to JSON format."""
        # Get selected scripts or all scripts
        selected_items = self.script_list.selectedItems()
        script_ids = None

        if selected_items:
            script_ids = [
                item.data(Qt.ItemDataRole.UserRole) for item in selected_items
            ]
            count_text = f"{len(script_ids)} selected scripts"
        else:
            count_text = "all scripts"

        # Get save file path
        default_filename = (
            f"adb_util_scripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {count_text} to JSON",
            str(Path.home() / default_filename),
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            try:
                success = self.script_manager.export_scripts_to_json(
                    file_path, script_ids
                )

                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Scripts exported successfully to:\n{file_path}",
                    )
                    self.logger.info(f"Scripts exported to JSON: {file_path}")
                else:
                    QMessageBox.critical(
                        self,
                        "Export Error",
                        "Failed to export scripts. Check logs for details.",
                    )

            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export scripts:\n{e}"
                )
                self.logger.error(f"Failed to export scripts: {e}")

    def import_scripts_json(self):
        """Import scripts from JSON format."""
        # Get file to import
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Scripts from JSON",
            str(Path.home()),
            "JSON Files (*.json);;All Files (*)",
        )

        if not file_path:
            return

        # Ask about overwriting existing scripts
        reply = QMessageBox.question(
            self,
            "Import Options",
            "Do you want to overwrite existing scripts with the same name?\n\n"
            "Yes: Overwrite existing scripts\n"
            "No: Skip existing scripts\n"
            "Cancel: Abort import",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        overwrite_existing = reply == QMessageBox.StandardButton.Yes

        try:
            (
                imported_count,
                skipped_count,
            ) = self.script_manager.import_scripts_from_json(
                file_path, overwrite_existing
            )

            # Show results
            message_parts = []
            if imported_count > 0:
                message_parts.append(
                    f"✅ {imported_count} scripts imported successfully"
                )
            if skipped_count > 0:
                message_parts.append(f"⚠️ {skipped_count} scripts skipped")

            if imported_count == 0 and skipped_count == 0:
                message = "No scripts were imported. Check the JSON file format."
                QMessageBox.warning(self, "Import Result", message)
            else:
                message = "\n".join(message_parts)
                QMessageBox.information(self, "Import Result", message)

                # Refresh the script list if any scripts were imported
                if imported_count > 0:
                    self.load_scripts()

            self.logger.info(
                f"Scripts imported from JSON: {file_path} - {imported_count} imported, {skipped_count} skipped"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Import Error", f"Failed to import scripts:\n{e}"
            )
            self.logger.error(f"Failed to import scripts: {e}")

    def apply_theme(self):
        """Apply current theme."""
        if hasattr(theme_manager, "apply_theme"):
            theme_manager.apply_theme(self)

    def showEvent(self, event):
        """Handle show event to refresh device list."""
        super().showEvent(event)
        # Refresh device list when tab is shown
        if hasattr(self, "device_combo") and self.device_combo.isEnabled():
            self.load_devices()

    def closeEvent(self, event):
        """Handle close event."""
        # Close all output dialogs
        for dialog in list(self.output_dialogs.values()):
            dialog.close()
        super().closeEvent(event)
