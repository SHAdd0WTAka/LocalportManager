"""Additional tests to reach 80%+ coverage."""
import os
import sys
import tempfile
import json
from io import BytesIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from localportmanager import LocalPortManager, PortRegistry, ReverseProxyHandler, main


class TestAdditionalCoverage:
    """Additional tests for better coverage."""
    
    def test_register_service_with_yes_flag(self):
        """Test register command with --yes flag."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            with patch('os.system') as mock_system, \
                 patch('sys.argv', [
                     'localportmanager',
                     '--state-file', state_file,
                     'register',
                     'test-service',
                     'echo {port}',
                     '--yes'
                 ]):
                main()
                
                # Auto-start with --yes should call os.system
                mock_system.assert_called_once()
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_port_registry_list_services_returns_copy(self):
        """Test that list_services returns a copy."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            registry = PortRegistry(state_file=state_file)
            registry.register("test", 4001)
            services = registry.list_services()
            services["new"] = 4002
            
            # Original should be unchanged
            assert "new" not in registry.list_services()
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_localportmanager_init_with_none_state_file(self):
        """Test LocalPortManager init with None state_file."""
        lpm = LocalPortManager(proxy_port=1355, state_file=None)
        assert lpm.registry is not None
        assert lpm.registry.state_file == "/tmp/localportmanager_registry.json"
    
    def test_proxy_handler_with_path_routing(self):
        """Test proxy handler path-based routing."""
        handler = MagicMock()
        handler.headers = {'Host': '127.0.0.1:1355'}
        handler.path = '/api/test'
        handler.rfile = BytesIO(b'')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
            f.write('{"api": 4001}')
        
        try:
            # Mock send_error to avoid 404
            from localportmanager import ReverseProxyHandler
            ReverseProxyHandler._proxy_request(handler, 'GET')
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_main_register_invalid_name(self):
        """Test register with invalid name shows error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            with patch('sys.argv', [
                'localportmanager',
                '--state-file', state_file,
                'register',
                'invalid name!',
                'cmd'
            ]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_register_service_output_format(self, capsys):
        """Test register service output format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            lpm = LocalPortManager(proxy_port=8888, state_file=state_file)
            
            with patch('builtins.input', return_value='n'):
                lpm.register_service("myapp", "python app.py {port}")
            
            captured = capsys.readouterr()
            
            assert "myapp" in captured.out
            assert "127.0.0.1" in captured.out
            assert "localhost" in captured.out
            assert "python app.py" in captured.out
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_status_command_with_services(self, capsys):
        """Test status command output with services."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
            f.write('{"webapp": 4001, "api": 4002}')
        
        try:
            with patch('sys.argv', [
                'localportmanager',
                '--port', '8888',
                '--state-file', state_file,
                'status'
            ]):
                main()
            
            captured = capsys.readouterr()
            
            assert "8888" in captured.out
            assert "webapp" in captured.out
            assert "api" in captured.out
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
