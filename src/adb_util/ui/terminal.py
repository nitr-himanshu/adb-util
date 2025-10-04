"""
Terminal UI

Interactive ADB shell with command history and saved commands.
"""

import asyncio
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QSplitter, QListWidget,
    QLabel, QFrame, QGroupBox, QComboBox,
    QMessageBox, QInputDialog, QMenu, QListWidgetItem,
    QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QAction, QColor, QTextCharFormat

from ..core.command_runner import CommandRunner
from ..utils.logger import get_logger
from ..utils.constants import COMMAND_TIMEOUT


class CommandWorker(QThread):
    """Worker thread for executing ADB commands."""
    
    command_finished = pyqtSignal(str, str, int)  # stdout, stderr, return_code
    command_started = pyqtSignal(str)  # command
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.command_runner = CommandRunner(device_id)
        self.command_queue = []
        self.logger = get_logger(__name__)
    
    def add_command(self, command: str):
        """Add command to execution queue."""
        self.command_queue.append(command)
        if not self.isRunning():
            self.start()
    
    def run(self):
        """Execute commands from queue."""
        while self.command_queue:
            command = self.command_queue.pop(0)
            
            try:
                self.command_started.emit(command)
                
                # Create event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Execute the command
                    stdout, stderr, return_code = loop.run_until_complete(
                        self.command_runner.execute_command(f"shell {command}")
                    )
                    
                    self.command_finished.emit(stdout, stderr, return_code)
                    
                finally:
                    loop.close()
                    
            except Exception as e:
                self.logger.error(f"Command execution error: {e}")
                self.command_finished.emit("", f"Error: {str(e)}", 1)


