# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# Python Package Makefile for provide-cicd
# Canonical Makefile for provide.io ecosystem projects

.PHONY: help setup test test-parallel lint lint-fix format format-check typecheck quality quality-all coverage build clean install uninstall lock version docs-setup docs-build docs-serve docs-clean ci-test ci-quality ci-all

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ==============================================================================
# 📖 Help & Information
# ==============================================================================

help: ## Show this help message
	@echo '$(BLUE)Available targets:$(NC)'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

version: ## Show package version
	@cat VERSION

# ==============================================================================
# 🔧 Setup & Environment
# ==============================================================================

setup: ## Initialize development environment
	@echo '$(BLUE)Setting up development environment...$(NC)'
	uv sync
	@echo '$(GREEN)✓ Development environment ready$(NC)'
	@echo '$(YELLOW)→ Run "make setup-pre-commit" to install git hooks$(NC)'

setup-pre-commit: ## Install pre-commit hooks from central config
	@echo '$(BLUE)Setting up pre-commit hooks...$(NC)'
	@if ! command -v pre-commit >/dev/null 2>&1; then \
		echo '$(YELLOW)Installing pre-commit...$(NC)'; \
		uv pip install pre-commit; \
	fi
	@if [ ! -f .pre-commit-config.yaml ]; then \
		echo '$(YELLOW)Installing standard pre-commit config...$(NC)'; \
		if [ -f configs/pre-commit-config.yaml ]; then \
			cp configs/pre-commit-config.yaml .pre-commit-config.yaml; \
		else \
			echo '$(RED)Warning: configs/pre-commit-config.yaml not found$(NC)'; \
			echo '$(RED)Create .pre-commit-config.yaml manually$(NC)'; \
		fi; \
	else \
		echo '$(GREEN)Pre-commit config already exists$(NC)'; \
	fi
	@pre-commit install
	@pre-commit install --hook-type commit-msg
	@echo '$(GREEN)✓ Pre-commit hooks installed$(NC)'

# ==============================================================================
# 🧪 Testing
# ==============================================================================

test: ## Run all tests
	@echo '$(BLUE)Running tests...$(NC)'
	uv run pytest
	@echo '$(GREEN)✓ Tests complete$(NC)'

test-parallel: ## Run tests in parallel
	@echo '$(BLUE)Running tests in parallel...$(NC)'
	uv run pytest -n auto
	@echo '$(GREEN)✓ Tests complete$(NC)'

coverage: ## Run tests with coverage report
	@echo '$(BLUE)Running tests with coverage...$(NC)'
	uv run pytest --cov=src/provide/cicd --cov-report=html --cov-report=term-missing
	@echo '$(GREEN)✓ Coverage report generated in htmlcov/$(NC)'

coverage-xml: ## Run tests with XML coverage for CI
	@echo '$(BLUE)Running tests with XML coverage for CI...$(NC)'
	uv run pytest --cov=src/provide/cicd --cov-report=xml --cov-report=term
	@echo '$(GREEN)✓ XML coverage report generated$(NC)'

# ==============================================================================
# 🔍 Code Quality
# ==============================================================================

lint: ## Run ruff check
	@echo '$(BLUE)Running ruff check...$(NC)'
	uv run ruff check src/ tests/
	@echo '$(GREEN)✓ Linting complete$(NC)'

lint-fix: ## Run ruff check with automatic fixes
	@echo '$(BLUE)Running ruff check --fix...$(NC)'
	uv run ruff check --fix --unsafe-fixes src/ tests/
	@echo '$(GREEN)✓ Linting with fixes complete$(NC)'

format: ## Format code with ruff
	@echo '$(BLUE)Formatting code...$(NC)'
	uv run ruff format src/ tests/
	@echo '$(GREEN)✓ Code formatted$(NC)'

format-check: ## Check code formatting without modifying
	@echo '$(BLUE)Checking code formatting...$(NC)'
	uv run ruff format --check src/ tests/
	@echo '$(GREEN)✓ Format check complete$(NC)'

typecheck: ## Run mypy type checker
	@echo '$(BLUE)Running mypy type checker...$(NC)'
	uv run mypy src/
	@echo '$(GREEN)✓ Type checking complete$(NC)'

quality: ## Run lint + typecheck
	@$(MAKE) lint
	@$(MAKE) typecheck

quality-all: ## Run format-check + lint + typecheck + test
	@$(MAKE) format-check
	@$(MAKE) lint
	@$(MAKE) typecheck
	@$(MAKE) test

# ==============================================================================
# 📦 Building & Distribution
# ==============================================================================

build: ## Build package distribution
	@echo '$(BLUE)Building package...$(NC)'
	uv build
	@echo '$(GREEN)✓ Package built in dist/$(NC)'

clean: ## Clean build artifacts and caches
	@echo '$(BLUE)Cleaning build artifacts and caches...$(NC)'
	rm -rf build/ dist/ *.egg-info/ .eggs/
	rm -rf workenv/ .mypy_cache/ .pytest_cache/ .ruff_cache/ htmlcov/ .coverage site/ .provide/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo '$(GREEN)✓ Cleanup complete$(NC)'

install: ## Install package in development mode
	@echo '$(BLUE)Installing package in development mode...$(NC)'
	uv pip install -e .
	@echo '$(GREEN)✓ Package installed$(NC)'

uninstall: ## Uninstall package
	@echo '$(BLUE)Uninstalling package...$(NC)'
	uv pip uninstall provide-cicd
	@echo '$(GREEN)✓ Package uninstalled$(NC)'

lock: ## Update dependency lock file
	@echo '$(BLUE)Updating dependency lock file...$(NC)'
	uv lock
	@echo '$(GREEN)✓ Lock file updated$(NC)'

# ==============================================================================
# 📚 Documentation
# ==============================================================================

docs-setup: ## Extract base mkdocs config from provide-foundry
	@echo '$(BLUE)Setting up documentation infrastructure...$(NC)'
	@python -c "from provide.foundry.config import extract_base_mkdocs; from pathlib import Path; extract_base_mkdocs(Path('.'))"
	@echo '$(GREEN)✓ Documentation infrastructure ready$(NC)'

docs-build: docs-setup ## Build documentation
	@echo '$(BLUE)Building documentation...$(NC)'
	uv run mkdocs build
	@echo '$(GREEN)✓ Documentation built in site/$(NC)'

docs-serve: docs-setup ## Serve documentation locally
	@echo '$(BLUE)Serving documentation on http://127.0.0.1:11012$(NC)'
	uv run mkdocs serve -a 127.0.0.1:11012

docs-clean: ## Clean documentation artifacts
	@echo '$(BLUE)Cleaning documentation artifacts...$(NC)'
	rm -rf site/ .provide/
	@echo '$(GREEN)✓ Documentation cleanup complete$(NC)'

# ==============================================================================
# 🤖 CI/CD Targets
# ==============================================================================

ci-test: ## CI testing target (parallel tests + coverage)
	@$(MAKE) test-parallel
	@$(MAKE) coverage-xml

ci-quality: ## CI quality target (format-check + lint + typecheck)
	@$(MAKE) format-check
	@$(MAKE) lint
	@$(MAKE) typecheck

ci-all: ## CI complete pipeline (quality + test + build)
	@$(MAKE) ci-quality
	@$(MAKE) ci-test
	@$(MAKE) build

# 🧰⚙️🔚
