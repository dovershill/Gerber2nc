.PHONY: help venv install install-dev test lint type-check clean clean-test clean-pyc clean-build run

# Default Python interpreter
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin

help:
	@echo "Gerber2nc Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make venv          - Create Python virtual environment"
	@echo "  make install       - Install package dependencies"
	@echo "  make install-dev   - Install package with dev dependencies"
	@echo "  make test          - Run tests with pytest"
	@echo "  make test-cov      - Run tests with coverage report"
	@echo "  make lint          - Run all linting checks (type-check)"
	@echo "  make type-check    - Run mypy type checking"
	@echo "  make clean         - Remove all build, test, and Python artifacts"
	@echo "  make clean-test    - Remove test and coverage artifacts"
	@echo "  make clean-pyc     - Remove Python file artifacts"
	@echo "  make clean-build   - Remove build artifacts"
	@echo ""
	@echo "Example workflow:"
	@echo "  make venv && source venv/bin/activate && make install-dev && make test"

venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created in ./$(VENV)"
	@echo "Activate it with: source $(VENV_BIN)/activate"

install:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Installing package dependencies..."
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -e .
	@echo "Installation complete!"

install-dev:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Error: Virtual environment not found. Run 'make venv' first."; \
		exit 1; \
	fi
	@echo "Installing package with dev dependencies..."
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -e ".[dev]"
	@echo "Dev installation complete!"

test:
	@if [ ! -f "$(VENV_BIN)/pytest" ]; then \
		echo "Error: pytest not found. Run 'make install-dev' first."; \
		exit 1; \
	fi
	@echo "Running tests..."
	$(VENV_BIN)/pytest

test-cov:
	@if [ ! -f "$(VENV_BIN)/pytest" ]; then \
		echo "Error: pytest not found. Run 'make install-dev' first."; \
		exit 1; \
	fi
	@echo "Running tests with coverage..."
	$(VENV_BIN)/pytest --cov=gerber2nc --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

type-check:
	@if [ ! -f "$(VENV_BIN)/mypy" ]; then \
		echo "Error: mypy not found. Run 'make install-dev' first."; \
		exit 1; \
	fi
	@echo "Running mypy type checking..."
	$(VENV_BIN)/mypy gerber2nc

lint: type-check
	@echo "All linting checks passed!"

clean: clean-build clean-pyc clean-test
	@echo "Cleaned all artifacts!"

clean-build:
	@echo "Removing build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	@echo "Removing Python file artifacts..."
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

clean-test:
	@echo "Removing test and coverage artifacts..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/

run:
	@echo "Run with: $(VENV_BIN)/gerber2nc <path-to-project>"
	@echo "Or: $(VENV_BIN)/python -m gerber2nc <path-to-project>"
