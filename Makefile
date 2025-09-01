# ---- dhis2kit Makefile ----
# Common workflows:
#   make help           # show all targets
#   make venv           # create virtualenv
#   make install        # install deps + editable package
#   make test           # run test suite
#   make demo           # run "python -m dhis2kit"
#   make examples       # run example scripts
#   make build          # build sdist+wheel in dist/
#   make clean          # remove caches and build artifacts
#   make distclean      # also remove venv
#   make format         # run black (optional)
#   make lint           # run ruff lint (optional)
#   make typecheck      # run mypy (optional)
#   make release VERSION=0.6.1   # tag & push a release (git)

# --- Config ---
VENV ?= .venv
PY   ?= $(VENV)/bin/python
PIP  ?= $(VENV)/bin/pip

PKG_NAME := dhis2kit

# Detect platform-specific venv python path if needed
ifeq ($(OS),Windows_NT)
	PY := $(VENV)/Scripts/python.exe
	PIP := $(VENV)/Scripts/pip.exe
endif

.PHONY: help venv install test demo examples build clean distclean format lint typecheck release

help:
	@echo ""
	@echo "dhis2kit Makefile targets:"
	@echo "  make venv        - create virtualenv in $(VENV)"
	@echo "  make install     - install deps (requirements.txt) + editable package"
	@echo "  make test        - run test suite (pytest)"
	@echo "  make demo        - run demo: python -m $(PKG_NAME)"
	@echo "  make examples    - run examples in ./examples"
	@echo "  make build       - build wheel + sdist into ./dist"
	@echo "  make clean       - remove build artifacts and caches"
	@echo "  make distclean   - clean + remove $(VENV)"
	@echo "  make format      - run black (if installed)"
	@echo "  make lint        - run ruff (if installed)"
	@echo "  make typecheck   - run mypy (if installed)"
	@echo "  make release VERSION=X.Y.Z - tag & push a release"
	@echo ""

# Create virtual environment
venv:
	@test -d $(VENV) || python -m venv $(VENV)
	@echo "Virtualenv ready at $(VENV)"

# Install requirements + package in editable mode
install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

# Run tests with pytest
test:
	$(PY) -m pytest -q

# Run CLI demo
demo:
	$(PY) -m $(PKG_NAME)

# Run example scripts
examples:
	$(PY) examples/example_crud_metadata.py
	$(PY) examples/example_crud_data.py
	$(PY) examples/example_analytics.py

# Build wheel + sdist
build:
	$(PIP) install --upgrade build
	$(PY) -m build

# Clean build artifacts and caches
clean:
	@echo "Cleaning build artifacts and caches..."
	@rm -rf build/ dist/ *.egg-info
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} \;
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov

# Clean + remove venv
distclean: clean
	@echo "Removing virtualenv $(VENV)..."
	@rm -rf $(VENV)

# Optional: code format with black
format:
	@if [ -x "$$(command -v $(PY))" ]; then true; else echo "Missing venv: run 'make install' first"; exit 1; fi
	@$(PIP) show black >/dev/null 2>&1 || (echo "Installing black..." && $(PIP) install black)
	@$(PY) -m black dhis2kit tests examples

# Optional: lint with ruff
lint:
	@if [ -x "$$(command -v $(PY))" ]; then true; else echo "Missing venv: run 'make install' first"; exit 1; fi
	@$(PIP) show ruff >/dev/null 2>&1 || (echo "Installing ruff..." && $(PIP) install ruff)
	@$(PY) -m ruff check dhis2kit tests examples

# Optional: type-check with mypy
typecheck:
	@if [ -x "$$(command -v $(PY))" ]; then true; else echo "Missing venv: run 'make install' first"; exit 1; fi
	@$(PIP) show mypy >/dev/null 2>&1 || (echo "Installing mypy..." && $(PIP) install mypy)
	@$(PY) -m mypy dhis2kit

# Tag and push a release
# Usage: make release VERSION=0.6.1
release:
	@if [ -z "$(VERSION)" ]; then echo "ERROR: VERSION is required (e.g., make release VERSION=0.6.1)"; exit 1; fi
	@git diff --quiet || (echo "ERROR: Git working tree is dirty. Commit or stash changes first."; exit 1)
	@echo "Running tests before release..."
	$(PY) -m pytest -q
	@echo "Building distributions..."
	$(PIP) install --upgrade build
	$(PY) -m build
	@echo "Tagging release v$(VERSION)..."
	git tag v$(VERSION)
	git push origin main
	git push origin v$(VERSION)
	@echo "Release v$(VERSION) pushed."
