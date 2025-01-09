# Makefile for Python project using .venv and pytest

.PHONY: test cleanup setup

# Path to the virtual environment
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Ensure virtual environment is set up and run tests
test: setup
	$(PYTHON) -m pytest tests/

# Create the virtual environment if it doesn't exist and install dependencies
setup:
	@if [ ! -d "$(VENV)" ]; then \
		python3 -m venv $(VENV); \
		$(PIP) install --upgrade pip; \
	fi; \
	$(PIP) install pytest
