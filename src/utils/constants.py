"""
Constants

Application-wide constants and configuration values.
"""

from pathlib import Path

# Application Information
APP_NAME = "ADB-UTIL"
APP_VERSION = "1.0.0"
APP_AUTHOR = "ADB-UTIL Team"

# File Extensions
SUPPORTED_TEXT_EXTENSIONS = ['.txt', '.json', '.xml', '.log', '.conf', '.ini', '.md']
SUPPORTED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']

# ADB Commands
ADB_DEVICES_COMMAND = "adb devices"
ADB_SHELL_COMMAND = "adb -s {device_id} shell"
ADB_LOGCAT_COMMAND = "adb -s {device_id} logcat"
ADB_PUSH_COMMAND = "adb -s {device_id} push {local_path} {device_path}"
ADB_PULL_COMMAND = "adb -s {device_id} pull {device_path} {local_path}"
ADB_GETPROP_COMMAND = "adb -s {device_id} shell getprop"

# Logcat specific commands
ADB_LOGCAT_CLEAR = "adb -s {device_id} logcat -c"
ADB_LOGCAT_DUMP = "adb -s {device_id} logcat -d"

# Logcat formats
LOGCAT_FORMATS = ["brief", "process", "tag", "raw", "time", "threadtime", "long"]

# Logcat buffers
LOGCAT_BUFFERS = ["main", "system", "radio", "events", "crash", "all"]

# Device States
DEVICE_STATE_DEVICE = "device"
DEVICE_STATE_OFFLINE = "offline"
DEVICE_STATE_UNAUTHORIZED = "unauthorized"
DEVICE_STATE_UNKNOWN = "unknown"

# Connection Types
CONNECTION_USB = "usb"
CONNECTION_TCPIP = "tcpip"

# UI Constants
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Tab Modes
TAB_MODES = {
    'file_manager': 'File Manager',
    'terminal': 'Terminal', 
    'logging': 'Logging'
}

# Log Levels
LOG_LEVELS = ['V', 'D', 'I', 'W', 'E', 'F']  # Verbose, Debug, Info, Warning, Error, Fatal

# Default Paths
DEFAULT_CONFIG_DIR = Path.home() / ".adb-util"
DEFAULT_DOWNLOADS_DIR = Path.home() / "Downloads" / "adb-util"

# Timeouts (seconds)
COMMAND_TIMEOUT = 30
DEVICE_DISCOVERY_TIMEOUT = 10
FILE_TRANSFER_TIMEOUT = 300
DEVICE_MONITORING_INTERVAL = 5

# Buffer Sizes
MAX_LOG_BUFFER_SIZE = 10000
FILE_TRANSFER_CHUNK_SIZE = 8192

# Logging Configuration
DEFAULT_LOG_DIR = Path.home() / ".adb-util" / "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
DEFAULT_FILE_LOGGING = False  # File logging disabled by default
