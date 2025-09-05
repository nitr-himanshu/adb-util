"""
Utils UI

Device utilities and system operations.
"""

import subprocess
import socket
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QGroupBox,
    QProgressBar, QSplitter, QLineEdit, QMessageBox,
    QTextEdit, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from utils.logger import get_logger


class Utils(QWidget):
    """Utils widget for device utilities and system operations."""
    
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.logger = get_logger(__name__)
        
        self.logger.info(f"Initializing device utils for device: {device_id}")
        self.init_ui()
        self.logger.info("Device utils initialization complete")
    
    def init_ui(self):
        """Initialize the utils UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        utils_label = QLabel(f"🛠️ Device Utils - {self.device_id}")
        utils_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(utils_label)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh All")
        refresh_btn.clicked.connect(self.refresh_all_info)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Add port forwarding section
        self.create_port_forwarding_section(layout)
        
        # Add device info directly without tabs
        self.create_device_info_content(layout)
    
    def create_port_forwarding_section(self, parent_layout):
        """Create port forwarding section."""
        port_group = QGroupBox("🔗 Port Forwarding")
        port_layout = QVBoxLayout(port_group)
        
        # Instructions
        instructions = QLabel("Forward TCP ports between your computer and the Android device")
        instructions.setStyleSheet("color: #666; font-style: italic;")
        port_layout.addWidget(instructions)
        
        # Port forwarding controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Port:"))
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("e.g., 8080")
        self.port_input.setMaximumWidth(100)
        controls_layout.addWidget(self.port_input)
        
        self.forward_btn = QPushButton("🔗 Forward Port")
        self.forward_btn.clicked.connect(self.setup_port_forward)
        controls_layout.addWidget(self.forward_btn)
        
        self.remove_forward_btn = QPushButton("❌ Remove Forward")
        self.remove_forward_btn.clicked.connect(self.remove_port_forward)
        controls_layout.addWidget(self.remove_forward_btn)
        
        controls_layout.addStretch()
        
        port_layout.addLayout(controls_layout)
        
        # Active forwards list
        self.forwards_text = QTextEdit()
        self.forwards_text.setMaximumHeight(100)
        self.forwards_text.setReadOnly(True)
        self.forwards_text.setPlaceholderText("No active port forwards")
        port_layout.addWidget(QLabel("Active Port Forwards:"))
        port_layout.addWidget(self.forwards_text)
        
        # Add refresh forwards button
        refresh_forwards_layout = QHBoxLayout()
        refresh_forwards_layout.addStretch()
        
        refresh_forwards_btn = QPushButton("🔄 Refresh Forwards")
        refresh_forwards_btn.clicked.connect(self.refresh_port_forwards)
        refresh_forwards_layout.addWidget(refresh_forwards_btn)
        
        port_layout.addLayout(refresh_forwards_layout)
        
        parent_layout.addWidget(port_group)
    
    def create_device_info_content(self, parent_layout):
        """Create device information content."""
        # Create splitter for two columns
        splitter = QSplitter(Qt.Orientation.Horizontal)
        parent_layout.addWidget(splitter)
        
        # Left column - System Properties
        left_panel = QFrame()
        left_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_panel)
        
        # System Properties Group
        sys_group = QGroupBox("📱 System Properties")
        sys_layout = QGridLayout(sys_group)
        
        properties = [
            ("Model:", "Unknown"),
            ("Android Version:", "Unknown"),
            ("API Level:", "Unknown"),
            ("Build Number:", "Unknown"),
            ("Serial Number:", "Unknown"),
            ("Manufacturer:", "Unknown"),
            ("Brand:", "Unknown"),
            ("Product:", "Unknown"),
            ("Device:", "Unknown"),
            ("Hardware:", "Unknown")
        ]
        
        self.property_labels = {}
        for i, (prop_name, default_value) in enumerate(properties):
            label = QLabel(prop_name)
            label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            sys_layout.addWidget(label, i, 0)
            
            value_label = QLabel(default_value)
            value_label.setStyleSheet("color: #0080ff;")
            sys_layout.addWidget(value_label, i, 1)
            
            self.property_labels[prop_name] = value_label
        
        left_layout.addWidget(sys_group)
        
        # Hardware Info Group
        hw_group = QGroupBox("🔧 Hardware Information")
        hw_layout = QGridLayout(hw_group)
        
        hw_info = [
            ("CPU Architecture:", "Unknown"),
            ("CPU Cores:", "Unknown"),
            ("RAM:", "Unknown"),
            ("Storage:", "Unknown"),
            ("Screen Resolution:", "Unknown"),
            ("Display Density:", "Unknown"),
            ("Battery Level:", "Unknown"),
            ("Charging Status:", "Unknown")
        ]
        
        self.hw_labels = {}
        for i, (hw_name, default_value) in enumerate(hw_info):
            label = QLabel(hw_name)
            label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            hw_layout.addWidget(label, i, 0)
            
            value_label = QLabel(default_value)
            value_label.setStyleSheet("color: #00ff00;")
            hw_layout.addWidget(value_label, i, 1)
            
            self.hw_labels[hw_name] = value_label
        
        left_layout.addWidget(hw_group)
        left_layout.addStretch()
        
        splitter.addWidget(left_panel)
        
        # Right column - System Status
        right_panel = QFrame()
        right_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_panel)
        
        # Storage Information
        storage_group = QGroupBox("💾 Storage Information")
        storage_layout = QVBoxLayout(storage_group)
        
        # Internal Storage
        internal_layout = QHBoxLayout()
        internal_layout.addWidget(QLabel("Internal Storage:"))
        
        self.internal_progress = QProgressBar()
        self.internal_progress.setValue(65)
        internal_layout.addWidget(self.internal_progress)
        
        self.internal_label = QLabel("65% (12.5GB / 19.2GB)")
        internal_layout.addWidget(self.internal_label)
        
        storage_layout.addLayout(internal_layout)
        
        # External Storage
        external_layout = QHBoxLayout()
        external_layout.addWidget(QLabel("External Storage:"))
        
        self.external_progress = QProgressBar()
        self.external_progress.setValue(30)
        external_layout.addWidget(self.external_progress)
        
        self.external_label = QLabel("30% (9.6GB / 32GB)")
        external_layout.addWidget(self.external_label)
        
        storage_layout.addLayout(external_layout)
        
        right_layout.addWidget(storage_group)
        
        # Memory Information
        memory_group = QGroupBox("🧠 Memory Information")
        memory_layout = QVBoxLayout(memory_group)
        
        # RAM Usage
        ram_layout = QHBoxLayout()
        ram_layout.addWidget(QLabel("RAM Usage:"))
        
        self.ram_progress = QProgressBar()
        self.ram_progress.setValue(78)
        ram_layout.addWidget(self.ram_progress)
        
        self.ram_label = QLabel("78% (3.1GB / 4GB)")
        ram_layout.addWidget(self.ram_label)
        
        memory_layout.addLayout(ram_layout)
        
        right_layout.addWidget(memory_group)
        
        # Network Information
        network_group = QGroupBox("🌐 Network Information")
        network_layout = QGridLayout(network_group)
        
        network_info = [
            ("WiFi Status:", "Connected"),
            ("SSID:", "MyNetwork"),
            ("IP Address:", "192.168.1.100"),
            ("MAC Address:", "AA:BB:CC:DD:EE:FF"),
            ("Mobile Data:", "Disabled"),
            ("Bluetooth:", "Enabled")
        ]
        
        self.network_labels = {}
        for i, (net_name, default_value) in enumerate(network_info):
            label = QLabel(net_name)
            label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            network_layout.addWidget(label, i, 0)
            
            value_label = QLabel(default_value)
            value_label.setStyleSheet("color: #ff8000;")
            network_layout.addWidget(value_label, i, 1)
            
            self.network_labels[net_name] = value_label
        
        right_layout.addWidget(network_group)
        right_layout.addStretch()
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 400])
    
    def refresh_all_info(self):
        """Refresh all device information."""
        # TODO: Implement actual device info refresh
        self.refresh_port_forwards()
    
    def setup_port_forward(self):
        """Set up port forwarding."""
        port_text = self.port_input.text().strip()
        
        if not port_text:
            # Ask user for port number
            port_text, ok = QInputDialog.getText(
                self, 
                "Port Forward", 
                "Enter port number to forward:",
                text="8080"
            )
            if not ok or not port_text.strip():
                return
            port_text = port_text.strip()
        
        try:
            port = int(port_text)
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
        except ValueError as e:
            QMessageBox.warning(
                self, 
                "Invalid Port", 
                f"Invalid port number: {port_text}\n{str(e)}"
            )
            return
        
        try:
            # Execute ADB forward command
            cmd = ["adb", "-s", self.device_id, "forward", f"tcp:{port}", f"tcp:{port}"]
            self.logger.info(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info(f"Port forward successful: {port}")
                QMessageBox.information(
                    self, 
                    "Port Forward Success", 
                    f"Successfully forwarded port {port}\n"
                    f"TCP:{port} -> TCP:{port}"
                )
                
                # Validate with connection test
                self.validate_port_forward(port)
                
                # Clear input and refresh list
                self.port_input.clear()
                self.refresh_port_forwards()
                
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.logger.error(f"Port forward failed: {error_msg}")
                QMessageBox.critical(
                    self, 
                    "Port Forward Failed", 
                    f"Failed to forward port {port}\n\nError: {error_msg}"
                )
                
        except subprocess.TimeoutExpired:
            QMessageBox.critical(
                self, 
                "Timeout", 
                "Port forward command timed out"
            )
        except FileNotFoundError:
            QMessageBox.critical(
                self, 
                "ADB Not Found", 
                "ADB command not found. Please ensure ADB is installed and in PATH."
            )
        except Exception as e:
            self.logger.error(f"Port forward error: {e}", exc_info=True)
            QMessageBox.critical(
                self, 
                "Error", 
                f"An error occurred: {str(e)}"
            )
    
    def remove_port_forward(self):
        """Remove port forwarding."""
        port_text, ok = QInputDialog.getText(
            self, 
            "Remove Port Forward", 
            "Enter port number to remove forwarding:",
            text=""
        )
        
        if not ok or not port_text.strip():
            return
        
        try:
            port = int(port_text.strip())
            if not (1 <= port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
        except ValueError as e:
            QMessageBox.warning(
                self, 
                "Invalid Port", 
                f"Invalid port number: {port_text}\n{str(e)}"
            )
            return
        
        try:
            # Execute ADB forward --remove command
            cmd = ["adb", "-s", self.device_id, "forward", "--remove", f"tcp:{port}"]
            self.logger.info(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                self.logger.info(f"Port forward removed: {port}")
                QMessageBox.information(
                    self, 
                    "Port Forward Removed", 
                    f"Successfully removed port forward for port {port}"
                )
                self.refresh_port_forwards()
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.logger.error(f"Remove port forward failed: {error_msg}")
                QMessageBox.critical(
                    self, 
                    "Remove Failed", 
                    f"Failed to remove port forward for port {port}\n\nError: {error_msg}"
                )
                
        except subprocess.TimeoutExpired:
            QMessageBox.critical(
                self, 
                "Timeout", 
                "Remove port forward command timed out"
            )
        except Exception as e:
            self.logger.error(f"Remove port forward error: {e}", exc_info=True)
            QMessageBox.critical(
                self, 
                "Error", 
                f"An error occurred: {str(e)}"
            )
    
    def refresh_port_forwards(self):
        """Refresh the list of active port forwards."""
        try:
            # Get list of active forwards
            cmd = ["adb", "-s", self.device_id, "forward", "--list"]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                forwards = result.stdout.strip()
                if forwards:
                    # Filter forwards for this device
                    device_forwards = []
                    for line in forwards.split('\n'):
                        if line.strip() and self.device_id in line:
                            device_forwards.append(line.strip())
                    
                    if device_forwards:
                        self.forwards_text.setText('\n'.join(device_forwards))
                    else:
                        self.forwards_text.setText("No active port forwards for this device")
                else:
                    self.forwards_text.setText("No active port forwards")
            else:
                self.forwards_text.setText("Failed to retrieve port forwards")
                
        except Exception as e:
            self.logger.error(f"Refresh port forwards error: {e}")
            self.forwards_text.setText(f"Error: {str(e)}")
    
    def validate_port_forward(self, port):
        """Validate port forwarding by testing connection."""
        try:
            # Test if we can connect to the forwarded port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                self.logger.info(f"Port {port} validation: Connection successful")
                QMessageBox.information(
                    self, 
                    "Validation Success", 
                    f"✅ Port {port} is accessible and responding"
                )
            else:
                self.logger.warning(f"Port {port} validation: No service responding")
                QMessageBox.information(
                    self, 
                    "Validation Complete", 
                    f"⚠️ Port {port} is forwarded but no service is responding\n"
                    f"This is normal if no service is running on port {port} on the device"
                )
                
        except Exception as e:
            self.logger.error(f"Port validation error: {e}")
            QMessageBox.information(
                self, 
                "Validation Note", 
                f"Port {port} forwarding setup complete\n"
                f"Note: Connection test failed, but forwarding may still be working"
            )
