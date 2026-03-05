"""Edge case tests for LocalPortManager."""
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from localportmanager import LocalPortManager, PortRegistry, ReverseProxyHandler, main


class TestPortRegistryEdgeCases:
    """Edge case tests for PortRegistry."""
    
    def test_get_port_with_none_value(self, temp_state_file):
        """Test get_port when value is None."""
        registry = PortRegistry(state_file=temp_state_file)
        # Manually set to None
        registry.mappings = {"test": None}
        result = registry.get_port("test")
        assert result is None
    
    def test_load_with_empty_json_object(self, temp_state_file):
        """Test loading empty JSON object."""
        with open(temp_state_file, 'w') as f:
            f.write('{}')
        
        registry = PortRegistry(state_file=temp_state_file)
        assert registry.mappings == {}
    
    def test_load_with_null_values(self, temp_state_file):
        """Test loading JSON with null values."""
        with open(temp_state_file, 'w') as f:
            json.dump({"test": None}, f)
        
        registry = PortRegistry(state_file=temp_state_file)
        # Should handle gracefully
        result = registry.get_port("test")
        assert result is None


class TestLocalPortManagerEdgeCases:
    """Edge case tests for LocalPortManager."""
    
    def test_register_service_with_special_chars_in_command(self, temp_state_file):
        """Test register with special characters in command."""
        lpm = LocalPortManager(proxy_port=9999, state_file=temp_state_file)
        
        with patch('builtins.input', return_value='n'):
            port = lpm.register_service("test", "echo 'Hello World' && ls -la {port}")
            
            assert port is not None
            assert lpm.registry.get_port("test") == port
    
    def test_unregister_nonexistent_service_output(self, temp_state_file, capsys):
        """Test unregister output for nonexistent service."""
        lpm = LocalPortManager(proxy_port=9999, state_file=temp_state_file)
        
        lpm.unregister_service("nonexistent")
        captured = capsys.readouterr()
        
        assert "not found" in captured.out
    
    def test_list_services_after_unregister(self, temp_state_file, capsys):
        """Test list services after unregistering all."""
        lpm = LocalPortManager(proxy_port=9999, state_file=temp_state_file)
        
        with patch('builtins.input', return_value='n'):
            lpm.register_service("test", "cmd")
        
        lpm.unregister_service("test")
        lpm.list_services()
        captured = capsys.readouterr()
        
        assert "No services registered" in captured.out


class TestArgumentParsing:
    """Test argument parsing."""
    
    def test_default_port_argument(self):
        """Test default port value."""
        with patch('sys.argv', ['localportmanager', 'list']), \
             tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
            
        try:
            with patch('sys.argv', ['localportmanager', '--state-file', state_file, 'list']):
                main()
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_custom_state_file(self):
        """Test custom state file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
            f.write('{"test": 4001}')
        
        try:
            with patch('sys.argv', [
                'localportmanager',
                '--state-file', state_file,
                '--port', '8080',
                'list'
            ]):
                main()
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)


class TestMainModule:
    """Test main module functionality."""
    
    def test_main_help(self):
        """Test main with --help."""
        with patch('sys.argv', ['localportmanager', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 0
    
    def test_main_proxy_with_custom_port(self):
        """Test proxy command with custom port."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            with patch('localportmanager.LocalPortManager.start_proxy') as mock_start:
                with patch('sys.argv', [
                    'localportmanager',
                    '--port', '8080',
                    '--state-file', state_file,
                    'proxy'
                ]):
                    # Should set up and call start_proxy
                    try:
                        main()
                    except SystemExit:
                        pass
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
