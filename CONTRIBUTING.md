# Contributing to LocalPortManager

Thank you for your interest in contributing to LocalPortManager!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/LocalportManager.git
   cd LocalportManager
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   # Or manually:
   pip install pytest pytest-cov black isort flake8 mypy bandit
   ```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=localportmanager --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

## Code Style

We use:
- **black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black localportmanager.py tests/

# Sort imports
isort localportmanager.py tests/

# Run linter
flake8 localportmanager.py tests/

# Type check
mypy localportmanager.py
```

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Make your changes and add tests

3. Ensure tests pass and coverage is ≥80%:
   ```bash
   pytest --cov=localportmanager --cov-fail-under=80
   ```

4. Commit your changes:
   ```bash
   git commit -am "Add some feature"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/my-new-feature
   ```

6. Open a Pull Request

## Commit Message Guidelines

Use conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or correcting tests
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example:
```
feat: Add support for custom port ranges

- Implement find_free_port with configurable range
- Add CLI option --port-range
- Add tests for new functionality
```

## Reporting Issues

When reporting issues, please include:

1. Python version
2. Operating system
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Error messages or logs

## Code of Conduct

Be respectful and constructive in all interactions.
