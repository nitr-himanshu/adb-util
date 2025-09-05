"""
Utils UI

Device utilities and system operations.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QTabWidget,
    QTextEdit, QLineEdit, QComboBox, QSpinBox,
    QProgressBar, QListWidget, QGroupBox,
    QCheckBox, QSlider, QMessageBox, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

from utils.logger import get_logger, log_device_operation


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
        
        # Create tabs for different utility categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.create_device_info_tab()
        self.create_app_management_tab()
        self.create_system_control_tab()
        self.create_network_tools_tab()
        self.create_performance_tab()
        self.create_backup_restore_tab()
    
    def create_device_info_tab(self):
        """Create device information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create splitter for two columns
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
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
        
        self.tab_widget.addTab(tab, "📱 Device Info")
    
    def create_app_management_tab(self):
        """Create application management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Package Filter:"))
        
        self.package_filter = QComboBox()
        self.package_filter.addItems(["All Packages", "User Apps", "System Apps", "Enabled Apps", "Disabled Apps"])
        controls_layout.addWidget(self.package_filter)
        
        controls_layout.addStretch()
        
        refresh_apps_btn = QPushButton("🔄 Refresh Apps")
        refresh_apps_btn.clicked.connect(self.refresh_app_list)
        controls_layout.addWidget(refresh_apps_btn)
        
        layout.addLayout(controls_layout)
        
        # App list and details
        app_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(app_splitter)
        
        # App list
        self.app_list = QTreeWidget()
        self.app_list.setHeaderLabels(["App Name", "Package Name", "Version", "Status"])
        self.app_list.itemClicked.connect(self.show_app_details)
        
        # Sample data
        self.populate_sample_apps()
        
        app_splitter.addWidget(self.app_list)
        
        # App details and actions
        details_panel = QFrame()
        details_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_panel)
        
        # App details
        details_group = QGroupBox("📋 App Details")
        details_group_layout = QVBoxLayout(details_group)
        
        self.app_details = QTextEdit()
        self.app_details.setMaximumHeight(150)
        self.app_details.setReadOnly(True)
        details_group_layout.addWidget(self.app_details)
        
        details_layout.addWidget(details_group)
        
        # App actions
        actions_group = QGroupBox("⚡ Actions")
        actions_layout = QGridLayout(actions_group)
        
        actions = [
            ("Launch App", "🚀", self.launch_app),
            ("Force Stop", "⏹️", self.force_stop_app),
            ("Clear Cache", "🗑️", self.clear_app_cache),
            ("Clear Data", "💥", self.clear_app_data),
            ("Uninstall", "❌", self.uninstall_app),
            ("Backup APK", "📦", self.backup_apk),
            ("Enable App", "✅", self.enable_app),
            ("Disable App", "❌", self.disable_app)
        ]
        
        for i, (name, icon, callback) in enumerate(actions):
            btn = QPushButton(f"{icon} {name}")
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn, i // 2, i % 2)
        
        details_layout.addWidget(actions_group)
        details_layout.addStretch()
        
        app_splitter.addWidget(details_panel)
        app_splitter.setSizes([500, 300])
        
        self.tab_widget.addTab(tab, "📱 App Management")
    
    def create_system_control_tab(self):
        """Create system control tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Actions
        actions_group = QGroupBox("⚡ System Actions")
        actions_layout = QGridLayout(actions_group)
        
        system_actions = [
            ("Reboot Device", "🔄", self.reboot_device),
            ("Reboot to Recovery", "🛠️", self.reboot_recovery),
            ("Reboot to Bootloader", "⚙️", self.reboot_bootloader),
            ("Power Off", "⏻", self.power_off),
            ("Take Screenshot", "📸", self.take_screenshot),
            ("Record Screen", "🎥", self.record_screen),
            ("Lock Screen", "🔒", self.lock_screen),
            ("Unlock Screen", "🔓", self.unlock_screen),
            ("Wake Screen", "💡", self.wake_screen),
            ("Enable Airplane Mode", "✈️", self.toggle_airplane_mode),
            ("Enable WiFi", "📶", self.toggle_wifi),
            ("Enable Mobile Data", "📱", self.toggle_mobile_data)
        ]
        
        for i, (name, icon, callback) in enumerate(system_actions):
            btn = QPushButton(f"{icon} {name}")
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn, i // 3, i % 3)
        
        layout.addWidget(actions_group)
        
        # Input Methods
        input_group = QGroupBox("⌨️ Input Methods")
        input_layout = QVBoxLayout(input_group)
        
        # Text input
        text_input_layout = QHBoxLayout()
        text_input_layout.addWidget(QLabel("Send Text:"))
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text to send to device...")
        text_input_layout.addWidget(self.text_input)
        
        send_text_btn = QPushButton("📝 Send")
        send_text_btn.clicked.connect(self.send_text)
        text_input_layout.addWidget(send_text_btn)
        
        input_layout.addLayout(text_input_layout)
        
        # Key events
        key_layout = QHBoxLayout()
        
        key_buttons = [
            ("Home", "🏠", "HOME"),
            ("Back", "⬅️", "BACK"),
            ("Menu", "☰", "MENU"),
            ("Recent", "⏮️", "APP_SWITCH"),
            ("Power", "⏻", "POWER"),
            ("Volume Up", "🔊", "VOLUME_UP"),
            ("Volume Down", "🔉", "VOLUME_DOWN"),
            ("Camera", "📷", "CAMERA")
        ]
        
        for name, icon, keycode in key_buttons:
            btn = QPushButton(f"{icon}")
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked, k=keycode: self.send_keyevent(k))
            key_layout.addWidget(btn)
        
        input_layout.addLayout(key_layout)
        
        layout.addWidget(input_group)
        
        # System Settings
        settings_group = QGroupBox("⚙️ System Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Brightness control
        settings_layout.addWidget(QLabel("Brightness:"), 0, 0)
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 255)
        self.brightness_slider.setValue(128)
        self.brightness_slider.valueChanged.connect(self.set_brightness)
        settings_layout.addWidget(self.brightness_slider, 0, 1)
        
        self.brightness_label = QLabel("50%")
        settings_layout.addWidget(self.brightness_label, 0, 2)
        
        # Volume control
        settings_layout.addWidget(QLabel("Volume:"), 1, 0)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 15)
        self.volume_slider.setValue(10)
        self.volume_slider.valueChanged.connect(self.set_volume)
        settings_layout.addWidget(self.volume_slider, 1, 1)
        
        self.volume_label = QLabel("67%")
        settings_layout.addWidget(self.volume_label, 1, 2)
        
        layout.addWidget(settings_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "⚙️ System Control")
    
    def create_network_tools_tab(self):
        """Create network tools tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Network Status
        status_group = QGroupBox("📶 Network Status")
        status_layout = QGridLayout(status_group)
        
        # TODO: Add network status widgets
        status_layout.addWidget(QLabel("Coming soon..."), 0, 0)
        
        layout.addWidget(status_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🌐 Network Tools")
    
    def create_performance_tab(self):
        """Create performance monitoring tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performance Metrics
        metrics_group = QGroupBox("📊 Performance Metrics")
        metrics_layout = QGridLayout(metrics_group)
        
        # TODO: Add performance monitoring widgets
        metrics_layout.addWidget(QLabel("Coming soon..."), 0, 0)
        
        layout.addWidget(metrics_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "📊 Performance")
    
    def create_backup_restore_tab(self):
        """Create backup and restore tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Backup Options
        backup_group = QGroupBox("💾 Backup Options")
        backup_layout = QVBoxLayout(backup_group)
        
        # TODO: Add backup/restore widgets
        backup_layout.addWidget(QLabel("Coming soon..."))
        
        layout.addWidget(backup_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "💾 Backup & Restore")
    
    def populate_sample_apps(self):
        """Populate app list with sample data."""
        sample_apps = [
            ("Chrome", "com.android.chrome", "91.0.4472.120", "Enabled"),
            ("Gmail", "com.google.android.gm", "2021.06.06.384", "Enabled"),
            ("Settings", "com.android.settings", "11", "System"),
            ("Calculator", "com.android.calculator2", "11", "Enabled"),
            ("WhatsApp", "com.whatsapp", "2.21.12.17", "Enabled"),
            ("Instagram", "com.instagram.android", "192.0.0.34.122", "Enabled"),
            ("System UI", "com.android.systemui", "11", "System"),
            ("Camera", "com.android.camera2", "11", "Enabled")
        ]
        
        for app_name, package, version, status in sample_apps:
            item = QTreeWidgetItem([app_name, package, version, status])
            self.app_list.addTopLevelItem(item)
    
    def show_app_details(self, item):
        """Show details for selected app."""
        app_name = item.text(0)
        package = item.text(1)
        version = item.text(2)
        status = item.text(3)
        
        details = f"""App Name: {app_name}
