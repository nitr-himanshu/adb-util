"""
Utils UI

Device utilities and system operations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QGroupBox,
    QProgressBar, QSplitter
)
from PyQt6.QtCore import Qt
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
        
        # Add device info directly without tabs
        self.create_device_info_content(layout)
    
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
        pass
