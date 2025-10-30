.PHONY: help install run format check clean install-service uninstall-service service-status

help:
	@echo "MacPing - Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make run               - Run the application"
	@echo "  make check             - Check code quality (use before committing)"
	@echo "  make format            - Auto-fix and format code (use during development)"
	@echo "  make install-service   - Install LaunchAgent to run at login"
	@echo "  make uninstall-service - Remove LaunchAgent"
	@echo "  make service-status    - Check if service is running"
	@echo "  make clean             - Remove temporary files and caches"

install:
	uv sync --extra dev

run:
	uv run macping.py

# Check code quality without modifying files
# Use this before committing or in CI
check:
	uv run ruff check macping.py
	uv run ruff format --check macping.py

# Auto-fix linting issues and format code
# Use this during development to clean up code
format:
	uv run ruff check --fix --unsafe-fixes macping.py
	uv run ruff format macping.py

# LaunchAgent configuration
PLIST_NAME = com.macping.plist
PLIST_TEMPLATE = com.macping.plist.template
PLIST_PATH = $(HOME)/Library/LaunchAgents/$(PLIST_NAME)
PROJECT_DIR = $(shell pwd)
UV_PATH = $(shell which uv)

# Install LaunchAgent to run MacPing at login
install-service:
	@echo "Installing LaunchAgent..."
	@mkdir -p $(HOME)/Library/LaunchAgents
	@sed -e 's|{{UV_PATH}}|$(UV_PATH)|g' \
	     -e 's|{{PROJECT_DIR}}|$(PROJECT_DIR)|g' \
	     -e 's|{{HOME}}|$(HOME)|g' \
	     $(PLIST_TEMPLATE) > $(PLIST_PATH)
	@launchctl load $(PLIST_PATH)
	@echo "LaunchAgent installed and loaded!"
	@echo "MacPing will now start automatically at login."
	@echo "Logs: ~/Library/Logs/macping.log"

# Remove LaunchAgent
uninstall-service:
	@echo "Uninstalling LaunchAgent..."
	@launchctl unload $(PLIST_PATH) 2>/dev/null || true
	@rm -f $(PLIST_PATH)
	@echo "LaunchAgent removed."

# Check if service is running
service-status:
	@echo "Checking MacPing service status..."
	@launchctl list | grep com.macping || echo "Service is not running"

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
