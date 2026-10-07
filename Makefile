.DEFAULT_GOAL := help

PYTHON := .venv/bin/python
RUFF := .venv/bin/ruff

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
	@docker compose exec -T postgres sh -c 'createdb -U "$$POSTGRES_USER" "$$1" >/dev/null 2>&1 || psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -lqt | grep -q "$$1"' sh cache_test
	@export TEST_DATABASE_URL="$$(docker compose config --format json | $(PYTHON) -c 'import json, sys; from sqlalchemy.engine import URL; env = json.load(sys.stdin)["services"]["postgres"]["environment"]; print(URL.create("postgresql+psycopg", username=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"], host="localhost", port=5432, database="cache_test").render_as_string(hide_password=False))')" && $(PYTHON) -m pytest

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
