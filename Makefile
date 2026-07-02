# Variables
PYTHON := poetry run python
PYTEST := poetry run pytest
RUFF := poetry run ruff
MYPY := poetry run mypy

.PHONY: install format lint test train api clean help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies via Poetry and setup pre-commit hooks
	poetry install
	# poetry run pre-commit install (Uncomment if using pre-commit)

format: ## Format code using Ruff (replaces Black & isort)
	$(RUFF) format .
	$(RUFF) check --fix .

lint: ## Run static type checking and linting
	@echo "Running Ruff Linter..."
	$(RUFF) check .
	@echo "Running Mypy Type Checker..."
	$(MYPY) qts_core/ data_platform/

test: ## Run unit and integration tests with coverage
	$(PYTEST) tests/unit/
	# $(PYTEST) tests/integration/ (Run integrations separately to save time)

train: ## Launch a localized RL training loop (for testing)
	$(PYTHON) qts_core/models/train.py --config config/local_ppo.yaml

api: ## Start the FastAPI telemetry and dashboard backend
	poetry run uvicorn dashboard.backend.main:app --reload --port 8000

dashboard: ## Start the React/Next.js frontend dashboard
	cd dashboard/frontend && npm install && npm run dev

clean: ## Remove cached files and pycache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov/