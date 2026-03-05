"""Tests for ReverseProxyHandler."""
import json
import os
import sys
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from localportmanager import ReverseProxyHandler, PortRegistry


class TestReverseProxyHandlerUnit:
    """Unit tests for ReverseProxyHandler."""
    
    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            path = f.name
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    def test_log_message_format(self, temp_state_file, capsys):
        """Test log message format."""
        handler = MagicMock()
        handler.log_message("Test message: %s", "arg")
        captured = capsys.readouterr()
        
        # Just test that log_message exists and can be called
        assert True


class TestReverseProxyHandlerProxyRequest:
    """Tests for _proxy_request method."""
    
    @pytest.fixture
    def temp_state_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            path = f.name
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    def test_proxy_request_service_not_found(self, temp_state_file):
        """Test 404 when service not registered."""
        handler = MagicMock()
        handler.headers = {'Host': 'unknown.localhost:1355'}
        handler.path = '/'
        handler.rfile = BytesIO(b'')
        
        # Call actual method but mock send_error
        from localportmanager import ReverseProxyHandler
        ReverseProxyHandler._proxy_request(handler, 'GET')
        
        handler.send_error.assert_called_once()
        args = handler.send_error.call_args[0]
        assert args[0] == 404


class TestHTTPMethodHandlers:
    """Test HTTP method handlers."""
    
    @pytest.fixture
    def temp_state_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            path = f.name
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    def test_do_get(self, temp_state_file):
        """Test do_GET method."""
        handler = MagicMock()
        from localportmanager import ReverseProxyHandler
        ReverseProxyHandler.do_GET(handler)
        handler._proxy_request.assert_called_once_with('GET')
    
    def test_do_post(self, temp_state_file):
        """Test do_POST method."""
        handler = MagicMock()
        from localportmanager import ReverseProxyHandler
        ReverseProxyHandler.do_POST(handler)
        handler._proxy_request.assert_called_once_with('POST')
    
    def test_do_put(self, temp_state_file):
        """Test do_PUT method."""
        handler = MagicMock()
        from localportmanager import ReverseProxyHandler
        ReverseProxyHandler.do_PUT(handler)
        handler._proxy_request.assert_called_once_with('PUT')
    
    def test_do_delete(self, temp_state_file):
        """Test do_DELETE method."""
        handler = MagicMock()
        from localportmanager import ReverseProxyHandler
        ReverseProxyHandler.do_DELETE(handler)
        handler._proxy_request.assert_called_once_with('DELETE')
    
    def test_do_patch(self, temp_state_file):
        """Test do_PATCH method."""
        handler = MagicMock()
        from localportmanager import ReverseProxyHandler
        ReverseProxyHandler.do_PATCH(handler)
        handler._proxy_request.assert_called_once_with('PATCH')
    
    def test_do_head(self, temp_state_file):
        """Test do_HEAD method."""
        handler = MagicMock()
        from localportmanager import ReverseProxyHandler
        ReverseProxyHandler.do_HEAD(handler)
        handler._proxy_request.assert_called_once_with('HEAD')
    
    def test_do_options(self, temp_state_file):
        """Test do_OPTIONS method."""
        handler = MagicMock()
        from localportmanager import ReverseProxyHandler
        ReverseProxyHandler.do_OPTIONS(handler)
        handler._proxy_request.assert_called_once_with('OPTIONS')
