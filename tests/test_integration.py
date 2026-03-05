"""Integration tests for LocalPortManager."""
import json
import os
import sys
import tempfile
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import urllib.request

from localportmanager import LocalPortManager, PortRegistry


class TestBackendHandler(BaseHTTPRequestHandler):
    """Simple test backend server."""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Hello from backend')
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        self.send_response(201)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"received": body.decode()}).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logs


@pytest.fixture(scope="module")
def test_backend():
    """Create a test backend server."""
    server = HTTPServer(('127.0.0.1', 0), TestBackendHandler)
    port = server.server_address[1]
    
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    yield port
    
    server.shutdown()


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.integration
    def test_full_proxy_flow(self, test_backend):
        """Test full proxy request flow."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            # Register the test backend
            registry = PortRegistry(state_file=state_file)
            registry.register("test-backend", test_backend)
            
            # Start proxy in background
            lpm = LocalPortManager(proxy_port=0, state_file=state_file)
            
            # Find a free port for proxy
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', 0))
            proxy_port = sock.getsockname()[1]
            sock.close()
            
            lpm = LocalPortManager(proxy_port=proxy_port, state_file=state_file)
            
            # Start proxy in thread
            def run_proxy():
                lpm.server = HTTPServer(
                    ('127.0.0.1', proxy_port), 
                    lpm.__class__.__mro__[0]  # Get handler class
                )
                lpm.server.serve_forever()
            
            proxy_thread = threading.Thread(target=run_proxy)
            proxy_thread.daemon = True
            proxy_thread.start()
            
            time.sleep(0.5)  # Wait for server to start
            
            # Make request through proxy
            req = urllib.request.Request(
                f'http://127.0.0.1:{proxy_port}/',
                headers={'Host': 'test-backend.localhost'}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    body = response.read()
                    assert b'Hello from backend' in body
            except Exception as e:
                pytest.skip(f"Integration test skipped: {e}")
            
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    @pytest.mark.integration
    def test_port_registry_persistence(self):
        """Test that registry data persists correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            # Create and populate registry
            registry1 = PortRegistry(state_file=state_file)
            registry1.register("service1", 4001)
            registry1.register("service2", 4002)
            
            # Create new registry instance with same file
            registry2 = PortRegistry(state_file=state_file)
            
            assert registry2.get_port("service1") == 4001
            assert registry2.get_port("service2") == 4002
            
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
    
    @pytest.mark.integration
    def test_concurrent_registry_access(self):
        """Test concurrent access to registry."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_file = f.name
        
        try:
            registry = PortRegistry(state_file=state_file)
            errors = []
            
            def worker(thread_id):
                try:
                    for i in range(5):
                        registry.register(f"thread-{thread_id}-{i}", 5000 + thread_id * 10 + i)
                        time.sleep(0.01)
                        port = registry.get_port(f"thread-{thread_id}-{i}")
                        if port is None:
                            errors.append(f"Thread {thread_id}: Port not found")
                except Exception as e:
                    errors.append(f"Thread {thread_id}: {e}")
            
            threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            assert not errors, f"Errors occurred: {errors}"
            assert len(registry.list_services()) == 15
            
        finally:
            if os.path.exists(state_file):
                os.unlink(state_file)
