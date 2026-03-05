# LocalPortManager 🔌

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-green.svg)](https://github.com/SHAdd0WTAka/LocalportManager)
[![CI](https://github.com/SHAdd0WTAka/LocalportManager/actions/workflows/ci.yml/badge.svg)](https://github.com/SHAdd0WTAka/LocalportManager/actions)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen.svg)](https://github.com/SHAdd0WTAka/LocalportManager)
[![PyPI](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/localportmanager/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A lightweight, zero-dependency local reverse proxy for managing multiple services on dynamic ports. Perfect for development environments, penetration testing frameworks, and microservice development.

## ✨ Features

- **🚀 Zero External Dependencies** - Uses only Python standard library (3.8+)
- **🔄 Dynamic Port Allocation** - Automatically finds available ports (4000-4999)
- **📝 Service Registry** - Persistent JSON-based service mappings
- **🌐 HTTP Reverse Proxy** - Route requests by hostname
- **🔒 Thread-Safe** - Concurrent request handling
- **⚡ Lightweight** - Single file, minimal overhead

## 📋 Requirements

- Python 3.8 or higher
- `*.localhost` DNS resolution (default on most systems including Kali Linux)

## 🚀 Quick Start

### 1. Start the Proxy Server

```bash
python localportmanager.py proxy
```

The proxy starts on `http://127.0.0.1:1355` by default.

### 2. Register a Service

```bash
# Register a simple HTTP server
python localportmanager.py register myapp "python -m http.server {port}"

# Register a custom application
python localportmanager.py register api "uvicorn main:app --port {port}"
```

### 3. Access Your Service

Once registered, access your service through the proxy:

```
http://myapp.localhost:1355
```

## 📖 Usage

### Commands

| Command | Description |
|---------|-------------|
| `proxy` | Start the reverse proxy server |
| `register <name> <command>` | Register a new service |
| `unregister <name>` | Remove a service from registry |
| `list` | List all registered services |
| `status` | Show proxy status and services |

### Options

```bash
# Start proxy on custom port
python localportmanager.py --port 8080 proxy

# Use custom state file
python localportmanager.py --state-file /path/to/registry.json proxy

# Auto-start service without prompting
python localportmanager.py register myapp "cmd" --yes
```

## 🔧 Examples

### Web Development

```bash
# Register multiple frontend applications
python localportmanager.py register frontend-react "npm run dev -- --port {port}"
python localportmanager.py register frontend-vue "npm run serve -- --port {port}"
python localportmanager.py register api "python -m uvicorn api:app --port {port}"
```

Access via:
- `http://frontend-react.localhost:1355`
- `http://frontend-vue.localhost:1355`
- `http://api.localhost:1355`

### Penetration Testing (Zen-AI-Pentest)

```bash
# Register various listeners
python localportmanager.py register listener-01 "nc -lvp {port}"
python localportmanager.py register payload-server "python -m http.server {port}"
python localportmanager.py register api-server "python api.py {port}"
```

### Docker Integration

```bash
# Register Docker container ports
python localportmanager.py register grafana "docker run -p {port}:3000 grafana/grafana"
```

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Client        │────▶│  LocalPortManager │────▶│  Backend Service │
│                 │     │  Proxy (127.0.0.1:1355)  │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │                           │
                              ▼                           ▼
                        ┌─────────────┐             ┌─────────────┐
                        │   Registry  │             │  Dynamic    │
                        │  (JSON)     │             │  Port (4000+)│
                        └─────────────┘             └─────────────┘
```

## 🔌 Service Routing

LocalPortManager routes requests based on the `Host` header:

| Host Header | Routes To |
|-------------|-----------|
| `myapp.localhost:1355` | Service "myapp" |
| `myapp` | Service "myapp" |
| `127.0.0.1:1355/myapp/...` | Service "myapp" (path-based fallback) |

## 📁 Project Structure

```
.
├── localportmanager.py    # Main application (single file)
├── README.md              # This file
├── LICENSE                # MIT License
└── examples/              # Usage examples
```

## 🛠️ Development

### Running Tests

```bash
# Test the module
python -c "import localportmanager; print('OK')"

# Test with verbose output
python localportmanager.py --version
```

### Code Structure

- `PortRegistry` - Manages service/port mappings
- `ReverseProxyHandler` - HTTP request handler
- `LocalPortManager` - Main application class

## ⚠️ Security Notes

- Proxy only binds to `127.0.0.1` (localhost)
- No authentication by design (local development tool)
- State file stored in `/tmp` by default (cleared on reboot)
- For production use, consider adding authentication layer

## 🤝 Integration with Zen-AI-Pentest

LocalPortManager is designed to work seamlessly with [Zen-AI-Pentest](https://github.com/SHAdd0WTAka/Zen-Ai-Pentest):

```python
# Inside Zen-AI-Pentest agent
from localportmanager import LocalPortManager

lpm = LocalPortManager(proxy_port=1355)
port = lpm.register_service("exploit-listener", "nc -lvp {port}")
print(f"Listener accessible at: http://exploit-listener.localhost:1355")
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need for simple service management in penetration testing
- Built for the Zen-AI-Pentest framework
- Zero-dependency philosophy for maximum portability

## 📞 Support

- Issues: [GitHub Issues](https://github.com/SHAdd0WTAka/LocalportManager/issues)
- Author: [@SHAdd0WTAka](https://github.com/SHAdd0WTAka)

---

**Made with ❤️ for the cybersecurity community**