class Terminal(QWidget):
    """Terminal widget for ADB shell commands."""
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.logger = get_logger(__name__)
        
        # Command history
        self.command_history = []
        self.history_index = -1
        
        # Saved commands
        self.saved_commands = self.load_saved_commands()
        
        # Command worker
        self.command_worker = CommandWorker(device_id)
        self.command_worker.command_finished.connect(self.on_command_finished)
        self.command_worker.command_started.connect(self.on_command_started)
        
        # Current directory tracking
        self.current_directory = "/"
        
        # Terminal state
        self.is_command_running = False
        
        self.logger.info(f"Initializing terminal for device: {device_id}")
        self.init_ui()
        self.setup_connections()
        self.initialize_terminal()
        self.logger.info("Terminal initialization complete")
    
    def init_ui(self):
        """Initialize the terminal UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        terminal_label = QLabel(f"💻 Terminal - {self.device_id}")
        terminal_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(terminal_label)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        header_layout.addWidget(self.status_label)
        
        # Terminal controls
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_terminal)
        header_layout.addWidget(clear_btn)
        
        save_session_btn = QPushButton("💾 Save Session")
        save_session_btn.clicked.connect(self.save_session)
        header_layout.addWidget(save_session_btn)
        
        layout.addLayout(header_layout)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Create terminal panel
        terminal_panel = self.create_terminal_panel()
        splitter.addWidget(terminal_panel)
        
        # Create saved commands panel
        commands_panel = self.create_saved_commands_panel()
        splitter.addWidget(commands_panel)
        
        # Set splitter proportions
        splitter.setSizes([700, 300])
    
    def create_terminal_panel(self):
        """Create the main terminal panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setFont(QFont("Consolas", 10))
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
                selection-background-color: #3399ff;
            }
        """)
        self.terminal_output.setReadOnly(True)
        layout.addWidget(self.terminal_output)
        
        # Command input area
        input_layout = QHBoxLayout()
        
        # Current directory label
        self.dir_label = QLabel("/")
        self.dir_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.dir_label.setStyleSheet("color: #00ff00;")
        input_layout.addWidget(self.dir_label)
        
        # Prompt label
        prompt_label = QLabel("$")
        prompt_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        prompt_label.setStyleSheet("color: #ffffff;")
        input_layout.addWidget(prompt_label)
        
        # Command input
        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Consolas", 10))
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444444;
                padding: 5px;
            }
        """)
        self.command_input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.command_input)
        
        # Execute button
        self.execute_btn = QPushButton("⚡ Execute")
        self.execute_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(self.execute_btn)
        
        layout.addLayout(input_layout)
        
        return panel
    
    def create_saved_commands_panel(self):
        """Create the saved commands panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Header
        header_layout = QHBoxLayout()
        
        commands_label = QLabel("📚 Saved Commands")
        commands_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(commands_label)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self.add_saved_command)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Category selector
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "System", "Files", "Process", "Network", "Custom"])
        self.category_combo.currentTextChanged.connect(self.filter_commands)
        category_layout.addWidget(self.category_combo)
        
        layout.addLayout(category_layout)
        
        # Commands list
        self.saved_commands_list = QListWidget()
        self.saved_commands_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.saved_commands_list.customContextMenuRequested.connect(self.show_command_context_menu)
        self.saved_commands_list.itemDoubleClicked.connect(self.execute_saved_command)
        layout.addWidget(self.saved_commands_list)
        
        # Quick commands section
        quick_group = QGroupBox("⚡ Quick Commands")
        quick_layout = QVBoxLayout(quick_group)
        
        quick_commands = [
            ("📱 Device Info", "getprop"),
            ("📁 List Files", "ls -la"),
            ("💾 Disk Usage", "df -h"),
            ("🔄 Processes", "ps"),
            ("🌐 Network", "netstat -tuln"),
            ("📊 Memory", "cat /proc/meminfo"),
        ]
        
        for name, command in quick_commands:
            btn = QPushButton(name)
            btn.setToolTip(f"Execute: {command}")
            btn.clicked.connect(lambda checked, cmd=command: self.execute_quick_command(cmd))
            quick_layout.addWidget(btn)
        
        layout.addWidget(quick_group)
        
        return panel
    
    def setup_connections(self):
        """Setup signal connections and event handlers."""
        # Override key press for command input
        self.command_input.keyPressEvent = self.handle_key_press
        
        # Load saved commands
        self.refresh_commands_list()
    
    def initialize_terminal(self):
        """Initialize the terminal with welcome message."""
        self.add_terminal_output("=== ADB Terminal Session ===", "system")
        self.add_terminal_output(f"Connected to device: {self.device_id}", "system")
        self.add_terminal_output(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "system")
        self.add_terminal_output("Type 'help' for available commands", "system")
        self.add_terminal_output("=" * 50, "system")
        
        # Get initial working directory
        self.update_working_directory()
    
    def handle_key_press(self, event):
        """Handle key press events for command input."""
        # Call original keyPressEvent first
        QLineEdit.keyPressEvent(self.command_input, event)
        
        # Handle special keys
        if event.key() == Qt.Key.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down:
            self.navigate_history(1)
        elif event.key() == Qt.Key.Key_Tab:
            self.auto_complete()
    
    def navigate_history(self, direction):
        """Navigate through command history."""
        if not self.command_history:
            return
        
        if direction == -1:  # Up
            if self.history_index > 0:
                self.history_index -= 1
        else:  # Down
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
            else:
                self.command_input.clear()
                self.history_index = len(self.command_history)
                return
        
        if 0 <= self.history_index < len(self.command_history):
            self.command_input.setText(self.command_history[self.history_index])
    
    def auto_complete(self):
        """Basic auto-completion for common commands."""
        current_text = self.command_input.text()
        
        common_commands = [
            "ls", "cd", "pwd", "cat", "grep", "find", "ps", "top", "df", "du",
            "chmod", "chown", "cp", "mv", "rm", "mkdir", "rmdir", "touch",
            "getprop", "setprop", "am", "pm", "dumpsys", "logcat", "netstat"
        ]
        
        matches = [cmd for cmd in common_commands if cmd.startswith(current_text)]
        
        if len(matches) == 1:
            self.command_input.setText(matches[0] + " ")
        elif len(matches) > 1:
            self.add_terminal_output(f"Possible completions: {', '.join(matches)}", "info")
    
    def execute_command(self):
        """Execute the command from input field."""
        if self.is_command_running:
            QMessageBox.warning(self, "Command Running", "Please wait for the current command to finish.")
            return
        
        command = self.command_input.text().strip()
        if not command:
            return
        
        # Add to history
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Clear input
        self.command_input.clear()
        
        # Handle built-in commands
        if self.handle_builtin_command(command):
            return
        
        # Show command in terminal
        self.add_terminal_output(f"{self.current_directory}$ {command}", "command")
        
        # Execute command
        self.is_command_running = True
        self.command_worker.add_command(command)
    
    def execute_quick_command(self, command):
        """Execute a quick command."""
        self.command_input.setText(command)
        self.execute_command()
    
    def execute_saved_command(self, item):
        """Execute a saved command."""
        command_data = item.data(Qt.ItemDataRole.UserRole)
        if command_data:
            command = command_data.get('command', '')
            self.command_input.setText(command)
            self.execute_command()
    
    def handle_builtin_command(self, command):
        """Handle built-in terminal commands."""
        parts = command.split()
        cmd = parts[0].lower()
        
        if cmd == "help":
            self.show_help()
            return True
        elif cmd == "clear":
            self.clear_terminal()
            return True
        elif cmd == "history":
            self.show_history()
            return True
        elif cmd == "pwd":
            self.add_terminal_output(f"Current directory: {self.current_directory}", "info")
            return True
        
        return False
    
    def show_help(self):
        """Show help information."""
        help_text = """
