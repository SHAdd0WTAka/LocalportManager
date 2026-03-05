.PHONY: help install test test-cov lint format clean build publish

help:
	@echo "LocalPortManager - Available commands:"
	@echo "  make install    - Install package in development mode"
	@echo "  make test       - Run tests"
	@echo "  make test-cov   - Run tests with coverage (80%+ required)"
	@echo "  make lint       - Run linting (flake8, black, isort)"
	@echo "  make format     - Format code with black and isort"
	@echo "  make type       - Run type checking with mypy"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make build      - Build package for distribution"
	@echo "  make publish    - Publish to PyPI"

install:
	pip install -e ".[dev]"

test:
	pytest -v

test-cov:
	pytest --cov=localportmanager --cov-report=html --cov-report=term --cov-fail-under=80

lint:
	flake8 localportmanager.py tests/ --max-line-length=100 --ignore=E203,W503
	black --check --diff localportmanager.py tests/
	isort --check --diff localportmanager.py tests/

format:
	black localportmanager.py tests/
	isort localportmanager.py tests/

type:
	mypy localportmanager.py --ignore-missing-imports

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

build: clean
	python -m build

publish: build
	twine check dist/*
	twine upload dist/*

ci: lint type test-cov
	@echo "All CI checks passed!"
