"""Tests for start_proxy method."""
import os
import sys
import tempfile
import threading
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from localportmanager import LocalPortManager, PortRegistry


class TestStartProxy:
    """Test cases for start_proxy method."""
    
    @pytest.fixture
    def temp_state_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            path = f.name
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    def test_start_proxy_keyboard_interrupt(self, temp_state_file):
        """Test graceful shutdown on KeyboardInterrupt."""
        lpm = LocalPortManager(proxy_port=0, state_file=temp_state_file)
        
        mock_server = MagicMock()
        mock_server.serve_forever.side_effect = KeyboardInterrupt()
        
        with patch('localportmanager.ThreadingHTTPServer', return_value=mock_server):
            lpm.server = mock_server
            
            # Should not raise
            lpm.start_proxy()
            
            mock_server.server_close.assert_called_once()
    
    def test_signal_handler(self, temp_state_file):
        """Test signal handler setup."""
        lpm = LocalPortManager(proxy_port=0, state_file=temp_state_file)
        
        mock_server = MagicMock()
        
        with patch('localportmanager.ThreadingHTTPServer', return_value=mock_server), \
             patch('localportmanager.signal.signal') as mock_signal:
            
            mock_server.serve_forever.side_effect = KeyboardInterrupt()
            
            lpm.start_proxy()
            
            # Signal handlers should be registered
            assert mock_signal.call_count >= 2
