"""
Terminal UI

Interactive ADB shell with command history and saved commands.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QSplitter, QListWidget,
    QLabel, QFrame, QTabWidget, QComboBox,
    QMessageBox, QInputDialog, QMenu
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QAction


class Terminal(QWidget):
    """Terminal widget for ADB shell commands."""
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.command_history = []
        self.history_index = -1
        self.init_ui()
    
    def init_ui(self):
        """Initialize the terminal UI."""
        layout = QHBoxLayout(self)
        
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
        splitter.setSizes([600, 300])
    
    def create_terminal_panel(self):
        """Create the main terminal panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Terminal header
        header_layout = QHBoxLayout()
        
        terminal_label = QLabel(f"💻 Terminal - {self.device_id}")
        terminal_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(terminal_label)
        
        header_layout.addStretch()
        
        # Terminal controls
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_terminal)
        header_layout.addWidget(clear_btn)
        
        save_session_btn = QPushButton("💾 Save Session")
        save_session_btn.clicked.connect(self.save_session)
        header_layout.addWidget(save_session_btn)
        
        layout.addLayout(header_layout)
        
        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setFont(QFont("Consolas", 10))
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }
        """)
        self.terminal_output.setReadOnly(True)
        layout.addWidget(self.terminal_output)
        
        # Command input area
        input_layout = QHBoxLayout()
        
        # Prompt label
        prompt_label = QLabel(f"{self.device_id}:/ $ ")
        prompt_label.setFont(QFont("Consolas", 10))
        prompt_label.setStyleSheet("color: #00ff00;")
        input_layout.addWidget(prompt_label)
        
        # Command input
        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Consolas", 10))
        self.command_input.returnPressed.connect(self.execute_command)
        self.command_input.keyPressEvent = self.handle_key_press
        input_layout.addWidget(self.command_input)
        
        # Execute button
        execute_btn = QPushButton("▶️ Execute")
        execute_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(execute_btn)
        
        layout.addLayout(input_layout)
        
        # Add welcome message
        self.add_terminal_output("ADB Terminal initialized", "system")
        self.add_terminal_output(f"Connected to device: {self.device_id}", "system")
        self.add_terminal_output("Type 'help' for available commands", "system")
        
        return panel
    
    def create_saved_commands_panel(self):
        """Create the saved commands panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Header
        header_layout = QHBoxLayout()
        
        commands_label = QLabel("💾 Saved Commands")
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
        self.category_combo.addItems([
            "All", "File Operations", "System Info", 
            "Network", "Package Management", "Custom"
        ])
        self.category_combo.currentTextChanged.connect(self.filter_commands)
        category_layout.addWidget(self.category_combo)
        
        layout.addLayout(category_layout)
        
        # Saved commands list
        self.saved_commands_list = QListWidget()
        self.saved_commands_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.saved_commands_list.customContextMenuRequested.connect(self.show_command_context_menu)
        self.saved_commands_list.itemDoubleClicked.connect(self.execute_saved_command)
        
        # Add some sample commands
        self.add_sample_commands()
        
        layout.addWidget(self.saved_commands_list)
        
        # Command details
        details_label = QLabel("Command Details:")
        details_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(details_label)
        
        self.command_details = QTextEdit()
        self.command_details.setMaximumHeight(100)
        self.command_details.setReadOnly(True)
        layout.addWidget(self.command_details)
        
        # Quick execute button
        quick_execute_btn = QPushButton("⚡ Quick Execute")
        quick_execute_btn.clicked.connect(self.execute_saved_command)
        layout.addWidget(quick_execute_btn)
        
        return panel
    
    def add_sample_commands(self):
        """Add sample saved commands."""
        sample_commands = [
            ("List Files", "ls -la", "File Operations"),
            ("Current Directory", "pwd", "File Operations"),
            ("System Info", "getprop ro.build.version.release", "System Info"),
            ("Device Model", "getprop ro.product.model", "System Info"),
            ("IP Address", "ip addr show wlan0", "Network"),
            ("WiFi Status", "dumpsys wifi", "Network"),
            ("Installed Packages", "pm list packages", "Package Management"),
            ("Running Processes", "ps", "System Info")
        ]
        
        for name, command, category in sample_commands:
            item_text = f"[{category}] {name}: {command}"
            self.saved_commands_list.addItem(item_text)
    
    def handle_key_press(self, event):
        """Handle key press events for command input."""
        if event.key() == Qt.Key.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down:
            self.navigate_history(1)
        else:
            # Call the original keyPressEvent
            QLineEdit.keyPressEvent(self.command_input, event)
    
    def navigate_history(self, direction):
        """Navigate through command history."""
        if not self.command_history:
            return
        
        self.history_index += direction
        
        if self.history_index < 0:
            self.history_index = 0
        elif self.history_index >= len(self.command_history):
            self.history_index = len(self.command_history) - 1
        
        if 0 <= self.history_index < len(self.command_history):
            self.command_input.setText(self.command_history[self.history_index])
    
    def execute_command(self):
        """Execute the entered command."""
        command = self.command_input.text().strip()
        if not command:
            return
        
        # Add to history
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Show command in terminal
        self.add_terminal_output(f"{self.device_id}:/ $ {command}", "input")
        
        # Clear input
        self.command_input.clear()
        
        # Simulate command execution (TODO: implement actual execution)
        self.simulate_command_execution(command)
    
    def simulate_command_execution(self, command):
        """Simulate command execution with mock responses."""
        # Mock responses for common commands
        responses = {
            "ls": "Documents\nPictures\nMusic\nVideos\nDownload",
            "pwd": "/sdcard",
            "help": "Available commands: ls, pwd, ps, getprop, pm, dumpsys, ip",
            "ps": "PID   PPID  NAME\n1     0     init\n2     0     kthreadd\n1234  1     com.android.systemui",
            "getprop ro.build.version.release": "11",
            "getprop ro.product.model": "SDK built for x86_64"
        }
        
        # Find matching response
        response = None
        for cmd_pattern, cmd_response in responses.items():
            if command.startswith(cmd_pattern):
                response = cmd_response
                break
        
        if response is None:
            if command.startswith("getprop"):
                response = "Property not found"
            else:
                response = f"Command '{command}' not found or not implemented in mock mode"
        
        # Simulate delay
        QTimer.singleShot(500, lambda: self.add_terminal_output(response, "output"))
    
    def add_terminal_output(self, text, output_type="output"):
        """Add text to terminal output."""
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if output_type == "input":
            self.terminal_output.setTextColor(Qt.GlobalColor.yellow)
        elif output_type == "system":
            self.terminal_output.setTextColor(Qt.GlobalColor.cyan)
        elif output_type == "error":
            self.terminal_output.setTextColor(Qt.GlobalColor.red)
        else:
            self.terminal_output.setTextColor(Qt.GlobalColor.white)
        
        self.terminal_output.append(text)
        
        # Auto-scroll to bottom
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.terminal_output.setTextCursor(cursor)
    
    def clear_terminal(self):
        """Clear the terminal output."""
        self.terminal_output.clear()
        self.add_terminal_output("Terminal cleared", "system")
    
    def save_session(self):
        """Save the current terminal session."""
        content = self.terminal_output.toPlainText()
        # TODO: Implement session saving
        QMessageBox.information(self, "Save Session", "Session saved successfully!")
    
    def add_saved_command(self):
        """Add a new saved command."""
        name, ok = QInputDialog.getText(self, "Add Command", "Command name:")
        if not ok or not name:
            return
        
        command, ok = QInputDialog.getText(self, "Add Command", "Command:")
        if not ok or not command:
            return
        
        category = self.category_combo.currentText()
        if category == "All":
            category = "Custom"
        
        item_text = f"[{category}] {name}: {command}"
        self.saved_commands_list.addItem(item_text)
    
    def execute_saved_command(self):
        """Execute the selected saved command."""
        current_item = self.saved_commands_list.currentItem()
        if not current_item:
            return
        
        # Extract command from item text
        item_text = current_item.text()
        # Format: [Category] Name: command
        command = item_text.split(": ", 1)[-1]
        
        self.command_input.setText(command)
        self.execute_command()
    
    def show_command_context_menu(self, position):
        """Show context menu for saved commands."""
        menu = QMenu(self)
        
        execute_action = QAction("Execute", self)
        execute_action.triggered.connect(self.execute_saved_command)
        menu.addAction(execute_action)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self.edit_saved_command)
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_saved_command)
        menu.addAction(delete_action)
        
        menu.exec(self.saved_commands_list.mapToGlobal(position))
    
    def edit_saved_command(self):
        """Edit the selected saved command."""
        # TODO: Implement command editing
        QMessageBox.information(self, "Edit Command", "Edit command functionality not yet implemented")
    
    def delete_saved_command(self):
        """Delete the selected saved command."""
        current_row = self.saved_commands_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, 
                "Delete Command", 
                "Are you sure you want to delete this command?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.saved_commands_list.takeItem(current_row)
    
    def filter_commands(self, category):
        """Filter saved commands by category."""
        # TODO: Implement command filtering
        pass
