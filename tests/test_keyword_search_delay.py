"""
Test to reproduce and fix the 3-second delay in keyword search after starting log capture.
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


def test_keyword_search_delay(logging_widget, qtbot):
    """Test that keyword search is available immediately after start capture."""
    
    # Record start time
    start_time = time.time()
    
    # Ensure widget is properly initialized
    qtbot.addWidget(logging_widget)
    
    # Mock the worker to simulate logcat streaming
    with patch.object(logging_widget, 'logcat_worker') as mock_worker:
        mock_worker.isRunning.return_value = True
        
        # Start capture
        logging_widget.start_capture()
        
        # Process events to ensure immediate feedback
        QApplication.processEvents()
        
        # Check that search input is immediately enabled
        assert logging_widget.search_input.isEnabled()
        assert logging_widget.highlight_input.isEnabled()
        
        # Check that keyword highlighting works immediately
        logging_widget.highlight_input.setText("test")
        # Simulate Enter key press by directly calling the method
        logging_widget.add_highlight_keyword(show_dialogs=False)
        
        # Process events
        QApplication.processEvents()
        
        # Verify highlighting is set up
        assert "test" in logging_widget.highlight_keywords
        
        # Check elapsed time - should be much less than 3 seconds
        elapsed_time = time.time() - start_time
        assert elapsed_time < 1.0, f"Keyword search took {elapsed_time} seconds, expected < 1 second"


def test_theme_refresh_timers_dont_block_ui(logging_widget, qtbot):
    """Test that theme refresh timers don't block UI responsiveness."""
    
    qtbot.addWidget(logging_widget)
    
    # Record the initial state
    initial_time = time.time()
    
    # Test that the UI is responsive during theme refresh timers
    for i in range(5):
        # Type in search input
        logging_widget.search_input.setText(f"search{i}")
        QApplication.processEvents()
        
        # Add highlight keyword
        logging_widget.highlight_input.setText(f"highlight{i}")
        # Simulate Enter key press by directly calling the method
        logging_widget.add_highlight_keyword(show_dialogs=False)
        QApplication.processEvents()
        
        # Verify immediate response
        assert f"highlight{i}" in logging_widget.highlight_keywords
        
        # Small delay to simulate user interaction
        time.sleep(0.1)
    
    # Total time should be well under 3 seconds
    total_time = time.time() - initial_time
    assert total_time < 1.0, f"UI interactions took {total_time} seconds, expected < 1 second"


def test_identify_delay_source(logging_widget, qtbot):
    """Identify the source of the 3-second delay."""
    
    qtbot.addWidget(logging_widget)
    
    # Track timing of various operations
    timings = {}
    
    # Test search input responsiveness
    start = time.time()
    logging_widget.search_input.setText("test search")
    QApplication.processEvents()
    timings['search_input'] = time.time() - start
    
    # Test highlight input responsiveness
    start = time.time()
    logging_widget.highlight_input.setText("test highlight")
    QApplication.processEvents()
    timings['highlight_input'] = time.time() - start
    
    # Test adding highlight keyword
    start = time.time()
    result = logging_widget.add_highlight_keyword(show_dialogs=False)
    QApplication.processEvents()
    timings['add_highlight'] = time.time() - start
    
    # Test applying filters
    start = time.time()
    logging_widget.apply_filters()
    QApplication.processEvents()
    timings['apply_filters'] = time.time() - start
    
    # Test refresh display
    start = time.time()
    logging_widget.refresh_display()
    QApplication.processEvents()
    timings['refresh_display'] = time.time() - start
    
    # Test theme refresh
    start = time.time()
    logging_widget.refresh_theme()
    QApplication.processEvents()
    timings['refresh_theme'] = time.time() - start
    
    # Print timing results for analysis
    print("\\nTiming Analysis:")
    for operation, duration in timings.items():
        print(f"  {operation}: {duration:.3f} seconds")
        # None of these should take more than 1 second
        assert duration < 1.0, f"{operation} took {duration} seconds, which is too long"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
