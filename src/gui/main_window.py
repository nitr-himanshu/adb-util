"""
Main Application Window

Main window class that contains the tab management system and overall application layout.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QStatusBar, QLabel, 
    QPushButton, QListWidget, QGridLayout, QFrame,
    QMessageBox, QSplitter, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QAction

from adb.device_manager import DeviceManager
from models.device import Device
from utils.logger import get_logger
from utils.constants import TAB_MODES
from utils.device_utils import device_utils
from utils.theme_manager import theme_manager


class DeviceDiscoveryWorker(QThread):
    """Worker thread for device discovery."""
    
    devices_discovered = pyqtSignal(list)
    adb_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        self.logger = get_logger(__name__)
    
    def run(self):
        """Run device discovery in thread."""
        try:
            # Use device utils for discovery
            devices = device_utils.discover_devices_sync()
            
            # Check ADB availability
            adb_available = device_utils.is_adb_available()
            self.adb_status_changed.emit(adb_available)
            
            self.devices_discovered.emit(devices)
            
        except Exception as e:
            self.logger.error(f"Device discovery failed: {e}")
            self.error_occurred.emit(str(e))
            self.devices_discovered.emit([])


class MainWindow(QMainWindow):
    """Main application window with tab management."""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.tab_widget = None
        self.device_list = None
        self.status_label = None
        self.device_count_label = None
        self.adb_status_label = None
        
        # Device management
        self.device_manager = DeviceManager()
        self.devices = []
        self.current_device = None
        self.discovery_worker = None
        
        # Timer for periodic device refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_devices)
        
        # Initialize theme manager
        self.init_theme_manager()
        
        self.logger.info("Initializing main window...")
        self.init_ui()
        self.init_device_discovery()
        self.logger.info("Main window initialization complete")
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("ADB-UTIL - Android Debug Bridge Utility")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create device panel (left side)
        device_panel = self.create_device_panel()
        splitter.addWidget(device_panel)
        
        # Create main content area (right side)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        splitter.addWidget(self.tab_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Show home tab by default
        self.show_home_tab()
    
    def create_device_panel(self):
        """Create the device selection panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumWidth(350)
        
        layout = QVBoxLayout(panel)
        
        # Title
        title_label = QLabel("Connected Devices")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Device list
        self.device_list = QListWidget()
        self.device_list.itemClicked.connect(self.on_device_selected)
        layout.addWidget(self.device_list)
        
        # Device actions
        actions_label = QLabel("Device Actions")
        actions_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(actions_label)
        
        # Action buttons in grid
        actions_layout = QGridLayout()
        
        file_manager_btn = QPushButton("📁 File Manager")
        file_manager_btn.clicked.connect(lambda: self.open_device_tab("file_manager"))
        actions_layout.addWidget(file_manager_btn, 0, 0)
        
        terminal_btn = QPushButton("💻 Terminal")
        terminal_btn.clicked.connect(lambda: self.open_device_tab("terminal"))
        actions_layout.addWidget(terminal_btn, 0, 1)
        
        logging_btn = QPushButton("📊 Logging")
        logging_btn.clicked.connect(lambda: self.open_device_tab("logging"))
        actions_layout.addWidget(logging_btn, 1, 0)
        
        layout.addLayout(actions_layout)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_connection_action = QAction("&New Connection", self)
        new_connection_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_connection_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        preferences_action = QAction("&Preferences", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(preferences_action)
        
        tools_menu.addSeparator()
        
        # Theme submenu
        theme_menu = tools_menu.addMenu("&Theme")
        
        light_theme_action = QAction("☀️ &Light Mode", self)
        light_theme_action.setShortcut("Ctrl+L")
        light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("🌙 &Dark Mode", self)
        dark_theme_action.setShortcut("Ctrl+D")
        dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        theme_menu.addSeparator()
        
        toggle_theme_action = QAction("🔄 &Toggle Theme", self)
        toggle_theme_action.setShortcut("Ctrl+T")
        toggle_theme_action.triggered.connect(self.toggle_theme)
        theme_menu.addAction(toggle_theme_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """Create the status bar."""
        status_bar = self.statusBar()
        
        self.status_label = QLabel("Ready")
        status_bar.addWidget(self.status_label)
        
        # Add stretch to push right-side widgets to the right
        status_bar.addWidget(QLabel(), 1)  # Stretch widget
        
        # Theme toggle button
        current_theme = theme_manager.get_current_theme()
        theme_icon = "🌙" if current_theme == "dark" else "☀️"
        theme_text = "Dark Mode" if current_theme == "light" else "Light Mode"
        
        self.theme_toggle_btn = QPushButton(f"{theme_icon} {theme_text}")
        self.theme_toggle_btn.setToolTip(f"Switch to {theme_text.lower()} (Ctrl+T)")
        self.theme_toggle_btn.setMaximumSize(120, 25)
        self.theme_toggle_btn.setFont(QFont("Arial", 8))
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        
        # Style the button based on current theme
        self.update_theme_button_style()
        
        status_bar.addPermanentWidget(self.theme_toggle_btn)
        
        # Device count
        self.device_count_label = QLabel("Devices: 0")
        status_bar.addPermanentWidget(self.device_count_label)
        
        # ADB status
        self.adb_status_label = QLabel("ADB: Checking...")
        status_bar.addPermanentWidget(self.adb_status_label)
    
    def show_home_tab(self):
        """Show the home/welcome tab."""
        home_widget = self.create_home_widget()
        self.tab_widget.addTab(home_widget, "🏠 Home")
    
    def create_home_widget(self):
        """Create the home/welcome widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Welcome message
        welcome_label = QLabel("Welcome to ADB-UTIL")
        welcome_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome_label)
        
        subtitle_label = QLabel("Android Debug Bridge Utility")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setObjectName("subtitle_label")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(30)
        
        # Quick start instructions
        instructions_label = QLabel("""
        Getting Started:
        
        1. Select a device from the left panel
        2. Choose an operation mode:
           📁 File Manager - Transfer files between device and computer
           💻 Terminal - Execute ADB commands
           📊 Logging - View real-time logcat output
        
        3. Click the mode button to open a new tab
        """)
        instructions_label.setFont(QFont("Arial", 12))
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions_label.setObjectName("instructions_label")
        layout.addWidget(instructions_label)
        
        return widget
    
    def close_tab(self, index):
        """Close a tab."""
        if index > 0:  # Don't close the home tab
            tab_name = self.tab_widget.tabText(index)
            self.logger.info(f"Closing tab: {tab_name}")
            self.tab_widget.removeTab(index)
        else:
            self.logger.debug("Attempted to close home tab - ignored")
    
    def refresh_devices(self):
        """Refresh the device list."""
        self.logger.info("Refreshing device list...")
        self.status_label.setText("Refreshing devices...")
        
        # Stop any existing discovery
        if self.discovery_worker and self.discovery_worker.isRunning():
            self.discovery_worker.terminate()
            self.discovery_worker.wait()
        
        # Start new discovery worker
        self.discovery_worker = DeviceDiscoveryWorker(self.device_manager)
        self.discovery_worker.devices_discovered.connect(self.on_devices_discovered)
        self.discovery_worker.adb_status_changed.connect(self.on_adb_status_changed)
        self.discovery_worker.error_occurred.connect(self.on_discovery_error)
        self.discovery_worker.start()
    
    def on_devices_discovered(self, devices):
        """Handle devices discovered signal."""
        self.devices = devices
        self.update_device_list(devices)
        
        connected_count = len([d for d in devices if d.is_online])
        self.device_count_label.setText(f"Devices: {len(devices)} ({connected_count} online)")
        self.status_label.setText(f"Found {len(devices)} devices, {connected_count} online")
        
        self.logger.info(f"Device discovery completed: {len(devices)} devices found")
    
    def on_adb_status_changed(self, available):
        """Handle ADB status change."""
        if available:
            self.adb_status_label.setText("ADB: Available")
        else:
            self.adb_status_label.setText("ADB: Not Available")
            self.status_label.setText("ADB not found - Please install ADB and restart")
    
    def on_discovery_error(self, error_msg):
        """Handle discovery error."""
        self.logger.error(f"Device discovery error: {error_msg}")
        self.status_label.setText(f"Discovery failed: {error_msg}")
        self.update_device_list([])
    
    def auto_refresh_devices(self):
        """Auto refresh devices periodically."""
        self.refresh_devices()
    
    def init_device_discovery(self):
        """Initialize device discovery."""
        # Initial device discovery
        self.refresh_devices()
        # Start periodic refresh (every 10 seconds)
        self.refresh_timer.start(10000)
    
    def update_device_list(self, devices):
        """Update the device list widget."""
        self.device_list.clear()
        
        if not devices:
            item = QListWidgetItem("No devices found")
            item.setData(Qt.ItemDataRole.UserRole, None)
            self.device_list.addItem(item)
            return
        
        for device in devices:
            # Create display text
            if device.is_online:
                icon = "📱"
                status = "Online"
            elif device.status == "unauthorized":
                icon = "🔒"
                status = "Unauthorized"
            elif device.status == "offline":
                icon = "📴"
                status = "Offline"
            else:
                icon = "❓"
                status = device.status.title()
            
            display_text = f"{icon} {device.display_name} - {status}"
            if device.connection_type == "tcpip":
                display_text += " (TCP/IP)"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, device)
            self.device_list.addItem(item)
    
    def on_device_selected(self, item):
        """Handle device selection."""
        device = item.data(Qt.ItemDataRole.UserRole)
        if device:
            self.current_device = device
            self.logger.info(f"Selected device: {device.display_name}")
            self.status_label.setText(f"Selected: {device.display_name}")
        else:
            self.current_device = None
    
    def open_device_tab(self, mode):
        """Open a device-specific tab."""
        if not self.current_device:
            QMessageBox.warning(
                self,
                "No Device Selected",
                "Please select a device from the device list first."
            )
            return
        
        if not self.current_device.is_online:
            QMessageBox.warning(
                self,
                "Device Not Online",
                f"Device {self.current_device.display_name} is not online.\n"
                f"Status: {self.current_device.status}"
            )
            return
        
        device_id = self.current_device.id
        tab_title = f"{TAB_MODES.get(mode, mode)} ({self.current_device.display_name})"
        
        self.logger.info(f"Opening {mode} tab for device: {device_id}")
        
        try:
            # Create appropriate widget based on mode
            if mode == "file_manager":
                from gui.file_manager import FileManager
                widget = FileManager(device_id)
            elif mode == "terminal":
                from gui.terminal import Terminal
                widget = Terminal(device_id)
            elif mode == "logging":
                from gui.logging import Logging
                widget = Logging(device_id)
            else:
                self.logger.warning(f"Unknown mode requested: {mode}")
                widget = QLabel(f"Mode '{mode}' not implemented yet")
            
            self.tab_widget.addTab(widget, tab_title)
            self.tab_widget.setCurrentWidget(widget)
            self.logger.info(f"Successfully created {mode} tab for device {device_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to create {mode} tab for device {device_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to create {mode} tab: {str(e)}")
    
    def show_about(self):
        """Show about dialog."""
        self.logger.debug("Showing about dialog")
        QMessageBox.about(
            self,
            "About ADB-UTIL",
            "ADB-UTIL v1.0.0\n\n"
            "A comprehensive Python-based desktop application\n"
            "for Android Debug Bridge (ADB) operations.\n\n"
            "Built with PyQt6"
        )
    
    def show_preferences(self):
        """Show preferences dialog."""
        self.logger.debug("Opening preferences dialog")
        try:
            from gui.preferences import PreferencesDialog
            preferences_dialog = PreferencesDialog(self)
            preferences_dialog.exec()
        except Exception as e:
            self.logger.error(f"Error opening preferences dialog: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open preferences: {e}")
    
    def init_theme_manager(self):
        """Initialize theme manager and load saved preferences."""
        try:
            # Load saved theme preference
            theme_manager.load_theme_preference()
            
            # Connect theme change signal
            theme_manager.theme_changed.connect(self.on_theme_changed)
            
            self.logger.info(f"Theme manager initialized with {theme_manager.get_current_theme()} theme")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize theme manager: {e}")
    
    def set_theme(self, theme_name: str):
        """Set the application theme."""
        try:
            theme_manager.set_theme(theme_name)
            theme_manager.save_theme_preference()
            self.logger.info(f"Theme changed to {theme_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to set theme to {theme_name}: {e}")
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        try:
            theme_manager.toggle_theme()
            theme_manager.save_theme_preference()
            
            # Update button text and style
            current_theme = theme_manager.get_current_theme()
            theme_icon = "🌙" if current_theme == "dark" else "☀️"
            theme_text = "Dark Mode" if current_theme == "light" else "Light Mode"
            
            self.theme_toggle_btn.setText(f"{theme_icon} {theme_text}")
            self.theme_toggle_btn.setToolTip(f"Switch to {theme_text.lower()} (Ctrl+T)")
            
            # Update button style
            self.update_theme_button_style()
            
            self.logger.info(f"Theme toggled to {current_theme}")
            
        except Exception as e:
            self.logger.error(f"Failed to toggle theme: {e}")
    
    def update_theme_button_style(self):
        """Update the theme toggle button style based on current theme."""
        try:
            current_theme = theme_manager.get_current_theme()
            
            if current_theme == "dark":
                self.theme_toggle_btn.setStyleSheet("""
                    QPushButton {
                        color: #FFD700; 
                        border: 1px solid #555; 
                        border-radius: 3px; 
                        padding: 4px 8px;
                        background-color: #2d2d2d;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #3d3d3d;
                        border-color: #777;
                    }
                """)
            else:
                self.theme_toggle_btn.setStyleSheet("""
                    QPushButton {
                        color: #4169E1; 
                        border: 1px solid #ccc; 
                        border-radius: 3px; 
                        padding: 4px 8px;
                        background-color: #f5f5f5;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #e5e5e5;
                        border-color: #999;
                    }
                """)
                
        except Exception as e:
            self.logger.error(f"Error updating theme button style: {e}")
    
    def on_theme_changed(self, theme_name: str):
        """Handle theme change event."""
        try:
            # Update theme toggle button
            if hasattr(self, 'theme_toggle_btn'):
                theme_icon = "🌙" if theme_name == "dark" else "☀️"
                theme_text = "Dark Mode" if theme_name == "light" else "Light Mode"
                
                self.theme_toggle_btn.setText(f"{theme_icon} {theme_text}")
                self.theme_toggle_btn.setToolTip(f"Switch to {theme_text.lower()} (Ctrl+T)")
                
                # Update button style
                self.update_theme_button_style()
            
            # Refresh theme for all open tabs with a small delay to ensure proper application
            def refresh_all_tabs():
                try:
                    for i in range(self.tab_widget.count()):
                        widget = self.tab_widget.widget(i)
                        if hasattr(widget, 'refresh_theme'):
                            # Add a small delay for each widget to prevent race conditions
                            QTimer.singleShot(50 * i, widget.refresh_theme)
                except Exception as e:
                    self.logger.error(f"Error refreshing tab themes: {e}")
            
            # Schedule the refresh after a small delay to ensure the theme is fully applied
            QTimer.singleShot(100, refresh_all_tabs)
            
            # Update status bar message
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Theme changed to {theme_name.title()} Mode")
                
            self.logger.debug(f"Theme change handled: {theme_name}")
            
        except Exception as e:
            self.logger.error(f"Error handling theme change: {e}")
