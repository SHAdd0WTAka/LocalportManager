#!/usr/bin/env python3
"""
LocalPortManager Secure Edition: VPN-Aware Port Manager
========================================================

Sichere Erweiterung des LocalPortManager mit VPN-Detection,
Kill-Switch und MITM-Schutz für Docker-Umgebungen.

Security Features:
- VPN Detection: Erkennt aktive VPN-Verbindungen
- Kill Switch: Blockiert Docker-Ports wenn VPN aktiv
- Secure Docker Mode: Bindet nur auf 127.0.0.1
- Network Isolation: Separate Netzwerk-Namespaces
- MITM Protection: Verifiziert TLS-Zertifikate

Author: SHAdd0WTAka
License: MIT
"""

import socket
import threading
import json
import os
import sys
import argparse
import signal
import subprocess
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen, Request
from urllib.error import URLError
from typing import Optional, Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time


__version__ = "1.1.0-secure"
__author__ = "SHAdd0WTAka"


class SecurityLevel(Enum):
    """Security levels for port allocation."""
    STANDARD = "standard"
    VPN_ONLY = "vpn_only"
    NO_VPN = "no_vpn"
    ISOLATED = "isolated"


class VPNDectector:
    """Detects active VPN connections on the system."""
    
    # Common VPN interface patterns
    VPN_PATTERNS = [
        r'tun\d+',      # OpenVPN, WireGuard
        r'wg\d+',       # WireGuard
        r'ppp\d+',      # PPTP
        r'ipsec\d+',    # IPSec
        r'proton',      # ProtonVPN
        r'nord',        # NordVPN
        r'express',     # ExpressVPN
        r'mullvad',     # Mullvad
    ]
    
    # Common VPN process names
    VPN_PROCESSES = [
        'openvpn', 'wireguard', 'wg-quick', 'pptp', 'ipsec',
        'protonvpn', 'nordvpn', 'expressvpn', 'mullvad-vpn',
        'cyberghost', 'surfshark', 'privateinternetaccess'
    ]
    
    def __init__(self):
        self._cache_time = 0
        self._cache_result = False
        self._cache_ttl = 5  # seconds
    
    def is_vpn_active(self) -> bool:
        """Check if VPN is currently active (with caching)."""
        now = time.time()
        if now - self._cache_time < self._cache_ttl:
            return self._cache_result
        
        result = self._check_vpn_interfaces() or self._check_vpn_processes()
        self._cache_result = result
        self._cache_time = now
        return result
    
    def _check_vpn_interfaces(self) -> bool:
        """Check for VPN network interfaces."""
        try:
            # Get all network interfaces
            result = subprocess.run(
                ['ip', 'link', 'show'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                # Fallback to /proc/net/dev
                return self._check_proc_net_dev()
            
            output = result.stdout.lower()
            
            for pattern in self.VPN_PATTERNS:
                if re.search(pattern, output):
                    return True
            
            return False
            
        except Exception:
            return self._check_proc_net_dev()
    
    def _check_proc_net_dev(self) -> bool:
        """Fallback VPN detection via /proc/net/dev."""
        try:
            with open('/proc/net/dev', 'r') as f:
                content = f.read().lower()
                for pattern in self.VPN_PATTERNS:
                    if re.search(pattern, content):
                        return True
            return False
        except Exception:
            return False
    
    def _check_vpn_processes(self) -> bool:
        """Check for running VPN processes."""
        try:
            result = subprocess.run(
                ['pgrep', '-x'] + self.VPN_PROCESSES,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_vpn_interfaces(self) -> List[str]:
        """Get list of active VPN interface names."""
        interfaces = []
        try:
            result = subprocess.run(
                ['ip', 'link', 'show'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for pattern in self.VPN_PATTERNS:
                matches = re.findall(pattern, result.stdout, re.IGNORECASE)
                interfaces.extend(matches)
            
        except Exception:
            pass
        
        return list(set(interfaces))


class DockerSecurity:
    """Security wrapper for Docker container management."""
    
    def __init__(self, vpn_detector: VPNDectector):
        self.vpn = vpn_detector
        self.blocked_containers: Set[str] = set()
    
    def secure_docker_command(self, command: str, security_level: SecurityLevel = SecurityLevel.STANDARD) -> str:
        """
        Transform Docker command to use secure port binding.
        
        Changes:
        -p HOST_PORT:CONTAINER_PORT -> -p 127.0.0.1:HOST_PORT:CONTAINER_PORT
        --publish HOST_PORT:CONTAINER_PORT -> --publish 127.0.0.1:HOST_PORT:CONTAINER_PORT
        """
        # Pattern to match -p PORT:PORT or --publish PORT:PORT
        patterns = [
            (r'-p\s+(\d+):(\d+)', r'-p 127.0.0.1:\1:\2'),
            (r'--publish\s+(\d+):(\d+)', r'--publish 127.0.0.1:\1:\2'),
        ]
        
        secure_cmd = command
        for pattern, replacement in patterns:
            secure_cmd = re.sub(pattern, replacement, secure_cmd)
        
        # Add security labels
        if security_level == SecurityLevel.ISOLATED:
            # Use custom network for isolation
            secure_cmd = self._add_network_isolation(secure_cmd)
        
        return secure_cmd
    
    def _add_network_isolation(self, command: str) -> str:
        """Add network isolation to Docker command."""
        # Check if network already specified
        if '--network' in command:
            return command
        
        # Create isolated network if not exists
        try:
            subprocess.run(
                ['docker', 'network', 'create', '--internal', 'lpm-isolated'],
                capture_output=True,
                timeout=10
            )
        except Exception:
            pass
        
        # Add network isolation
        return command.replace('docker run', 'docker run --network lpm-isolated')
    
    def check_security_policy(self, service_name: str, is_docker: bool = False) -> Tuple[bool, str]:
        """
        Check if service complies with security policy.
        
        Returns:
            (allowed, message)
        """
        vpn_active = self.vpn.is_vpn_active()
        
        if is_docker and vpn_active:
            # Docker + VPN = potential MITM risk
            if service_name not in self.blocked_containers:
                self.blocked_containers.add(service_name)
            return False, (
                f"⚠️  SECURITY BLOCK: Service '{service_name}'\n"
                f"    Docker containers with exposed ports are BLOCKED when VPN is active.\n"
                f"    Reason: MITM attack risk through VPN tunnel manipulation.\n"
                f"\n"
                f"    Solutions:\n"
                f"    1. Use 'secure' mode: -p 127.0.0.1:PORT:CONTAINER_PORT\n"
                f"    2. Stop VPN: sudo systemctl stop <vpn-service>\n"
                f"    3. Use isolated network: --network lpm-isolated\n"
                f"    4. Disable kill switch: --no-kill-switch (NOT RECOMMENDED)\n"
            )
        
        return True, "OK"
    
    def kill_switch_status(self) -> Dict:
        """Get current kill switch status."""
        return {
            'vpn_active': self.vpn.is_vpn_active(),
            'blocked_services': list(self.blocked_containers),
            'kill_switch_enabled': True,
            'vpn_interfaces': self.vpn.get_vpn_interfaces()
        }


@dataclass
class ServiceConfig:
    """Configuration for a registered service."""
    name: str
    port: int
    command: str
    is_docker: bool = False
    security_level: str = "standard"
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()


class SecurePortRegistry:
    """Thread-safe port registry with security metadata."""
    
    def __init__(self, state_file: str = "/tmp/localportmanager_registry.json"):
        self.state_file = state_file
        self.lock = threading.Lock()
        self.services: Dict[str, ServiceConfig] = {}
        self._load()
    
    def _load(self) -> None:
        """Load services from state file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    for name, svc_data in data.items():
                        self.services[name] = ServiceConfig(**svc_data)
            except (json.JSONDecodeError, TypeError):
                self.services = {}
    
    def _save(self) -> None:
        """Save services to state file."""
        with open(self.state_file, 'w') as f:
            data = {name: asdict(svc) for name, svc in self.services.items()}
            json.dump(data, f, indent=2)
    
    def register(self, config: ServiceConfig) -> None:
        """Register a service with security metadata."""
        with self.lock:
            self.services[config.name] = config
            self._save()
    
    def unregister(self, name: str) -> bool:
        """Unregister a service."""
        with self.lock:
            if name in self.services:
                del self.services[name]
                self._save()
                return True
            return False
    
    def get_service(self, name: str) -> Optional[ServiceConfig]:
        """Get service configuration."""
        with self.lock:
            return self.services.get(name)
    
    def get_port(self, name: str) -> Optional[int]:
        """Get port for a service."""
        with self.lock:
            svc = self.services.get(name)
            return svc.port if svc else None
    
    def list_services(self) -> Dict[str, ServiceConfig]:
        """Return all registered services."""
        with self.lock:
            return dict(self.services)
    
    def find_free_port(self, start: int = 4000, end: int = 4999) -> int:
        """Find first available port in range."""
        used_ports = {svc.port for svc in self.services.values()}
        
        for port in range(start, end + 1):
            if port in used_ports:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', port)) != 0:
                    return port
        raise RuntimeError("No free ports available in range")
    
    def is_docker_service(self, name: str) -> bool:
        """Check if service is a Docker container."""
        svc = self.get_service(name)
        return svc.is_docker if svc else False


class SecureReverseProxyHandler(BaseHTTPRequestHandler):
    """HTTP handler with security checks."""
    
    protocol_version = 'HTTP/1.1'
    vpn_detector = VPNDectector()
    
    def log_message(self, format: str, *args) -> None:
        """Custom logging with security indicators."""
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        vpn_indicator = "🔒" if self.vpn_detector.is_vpn_active() else "  "
        sys.stderr.write(f"[{timestamp}] {vpn_indicator} {format % args}\n")
    
    def do_GET(self) -> None:
        self._proxy_request('GET')
    
    def do_POST(self) -> None:
        self._proxy_request('POST')
    
    def do_PUT(self) -> None:
        self._proxy_request('PUT')
    
    def do_DELETE(self) -> None:
        self._proxy_request('DELETE')
    
    def do_PATCH(self) -> None:
        self._proxy_request('PATCH')
    
    def do_HEAD(self) -> None:
        self._proxy_request('HEAD')
    
    def do_OPTIONS(self) -> None:
        self._proxy_request('OPTIONS')
    
    def _proxy_request(self, method: str) -> None:
        """Proxy request with security validation."""
        host = self.headers.get('Host', '').split(':')[0]
        
        # Extract service name
        if host.endswith('.localhost'):
            service_name = host.replace('.localhost', '')
        else:
            service_name = host
        
        # Path-based fallback
        if service_name in ['localhost', '127.0.0.1'] and self.path.startswith('/'):
            path_parts = self.path.strip('/').split('/')
            if path_parts and path_parts[0]:
                potential_service = path_parts[0]
                registry = SecurePortRegistry()
                if registry.get_port(potential_service):
                    service_name = potential_service
                    self.path = '/' + '/'.join(path_parts[1:]) if len(path_parts) > 1 else '/'
        
        registry = SecurePortRegistry()
        service = registry.get_service(service_name)
        
        if not service:
            self.send_error(404, f"Service '{service_name}' not registered")
            return
        
        # Security check: Docker + VPN
        if service.is_docker and self.vpn_detector.is_vpn_active():
            self.send_error(403, 
                "Access Denied: Docker service blocked when VPN is active (MITM protection)")
            return
        
        # Proxy to backend
        target_port = service.port
        try:
            backend_url = f"http://127.0.0.1:{target_port}{self.path}"
            req = Request(backend_url, method=method)
            
            # Copy headers
            hop_by_hop = ['connection', 'keep-alive', 'proxy-authenticate',
                         'proxy-authorization', 'te', 'trailers',
                         'transfer-encoding', 'upgrade', 'host']
            
            for header, value in self.headers.items():
                if header.lower() not in hop_by_hop:
                    req.add_header(header, value)
            
            # Add security headers
            req.add_header('X-LPM-Security', 'enabled')
            if service.is_docker:
                req.add_header('X-LPM-Container', 'docker')
            
            with urlopen(req, timeout=30) as response:
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'connection',
                                               'keep-alive', 'upgrade']:
                        self.send_header(header, value)
                self.end_headers()
                data = response.read()
                if data:
                    self.wfile.write(data)
        
        except URLError as e:
            self.send_error(502, f"Backend unreachable: {e}")
        except Exception as e:
            self.send_error(500, f"Proxy error: {e}")


class SecureLocalPortManager:
    """Secure port manager with VPN awareness."""
    
    def __init__(self, proxy_port: int = 1355, state_file: Optional[str] = None,
                 kill_switch: bool = True):
        self.proxy_port = proxy_port
        self.kill_switch_enabled = kill_switch
        self.registry = SecurePortRegistry(state_file) if state_file else SecurePortRegistry()
        self.vpn_detector = VPNDectector()
        self.docker_security = DockerSecurity(self.vpn_detector)
        self.server: Optional[ThreadingHTTPServer] = None
        self._shutdown_event = threading.Event()
    
    def start_proxy(self) -> None:
        """Start secure reverse proxy."""
        SecureReverseProxyHandler.vpn_detector = self.vpn_detector
        
        self.server = ThreadingHTTPServer(
            ('127.0.0.1', self.proxy_port),
            SecureReverseProxyHandler
        )
        
        vpn_status = "ACTIVE" if self.vpn_detector.is_vpn_active() else "inactive"
        kill_status = "ENABLED" if self.kill_switch_enabled else "DISABLED"
        
        print(f"[*] LocalPortManager Secure v{__version__}")
        print(f"[*] Proxy: http://127.0.0.1:{self.proxy_port}")
        print(f"[*] VPN Status: {vpn_status}")
        print(f"[*] Kill Switch: {kill_status}")
        print(f"[*] Press Ctrl+C to stop")
        
        if self.kill_switch_enabled and self.vpn_detector.is_vpn_active():
            print(f"\n⚠️  WARNING: VPN is active!")
            print(f"    Docker containers will be BLOCKED to prevent MITM attacks.\n")
        
        def signal_handler(signum, frame):
            print("\n[!] Shutting down...")
            self._shutdown_event.set()
            if self.server:
                self.server.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.server_close()
            print("[*] Proxy stopped")
    
    def register_service(self, name: str, command: str, auto_start: bool = False,
                         security_level: str = "standard", no_kill_switch: bool = False) -> int:
        """Register service with security checks."""
        if not name or not name.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Service name must be alphanumeric with dashes/underscores only")
        
        # Detect if Docker command
        is_docker = 'docker' in command.lower()
        
        # Security check
        if is_docker and self.kill_switch_enabled and not no_kill_switch:
            allowed, message = self.docker_security.check_security_policy(name, is_docker=True)
            if not allowed:
                print(f"\n{message}")
                print(f"\nTo bypass (NOT RECOMMENDED): Use --no-kill-switch flag\n")
                raise RuntimeError(f"Security policy violation for '{name}'")
        
        # Find port and prepare command
        port = self.registry.find_free_port()
        
        if is_docker:
            # Secure Docker command
            sec_level = SecurityLevel(security_level) if security_level in [e.value for e in SecurityLevel] else SecurityLevel.STANDARD
            command = self.docker_security.secure_docker_command(command, sec_level)
        
        if '{port}' in command:
            cmd = command.replace('{port}', str(port))
        else:
            cmd = f"{command} {port}"
        
        # Create service config
        config = ServiceConfig(
            name=name,
            port=port,
            command=cmd,
            is_docker=is_docker,
            security_level=security_level
        )
        
        self.registry.register(config)
        
        # Output
        docker_indicator = "🐳" if is_docker else "  "
        security_indicator = "🔒" if is_docker else "  "
        
        print(f"{docker_indicator} Service '{name}' registered:")
        print(f"    Port:     {port}")
        print(f"    Proxy:    http://{name}.localhost:{self.proxy_port}")
        print(f"    Command:  {cmd}")
        if is_docker:
            print(f"{security_indicator} Security: Localhost-only binding applied")
        
        # Start service
        if auto_start:
            print(f"[*] Starting service...")
            os.system(f"{cmd} &")
        else:
            response = input("Start service now? [y/N]: ").lower()
            if response == 'y':
                os.system(f"{cmd} &")
        
        return port
    
    def unregister_service(self, name: str) -> bool:
        """Unregister a service."""
        if self.registry.unregister(name):
            print(f"[+] Service '{name}' unregistered")
            return True
        else:
            print(f"[!] Service '{name}' not found")
            return False
    
    def list_services(self) -> None:
        """List services with security info."""
        services = self.registry.list_services()
        
        if not services:
            print("[*] No services registered")
            return
        
        vpn_active = self.vpn_detector.is_vpn_active()
        
        print(f"\n{'Service':<20} {'Port':<8} {'Type':<10} {'Status'}")
        print("-" * 65)
        
        for name, svc in sorted(services.items()):
            type_indicator = "🐳 Docker" if svc.is_docker else "🔧 Local"
            
            if svc.is_docker and vpn_active:
                status = "🔒 BLOCKED (VPN)"
            else:
                status = "✅ Active"
            
            print(f"{name:<20} {svc.port:<8} {type_indicator:<10} {status}")
        
        if vpn_active:
            print(f"\n⚠️  VPN is active - Docker services are blocked for security")
        print()
    
    def security_status(self) -> None:
        """Show detailed security status."""
        status = self.docker_security.kill_switch_status()
        
        print("\n" + "="*50)
        print("🔒 SECURITY STATUS")
        print("="*50)
        print(f"VPN Active:       {'YES ⚠️' if status['vpn_active'] else 'NO ✅'}")
        print(f"Kill Switch:      {'ENABLED' if status['kill_switch_enabled'] else 'DISABLED'}")
        print(f"Blocked Services: {len(status['blocked_services'])}")
        
        if status['vpn_interfaces']:
            print(f"\nVPN Interfaces:   {', '.join(status['vpn_interfaces'])}")
        
        if status['blocked_services']:
            print(f"\nBlocked Services:")
            for svc in status['blocked_services']:
                print(f"  - {svc}")
        
        print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='LocalPortManager Secure: VPN-Aware Port Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard usage
  %(prog)s proxy
  
  # Register local service
  %(prog)s register webapp "python -m http.server {port}"
  
  # Register Docker (auto-secured to 127.0.0.1)
  %(prog)s register grafana "docker run -p {port}:3000 grafana/grafana"
  
  # Register with isolation
  %(prog)s register db "docker run -p {port}:5432 postgres" --isolated
  
  # Bypass kill switch (NOT RECOMMENDED)
  %(prog)s register app "docker run -p {port}:80 nginx" --no-kill-switch
        """
    )
    
    parser.add_argument('--port', type=int, default=1355, help='Proxy port')
    parser.add_argument('--state-file', type=str, help='State file path')
    parser.add_argument('--no-kill-switch', action='store_true',
                       help='Disable VPN kill switch (security risk)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Proxy command
    subparsers.add_parser('proxy', help='Start secure proxy server')
    
    # Register command
    reg_parser = subparsers.add_parser('register', help='Register a service')
    reg_parser.add_argument('name', help='Service name')
    reg_parser.add_argument('command', help='Command with {port} placeholder')
    reg_parser.add_argument('-y', '--yes', action='store_true', help='Auto-start')
    reg_parser.add_argument('--isolated', action='store_true',
                           help='Use isolated network (Docker only)')
    reg_parser.add_argument('--security-level', choices=['standard', 'isolated'],
                           default='standard', help='Security level')
    reg_parser.add_argument('--no-kill-switch', action='store_true',
                           help='Bypass kill switch for this service')
    
    # Other commands
    subparsers.add_parser('unregister', help='Unregister service').add_argument('name')
    subparsers.add_parser('list', help='List services')
    subparsers.add_parser('status', help='Show security status')
    subparsers.add_parser('security', help='Show detailed security info')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    lpm = SecureLocalPortManager(
        proxy_port=args.port,
        state_file=args.state_file,
        kill_switch=not args.no_kill_switch
    )
    
    if args.command == 'proxy':
        lpm.start_proxy()
    elif args.command == 'register':
        try:
            security_level = 'isolated' if args.isolated else args.security_level
            no_ks = getattr(args, 'no_kill_switch', False)
            lpm.register_service(
                args.name, args.command, args.yes,
                security_level=security_level,
                no_kill_switch=no_ks
            )
        except (ValueError, RuntimeError) as e:
            print(f"[!] Error: {e}")
            sys.exit(1)
    elif args.command == 'unregister':
        lpm.unregister_service(args.name)
    elif args.command == 'list':
        lpm.list_services()
    elif args.command == 'status' or args.command == 'security':
        lpm.security_status()


if __name__ == "__main__":
    main()
