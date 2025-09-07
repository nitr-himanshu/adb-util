"""
Test to verify the immediate responsiveness fix for keyword search delay.
"""

import pytest
import sys
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

sys.path.insert(0, 'src')
from gui.logging import Logging


@pytest.fixture
def app():
    """Create QApplication for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def logging_widget(app):
    """Create a logging widget for testing."""
    with patch('gui.logging.LogcatHandler'):
        widget = Logging("test_device")
        return widget


def test_immediate_response_after_start_capture(logging_widget, qtbot):
    """Test that all UI elements respond immediately after clicking start capture."""
    
    qtbot.addWidget(logging_widget)
    
    # Record precise timing
    start_time = time.perf_counter()
    
    # Mock the worker to avoid actual ADB calls
    with patch.object(logging_widget, 'logcat_worker') as mock_worker:
        mock_worker.isRunning.return_value = True
        
        # Click start capture
        logging_widget.start_capture()
        
        # Measure time for immediate UI feedback
        immediate_time = time.perf_counter()
        ui_response_time = immediate_time - start_time
        
        # Process any pending events
        QApplication.processEvents()
        
        # Check that UI responds immediately (within 1ms)
        assert ui_response_time < 0.001, f"UI took {ui_response_time*1000:.1f}ms to respond, expected <1ms"
        
        # Verify immediate state changes
        assert logging_widget.is_capturing == True
        assert logging_widget.start_btn.text() == "⏸️ Pause"
        assert logging_widget.stop_btn.isEnabled() == True
        assert "Starting" in logging_widget.status_label.text()
        
        # Verify search functionality is immediately available
        assert logging_widget.search_input.isEnabled() == True
        assert logging_widget.highlight_input.isEnabled() == True
        
        # Test immediate search functionality
        search_start = time.perf_counter()
        logging_widget.search_input.setText("immediate_search")
        QApplication.processEvents()
        search_time = time.perf_counter() - search_start
        
        assert search_time < 0.01, f"Search took {search_time*1000:.1f}ms, expected <10ms"
        
        # Test immediate highlight functionality
        highlight_start = time.perf_counter()
        logging_widget.highlight_input.setText("immediate_highlight")
        result = logging_widget.add_highlight_keyword(show_dialogs=False)
        QApplication.processEvents()
        highlight_time = time.perf_counter() - highlight_start
        
        assert result == True, "Highlight keyword addition should succeed immediately"
        assert highlight_time < 0.01, f"Highlight took {highlight_time*1000:.1f}ms, expected <10ms"
        assert "immediate_highlight" in logging_widget.highlight_keywords
        
        # Verify total response time
        total_time = time.perf_counter() - start_time
        assert total_time < 0.05, f"Total operation took {total_time*1000:.1f}ms, expected <50ms"
        
        print(f"\\n✅ Performance Results:")
        print(f"   UI Response: {ui_response_time*1000:.2f}ms")
        print(f"   Search Time: {search_time*1000:.2f}ms") 
        print(f"   Highlight Time: {highlight_time*1000:.2f}ms")
        print(f"   Total Time: {total_time*1000:.2f}ms")


def test_no_blocking_operations(logging_widget, qtbot):
    """Test that no operations block the UI thread."""
    
    qtbot.addWidget(logging_widget)
    
    # Simulate rapid user interactions immediately after start capture
    with patch.object(logging_widget, 'logcat_worker') as mock_worker:
        mock_worker.isRunning.return_value = True
        
        start_time = time.perf_counter()
        
        # Start capture
        logging_widget.start_capture()
        
        # Immediately perform multiple operations without delays
        operations = []
        
        # Operation 1: Search
        op_start = time.perf_counter()
        logging_widget.search_input.setText("test1")
        QApplication.processEvents()
        operations.append(("Search", time.perf_counter() - op_start))
        
        # Operation 2: Add highlight
        op_start = time.perf_counter()
        logging_widget.highlight_input.setText("highlight1")
        logging_widget.add_highlight_keyword(show_dialogs=False)
        QApplication.processEvents()
        operations.append(("Highlight", time.perf_counter() - op_start))
        
        # Operation 3: Filter change
        op_start = time.perf_counter()
        logging_widget.level_checkboxes['D'].setChecked(False)
        QApplication.processEvents()
        operations.append(("Filter", time.perf_counter() - op_start))
        
        # Operation 4: Buffer size change
        op_start = time.perf_counter()
        logging_widget.buffer_size_spin.setValue(500)
        QApplication.processEvents()
        operations.append(("Buffer Size", time.perf_counter() - op_start))
        
        total_time = time.perf_counter() - start_time
        
        # Verify no operation takes more than 10ms
        for op_name, op_time in operations:
            assert op_time < 0.01, f"{op_name} took {op_time*1000:.1f}ms, expected <10ms"
        
        # Verify total time is reasonable
        assert total_time < 0.1, f"All operations took {total_time*1000:.1f}ms, expected <100ms"
        
        print(f"\\n✅ All operations completed in {total_time*1000:.1f}ms")
        for op_name, op_time in operations:
            print(f"   {op_name}: {op_time*1000:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
