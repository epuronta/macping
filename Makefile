.PHONY: help install run format check clean

help:
	@echo "MacPing - Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make run        - Run the application"
	@echo "  make check      - Check code quality (use before committing)"
	@echo "  make format     - Auto-fix and format code (use during development)"
	@echo "  make clean      - Remove temporary files and caches"

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
