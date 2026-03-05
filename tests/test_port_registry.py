"""Tests for PortRegistry class."""
import json
import os
import tempfile
import threading
import time
import pytest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from localportmanager import PortRegistry


class TestPortRegistry:
    """Test cases for PortRegistry."""
    
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
    def registry(self, temp_state_file):
        """Create a PortRegistry with temp state file."""
        return PortRegistry(state_file=temp_state_file)
    
    def test_init_creates_empty_registry(self, temp_state_file):
        """Test that init creates an empty registry."""
        registry = PortRegistry(state_file=temp_state_file)
        assert registry.mappings == {}
    
    def test_init_loads_existing_data(self, temp_state_file):
        """Test that init loads existing data from file."""
        with open(temp_state_file, 'w') as f:
            json.dump({"service1": 4001, "service2": 4002}, f)
        
        registry = PortRegistry(state_file=temp_state_file)
        assert registry.mappings == {"service1": 4001, "service2": 4002}
    
    def test_init_handles_corrupted_file(self, temp_state_file):
        """Test that init handles corrupted JSON files."""
        with open(temp_state_file, 'w') as f:
            f.write("not valid json")
        
        registry = PortRegistry(state_file=temp_state_file)
        assert registry.mappings == {}
    
    def test_register_saves_to_file(self, registry, temp_state_file):
        """Test that register persists to file."""
        registry.register("test-service", 4001)
        
        with open(temp_state_file, 'r') as f:
            data = json.load(f)
        
        assert data == {"test-service": 4001}
    
    def test_register_overwrites_existing(self, registry, temp_state_file):
        """Test that register overwrites existing service."""
        registry.register("test-service", 4001)
        registry.register("test-service", 4002)
        
        with open(temp_state_file, 'r') as f:
            data = json.load(f)
        
        assert data == {"test-service": 4002}
    
    def test_unregister_removes_service(self, registry, temp_state_file):
        """Test that unregister removes service."""
        registry.register("test-service", 4001)
        result = registry.unregister("test-service")
        
        assert result is True
        assert registry.mappings == {}
        
        with open(temp_state_file, 'r') as f:
            data = json.load(f)
        assert data == {}
    
    def test_unregister_nonexistent_returns_false(self, registry):
        """Test that unregister returns False for nonexistent service."""
        result = registry.unregister("nonexistent")
        assert result is False
    
    def test_get_port_returns_int(self, registry):
        """Test that get_port returns integer."""
        registry.register("test", 4001)
        port = registry.get_port("test")
        
        assert isinstance(port, int)
        assert port == 4001
    
    def test_get_port_returns_none_for_nonexistent(self, registry):
        """Test that get_port returns None for nonexistent service."""
        port = registry.get_port("nonexistent")
        assert port is None
    
    def test_get_port_handles_string_values(self, temp_state_file):
        """Test that get_port handles string port values."""
        with open(temp_state_file, 'w') as f:
            json.dump({"test": "4001"}, f)
        
        registry = PortRegistry(state_file=temp_state_file)
        port = registry.get_port("test")
        
        assert isinstance(port, int)
        assert port == 4001
    
    def test_list_services_returns_copy(self, registry):
        """Test that list_services returns a copy."""
        registry.register("test", 4001)
        services = registry.list_services()
        services["new"] = 4002
        
        assert registry.mappings == {"test": 4001}
    
    def test_find_free_port_skips_used_ports(self, registry):
        """Test that find_free_port skips used ports."""
        registry.register("service1", 4000)
        registry.register("service2", 4001)
        
        port = registry.find_free_port(start=4000, end=4010)
        
        assert port == 4002
    
    def test_find_free_port_respects_range(self, registry):
        """Test that find_free_port respects port range."""
        # Block ports 4000-4004
        for i in range(5):
            registry.register(f"service{i}", 4000 + i)
        
        port = registry.find_free_port(start=4000, end=4010)
        
        assert port == 4005
    
    def test_find_free_port_raises_when_no_ports_available(self, registry):
        """Test that find_free_port raises when no ports available."""
        # Block all ports in small range
        for i in range(5):
            registry.register(f"service{i}", 4000 + i)
        
        with pytest.raises(RuntimeError, match="No free ports available"):
            registry.find_free_port(start=4000, end=4004)
    
    def test_thread_safety(self, temp_state_file):
        """Test thread safety of PortRegistry."""
        registry = PortRegistry(state_file=temp_state_file)
        errors = []
        
        def register_services():
            try:
                for i in range(10):
                    registry.register(f"thread-{threading.current_thread().ident}-{i}", 5000 + i)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=register_services) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert not errors
        assert len(registry.mappings) == 50
    
    def test_default_state_file(self):
        """Test default state file path."""
        registry = PortRegistry()
        assert registry.state_file == "/tmp/localportmanager_registry.json"
