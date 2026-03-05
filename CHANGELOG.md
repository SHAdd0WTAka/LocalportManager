# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-05

### Added
- Initial release of LocalPortManager
- Zero-dependency local reverse proxy
- Dynamic port allocation (4000-4999)
- Service registry with persistent JSON state
- HTTP reverse proxy with Host header routing
- Support for all HTTP methods (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)
- Path-based routing fallback
- CLI with commands: proxy, register, unregister, list, status
- Python API for programmatic usage
- Thread-safe operations
- Signal handling for graceful shutdown
- Comprehensive test suite (80%+ coverage)
- CI/CD with GitHub Actions
- PyPI package support
- MIT License

### Features
- **proxy**: Start the reverse proxy server
- **register**: Register a service with dynamic port
- **unregister**: Remove a service from registry
- **list**: List all registered services
- **status**: Show proxy status and services
- Custom state file support
- Custom proxy port configuration
- Auto-start services with `--yes` flag
- Service name validation

[1.0.0]: https://github.com/SHAdd0WTAka/LocalportManager/releases/tag/v1.0.0
