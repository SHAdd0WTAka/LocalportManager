"""Tests for LocalPortManager class."""
import json
import os
import sys
import tempfile
import threading
import time
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from localportmanager import LocalPortManager, PortRegistry


class TestLocalPortManager:
    """Test cases for LocalPortManager."""
    
    @pytest.fixture
    def temp_state_file(self):
        """Create a temporary state file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            path = f.name
        yield path
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def lpm(self, temp_state_file):
        """Create a LocalPortManager with temp state file."""
        return LocalPortManager(proxy_port=9999, state_file=temp_state_file)
    
    def test_init_default_values(self):
        """Test that init uses default values."""
        lpm = LocalPortManager()
        assert lpm.proxy_port == 1355
        assert lpm.registry is not None
    
    def test_init_custom_values(self, temp_state_file):
        """Test that init accepts custom values."""
        lpm = LocalPortManager(proxy_port=8080, state_file=temp_state_file)
        assert lpm.proxy_port == 8080
        assert lpm.registry.state_file == temp_state_file
    
    def test_register_service_validates_name(self, lpm):
        """Test that register_service validates service name."""
        with pytest.raises(ValueError, match="alphanumeric"):
            lpm.register_service("invalid name!", "cmd")
    
    def test_register_service_empty_name(self, lpm):
        """Test that register_service rejects empty name."""
        with pytest.raises(ValueError, match="alphanumeric"):
            lpm.register_service("", "cmd")
    
    def test_register_service_accepts_dashes_and_underscores(self, lpm):
        """Test that register_service accepts dashes and underscores."""
        with patch('builtins.input', return_value='n'):
            port = lpm.register_service("my-service_01", "cmd {port}")
        
        assert isinstance(port, int)
        assert lpm.registry.get_port("my-service_01") == port
    
    def test_register_service_replaces_placeholder(self, lpm, temp_state_file, capsys):
        """Test that register_service replaces {port} placeholder."""
        with patch('builtins.input', return_value='n'):
            lpm.register_service("test", "python -m http.server {port}")
            captured = capsys.readouterr()
            
            assert "python -m http.server" in captured.out
    
    def test_register_service_appends_port_when_no_placeholder(self, lpm, capsys):
        """Test that register_service appends port when no placeholder."""
        with patch('builtins.input', return_value='n'):
            lpm.register_service("test", "python server.py")
            captured = capsys.readouterr()
            
            assert "python server.py" in captured.out
    
    def test_register_service_auto_start(self, lpm):
        """Test that register_service can auto-start."""
        with patch('os.system') as mock_system:
            lpm.register_service("test", "echo {port}", auto_start=True)
            
            mock_system.assert_called_once()
            assert "echo" in mock_system.call_args[0][0]
    
    def test_register_service_prompts_for_start(self, lpm):
        """Test that register_service prompts for start."""
        with patch('builtins.input', return_value='y'), \
             patch('os.system') as mock_system:
            lpm.register_service("test", "echo {port}")
            
            mock_system.assert_called_once()
    
    def test_register_service_skips_start_on_no(self, lpm):
        """Test that register_service skips start on 'n'."""
        with patch('builtins.input', return_value='n'), \
             patch('os.system') as mock_system:
            lpm.register_service("test", "echo {port}")
            
            mock_system.assert_not_called()
    
    def test_unregister_service_success(self, lpm, temp_state_file):
        """Test successful unregister."""
        with patch('builtins.input', return_value='n'):
            lpm.register_service("test", "cmd")
        
        result = lpm.unregister_service("test")
        
        assert result is True
        # Re-read registry to verify
        registry2 = PortRegistry(state_file=temp_state_file)
        assert registry2.get_port("test") is None
    
    def test_unregister_service_failure(self, lpm):
        """Test unregister of nonexistent service."""
        result = lpm.unregister_service("nonexistent")
        
        assert result is False
    
    def test_list_services_empty(self, lpm, capsys):
        """Test list_services with no services."""
        lpm.list_services()
        captured = capsys.readouterr()
        
        assert "No services registered" in captured.out
    
    def test_list_services_with_data(self, lpm, capsys):
        """Test list_services with registered services."""
        with patch('builtins.input', return_value='n'):
            lpm.register_service("webapp", "cmd1")
            lpm.register_service("api", "cmd2")
        
        lpm.list_services()
        captured = capsys.readouterr()
        
        assert "webapp" in captured.out
        assert "api" in captured.out
        assert "http://webapp.localhost:9999" in captured.out


class TestMain:
    """Test cases for main function."""
    
    def test_main_no_command_prints_help(self, capsys):
        """Test that main prints help when no command given."""
        with patch('sys.argv', ['localportmanager']):
            with pytest.raises(SystemExit) as exc_info:
                from localportmanager import main
                main()
            
            assert exc_info.value.code == 1
    
    def test_main_version(self, capsys):
        """Test --version flag."""
        with patch('sys.argv', ['localportmanager', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                from localportmanager import main
                main()
            
            assert exc_info.value.code == 0
    
    def test_main_register_command(self):
        """Test register command."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
            f.write('{}')  # Write empty JSON object
        
        try:
            with patch('builtins.input', return_value='n'), \
                 patch('sys.argv', [
                    'localportmanager', 
                    '--state-file', state_file,
                    'register', 
                    'test-service', 
                    'python -m http.server {port}'
                ]):
                from localportmanager import main
                main()
            
            # Verify directly
            with open(state_file, 'r') as f:
                data = json.load(f)
            
            assert "test-service" in data
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_main_unregister_command(self):
        """Test unregister command."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            registry = PortRegistry(state_file=state_file)
            registry.register("test-service", 4001)
            
            with patch('sys.argv', [
                'localportmanager',
                '--state-file', state_file,
                'unregister',
                'test-service'
            ]):
                from localportmanager import main
                main()
            
            # Create fresh registry to verify
            registry2 = PortRegistry(state_file=state_file)
            assert registry2.get_port("test-service") is None
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_main_list_command(self, capsys):
        """Test list command."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            registry = PortRegistry(state_file=state_file)
            registry.register("test", 4001)
            
            with patch('sys.argv', [
                'localportmanager',
                '--state-file', state_file,
                'list'
            ]):
                from localportmanager import main
                main()
            
            captured = capsys.readouterr()
            assert "test" in captured.out
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    def test_main_status_command(self, capsys):
        """Test status command."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            with patch('sys.argv', [
                'localportmanager',
                '--port', '8888',
                '--state-file', state_file,
                'status'
            ]):
                from localportmanager import main
                main()
            
            captured = capsys.readouterr()
            assert "8888" in captured.out
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
