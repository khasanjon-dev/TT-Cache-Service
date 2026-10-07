.DEFAULT_GOAL := help

PYTHON := .venv/bin/python
RUFF := .venv/bin/ruff

POSTGRES_PASSWORD ?= cache_user_dev
TEST_DATABASE_URL := postgresql+psycopg://cache_user:$(POSTGRES_PASSWORD)@localhost:5432/cache_test

.PHONY: install dev test lint format check docker-up docker-down docker-test clean help

install: ## Install project dependencies
	python3.12 -m venv .venv
	$(PYTHON) -m pip install -e '.[dev]'

dev: ## Start PostgreSQL and run the API locally
	@docker compose up -d postgres
	@$(PYTHON) -m app.init_db
	@$(PYTHON) -m uvicorn app.main:app --reload

test: ## Run all tests against PostgreSQL
	@$(MAKE) docker-test

lint: ## Run Ruff lint checks
	@$(RUFF) check .

format: ## Format Python files with Ruff
	@$(RUFF) format .

check: lint ## Run lint, format checks, and tests
	@$(RUFF) format --check .
	@$(MAKE) test

docker-up: ## Build and start all Docker services
	@docker compose up --build -d

docker-down: ## Stop Docker services
	@docker compose down

docker-test: ## Run tests using a dedicated PostgreSQL test database
	@docker compose up -d postgres
	@if ! docker compose exec -T postgres psql -U cache_user -d cache_db -tAc
		"SELECT 1 FROM pg_database WHERE datname = 'cache_test'" | grep -q 1; then
		docker compose exec -T postgres createdb -U cache_user cache_test;
	fi
	@TEST_DATABASE_URL='$(TEST_DATABASE_URL)' $(PYTHON) -m pytest

clean: ## Remove Python and tool caches
	@rm -rf .pytest_cache .ruff_cache build dist
	@find app tests -type d -name __pycache__ -prune -exec rm -rf {} +

help: ## Show available commands
	@echo "Usage: make <target>"
	@echo ""
	@echo "Commands:"
	@echo "  install        Install project dependencies"
	@echo "  dev            Start PostgreSQL and run the API"
	@echo "  test           Run all tests against PostgreSQL"
	@echo "  lint           Run Ruff lint checks"
	@echo "  format         Format Python files"
	@echo "  check          Run lint, formatting checks, and tests"
	@echo "  docker-up      Build and start Docker services"
	@echo "  docker-down    Stop Docker services"
	@echo "  docker-test    Run tests with PostgreSQL"
	@echo "  clean          Remove caches and build artifacts"
	@echo "  help           Show this help"