Available built-in commands:
  help     - Show this help message
  clear    - Clear terminal output
  history  - Show command history
  pwd      - Show current directory

Common ADB shell commands:
  ls [-la]           - List files and directories
  cd <directory>     - Change directory
  cat <file>         - Display file contents
  ps                 - List running processes
  getprop            - Show system properties
  dumpsys <service>  - Dump system service info
  netstat -tuln      - Show network connections
  df -h              - Show disk usage
  top                - Show running processes (real-time)
  
Use ↑/↓ arrow keys to navigate command history
Use Tab for auto-completion
        """
        self.add_terminal_output(help_text, "info")
    
    def show_history(self):
        """Show command history."""
        if not self.command_history:
            self.add_terminal_output("No command history available", "info")
            return
        
        self.add_terminal_output("Command History:", "info")
        for i, cmd in enumerate(self.command_history[-10:], 1):  # Show last 10
            self.add_terminal_output(f"  {i}. {cmd}", "info")
    
    def on_command_started(self, command):
        """Handle command start."""
        self.status_label.setText("Running...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.execute_btn.setEnabled(False)
    
    def on_command_finished(self, stdout, stderr, return_code):
        """Handle command completion."""
        self.is_command_running = False
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.execute_btn.setEnabled(True)
        
        # Display output
        if stdout:
            self.add_terminal_output(stdout, "output")
        
        if stderr:
            self.add_terminal_output(stderr, "error")
        
        if return_code != 0 and not stderr:
            self.add_terminal_output(f"Command exited with code: {return_code}", "error")
        
        # Update working directory if command was 'cd'
        if self.command_history and self.command_history[-1].strip().startswith('cd '):
            self.update_working_directory()
    
    def update_working_directory(self):
        """Update the current working directory display."""
        # Get current directory from device
        self.command_worker.add_command("pwd")
    
    def add_terminal_output(self, text, output_type="normal"):
        """Add text to terminal output with formatting."""
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Set formatting based on output type
        format = QTextCharFormat()
        
        if output_type == "command":
            format.setForeground(QColor("#00ff00"))  # Green
            format.setFontWeight(QFont.Weight.Bold)
        elif output_type == "output":
            format.setForeground(QColor("#ffffff"))  # White
        elif output_type == "error":
            format.setForeground(QColor("#ff6666"))  # Red
        elif output_type == "system":
            format.setForeground(QColor("#ffff00"))  # Yellow
        elif output_type == "info":
            format.setForeground(QColor("#66ccff"))  # Light blue
        else:
            format.setForeground(QColor("#ffffff"))  # White
        
        # Insert text with formatting
        cursor.setCharFormat(format)
        cursor.insertText(text + "\n")
        
        # Auto-scroll to bottom
        scrollbar = self.terminal_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_terminal(self):
        """Clear terminal output."""
        self.terminal_output.clear()
        self.add_terminal_output("Terminal cleared", "system")
    
    def save_session(self):
        """Save terminal session to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Terminal Session",
            f"terminal_session_{self.device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"ADB Terminal Session - Device: {self.device_id}\n")
                    f.write(f"Session Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(self.terminal_output.toPlainText())
                
                QMessageBox.information(self, "Session Saved", f"Terminal session saved to:\n{filename}")
                self.logger.info(f"Terminal session saved to: {filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save session:\n{str(e)}")
                self.logger.error(f"Failed to save terminal session: {e}")
    
    def load_saved_commands(self):
        """Load saved commands from file."""
        config_dir = os.path.expanduser("~/.adb-util")
        commands_file = os.path.join(config_dir, "saved_commands.json")
        
        if os.path.exists(commands_file):
            try:
                with open(commands_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load saved commands: {e}")
        
        # Return default commands if file doesn't exist
        return {
            "System": [
                {"name": "Device Properties", "command": "getprop"},
                {"name": "System Information", "command": "uname -a"},
                {"name": "Uptime", "command": "uptime"},
                {"name": "Date/Time", "command": "date"},
            ],
            "Files": [
                {"name": "List Root", "command": "ls -la /"},
                {"name": "List Data", "command": "ls -la /data"},
                {"name": "List System", "command": "ls -la /system"},
                {"name": "Disk Usage", "command": "df -h"},
            ],
            "Process": [
                {"name": "Running Processes", "command": "ps"},
                {"name": "Top Processes", "command": "top -n 1"},
                {"name": "Memory Info", "command": "cat /proc/meminfo"},
                {"name": "CPU Info", "command": "cat /proc/cpuinfo"},
            ],
            "Network": [
                {"name": "Network Interfaces", "command": "ip addr"},
                {"name": "Network Connections", "command": "netstat -tuln"},
                {"name": "WiFi Status", "command": "dumpsys wifi"},
                {"name": "Ping Google", "command": "ping -c 4 8.8.8.8"},
            ]
        }
    
    def save_saved_commands(self):
        """Save commands to file."""
        config_dir = os.path.expanduser("~/.adb-util")
        os.makedirs(config_dir, exist_ok=True)
        commands_file = os.path.join(config_dir, "saved_commands.json")
        
        try:
            with open(commands_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_commands, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save commands: {e}")
    
    def refresh_commands_list(self):
        """Refresh the saved commands list."""
        self.saved_commands_list.clear()
        
        current_category = self.category_combo.currentText()
        
        for category, commands in self.saved_commands.items():
            if current_category == "All" or current_category == category:
                for cmd_data in commands:
                    item = QListWidgetItem(f"{cmd_data['name']} - {cmd_data['command']}")
                    item.setData(Qt.ItemDataRole.UserRole, cmd_data)
                    item.setToolTip(f"Category: {category}\nCommand: {cmd_data['command']}")
                    self.saved_commands_list.addItem(item)
    
    def add_saved_command(self):
        """Add a new saved command."""
        name, ok = QInputDialog.getText(self, "Add Command", "Command name:")
        if not ok or not name.strip():
            return
        
        command, ok = QInputDialog.getText(self, "Add Command", "Command:")
        if not ok or not command.strip():
            return
        
        category = self.category_combo.currentText()
        if category == "All":
            category = "Custom"
        
        if category not in self.saved_commands:
            self.saved_commands[category] = []
        
        self.saved_commands[category].append({
            "name": name.strip(),
            "command": command.strip()
        })
        
        self.save_saved_commands()
        self.refresh_commands_list()
    
    def show_command_context_menu(self, position):
        """Show context menu for saved commands."""
        if self.saved_commands_list.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        execute_action = QAction("Execute", self)
        execute_action.triggered.connect(self.execute_saved_command_from_menu)
        menu.addAction(execute_action)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self.edit_saved_command)
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_saved_command)
        menu.addAction(delete_action)
        
        menu.exec(self.saved_commands_list.mapToGlobal(position))
    
    def execute_saved_command_from_menu(self):
        """Execute saved command from context menu."""
        current_item = self.saved_commands_list.currentItem()
        if current_item:
            self.execute_saved_command(current_item)
    
    def edit_saved_command(self):
        """Edit the selected saved command."""
        current_item = self.saved_commands_list.currentItem()
        if not current_item:
            return
        
        cmd_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not cmd_data:
            return
        
        name, ok = QInputDialog.getText(self, "Edit Command", "Command name:", text=cmd_data['name'])
        if not ok:
            return
        
        command, ok = QInputDialog.getText(self, "Edit Command", "Command:", text=cmd_data['command'])
        if not ok:
            return
        
        # Update the command data
        cmd_data['name'] = name.strip()
        cmd_data['command'] = command.strip()
        
        # Update in saved commands
        for category_commands in self.saved_commands.values():
            for cmd in category_commands:
                if cmd == cmd_data:
                    cmd['name'] = name.strip()
                    cmd['command'] = command.strip()
                    break
        
        self.save_saved_commands()
        self.refresh_commands_list()
    
    def delete_saved_command(self):
        """Delete the selected saved command."""
        current_item = self.saved_commands_list.currentItem()
        if not current_item:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Command",
            "Are you sure you want to delete this command?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            cmd_data = current_item.data(Qt.ItemDataRole.UserRole)
            
            # Remove from saved commands
            for category, commands in self.saved_commands.items():
                if cmd_data in commands:
                    commands.remove(cmd_data)
                    break
            
            self.save_saved_commands()
            self.refresh_commands_list()
    
    def filter_commands(self, category):
        """Filter saved commands by category."""
        self.refresh_commands_list()
