#!/usr/bin/env python3
"""
LocalPortManager Python API Example

This example shows how to use LocalPortManager programmatically
within your Python applications.
"""

import sys
import os

# Add parent directory to path for import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from localportmanager import LocalPortManager, PortRegistry


def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===\n")
    
    # Create instance with custom port
    lpm = LocalPortManager(proxy_port=1355)
    
    # Register services (without auto-starting)
    print("Registering services...")
    port1 = lpm.register_service("my-webapp", "python -m http.server {port}", auto_start=False)
    port2 = lpm.register_service("my-api", "uvicorn api:app --port {port}", auto_start=False)
    
    print(f"\nRegistered ports: {port1}, {port2}")
    
    # List all services
    print("\n--- Registered Services ---")
    lpm.list_services()
    
    # Unregister a service
    print("\nUnregistering 'my-webapp'...")
    lpm.unregister_service("my-webapp")
    
    # List again
    print("\n--- Updated Services ---")
    lpm.list_services()


def example_registry_only():
    """Using only the registry without the proxy."""
    print("\n=== Registry Only Example ===\n")
    
    # Create registry with custom state file
    registry = PortRegistry(state_file="/tmp/example_registry.json")
    
    # Register some ports
    registry.register("service-a", 4001)
    registry.register("service-b", 4002)
    
    # Get port for a service
    port = registry.get_port("service-a")
    print(f"Service 'service-a' is on port: {port}")
    
    # List all
    print(f"\nAll services: {registry.list_services()}")
    
    # Find a free port
    free_port = registry.find_free_port(start=4010, end=4020)
    print(f"\nFree port found: {free_port}")
    
    # Cleanup
    os.remove("/tmp/example_registry.json")


def example_zen_ai_integration():
    """Example integration with Zen-AI-Pentest style workflow."""
    print("\n=== Zen-AI-Pentest Integration Example ===\n")
    
    lpm = LocalPortManager(proxy_port=1355)
    
    # Simulate registering exploit listeners
    listeners = [
        ("http-listener", "python -m http.server {port}"),
        ("reverse-shell", "nc -lvp {port}"),
        ("payload-server", "python -m http.server {port}"),
    ]
    
    print("Registering penetration testing listeners:")
    for name, cmd in listeners:
        port = lpm.register_service(name, cmd, auto_start=False)
        print(f"  {name}: http://{name}.localhost:1355 (local port {port})")
    
    print("\n--- All Listeners ---")
    lpm.list_services()
    
    print("\n[NOTE] In a real scenario, you would start the proxy with lpm.start_proxy()")


if __name__ == "__main__":
    example_basic_usage()
    example_registry_only()
    example_zen_ai_integration()