Package Name: {package}
Version: {version}
Status: {status}
Install Location: Internal Storage
Target SDK: 30
Min SDK: 21
Permissions: Camera, Storage, Location, Contacts
Data Size: 125 MB
Cache Size: 45 MB
Last Updated: 2021-06-15"""
        
        self.app_details.setText(details)
    
    # Action methods (placeholders for actual implementation)
    def refresh_all_info(self):
        """Refresh all device information."""
        QMessageBox.information(self, "Refresh", "Device information refreshed!")
    
    def refresh_app_list(self):
        """Refresh application list."""
        QMessageBox.information(self, "Refresh Apps", "Application list refreshed!")
    
    def launch_app(self):
        """Launch selected app."""
        QMessageBox.information(self, "Launch App", "App launched!")
    
    def force_stop_app(self):
        """Force stop selected app."""
        QMessageBox.information(self, "Force Stop", "App force stopped!")
    
    def clear_app_cache(self):
        """Clear app cache."""
        QMessageBox.information(self, "Clear Cache", "App cache cleared!")
    
    def clear_app_data(self):
        """Clear app data."""
        reply = QMessageBox.question(
            self, 
            "Clear Data", 
            "This will delete all app data. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Clear Data", "App data cleared!")
    
    def uninstall_app(self):
        """Uninstall selected app."""
        reply = QMessageBox.question(
            self, 
            "Uninstall", 
            "Are you sure you want to uninstall this app?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Uninstall", "App uninstalled!")
    
    def backup_apk(self):
        """Backup APK file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save APK", 
            "app.apk",
            "APK Files (*.apk);;All Files (*)"
        )
        if filename:
            QMessageBox.information(self, "Backup APK", f"APK saved to {filename}")
    
    def enable_app(self):
        """Enable selected app."""
        QMessageBox.information(self, "Enable App", "App enabled!")
    
    def disable_app(self):
        """Disable selected app."""
        QMessageBox.information(self, "Disable App", "App disabled!")
    
    def reboot_device(self):
        """Reboot device."""
        self.logger.warning(f"User initiated device reboot for {self.device_id}")
        reply = QMessageBox.question(
            self, 
            "Reboot", 
            "Are you sure you want to reboot the device?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            log_device_operation(self.device_id, "reboot", "User confirmed reboot")
            QMessageBox.information(self, "Reboot", "Device rebooting...")
        else:
            self.logger.info(f"Device reboot cancelled by user for {self.device_id}")
    
    def reboot_recovery(self):
        """Reboot to recovery mode."""
        self.logger.warning(f"User initiated recovery mode reboot for {self.device_id}")
        log_device_operation(self.device_id, "reboot_recovery", "Entering recovery mode")
        QMessageBox.information(self, "Recovery", "Rebooting to recovery mode...")
    
    def reboot_bootloader(self):
        """Reboot to bootloader."""
        QMessageBox.information(self, "Bootloader", "Rebooting to bootloader...")
    
    def power_off(self):
        """Power off device."""
        QMessageBox.information(self, "Power Off", "Device powering off...")
    
    def take_screenshot(self):
        """Take device screenshot."""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Screenshot", 
            "screenshot.png",
            "PNG Files (*.png);;All Files (*)"
        )
        if filename:
            QMessageBox.information(self, "Screenshot", f"Screenshot saved to {filename}")
    
    def record_screen(self):
        """Record device screen."""
        QMessageBox.information(self, "Screen Record", "Screen recording started!")
    
    def lock_screen(self):
        """Lock device screen."""
        QMessageBox.information(self, "Lock Screen", "Screen locked!")
    
    def unlock_screen(self):
        """Unlock device screen."""
        QMessageBox.information(self, "Unlock Screen", "Screen unlocked!")
    
    def wake_screen(self):
        """Wake device screen."""
        QMessageBox.information(self, "Wake Screen", "Screen awakened!")
    
    def toggle_airplane_mode(self):
        """Toggle airplane mode."""
        QMessageBox.information(self, "Airplane Mode", "Airplane mode toggled!")
    
    def toggle_wifi(self):
        """Toggle WiFi."""
        QMessageBox.information(self, "WiFi", "WiFi toggled!")
    
    def toggle_mobile_data(self):
        """Toggle mobile data."""
        QMessageBox.information(self, "Mobile Data", "Mobile data toggled!")
    
    def send_text(self):
        """Send text to device."""
        text = self.text_input.text()
        if text:
            QMessageBox.information(self, "Send Text", f"Text sent: {text}")
            self.text_input.clear()
    
    def send_keyevent(self, keycode):
        """Send key event to device."""
        QMessageBox.information(self, "Key Event", f"Key sent: {keycode}")
    
    def set_brightness(self, value):
        """Set device brightness."""
        percentage = int((value / 255) * 100)
        self.brightness_label.setText(f"{percentage}%")
    
    def set_volume(self, value):
        """Set device volume."""
        percentage = int((value / 15) * 100)
        self.volume_label.setText(f"{percentage}%")
