# Storefront Agent Makefile

.PHONY: help install install-dev test test-cov lint format clean build publish docs

help: ## Show this help message
	@echo "Storefront Agent - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in production mode
	pip install -e .

install-dev: ## Install the package in development mode with dev dependencies
	pip install -e ".[dev,test,docs]"

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=src/storefront_agent --cov-report=html --cov-report=term

lint: ## Run linting
	flake8 src/ tests/ examples/
	mypy src/

format: ## Format code
	black src/ tests/ examples/
	isort src/ tests/ examples/

format-check: ## Check code formatting
	black --check src/ tests/ examples/
	isort --check-only src/ tests/ examples/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean ## Build the package
	python -m build

publish: build ## Publish to PyPI
	twine upload dist/*

docs: ## Build documentation
	cd docs && make html

docs-serve: ## Serve documentation locally
	cd docs && python -m http.server 8000

run: ## Run the agent in interactive mode
	python main.py

run-example: ## Run example usage
	python examples/example_usage.py

test-install: ## Test installation
	python tests/test_installation.py

setup: ## Initial setup
	python setup.py

check: format-check lint test ## Run all checks

pre-commit: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

# Development shortcuts
dev-install: install-dev pre-commit ## Complete development setup

quick-test: ## Quick test run
	pytest tests/ -x -v --tb=short

watch-test: ## Run tests in watch mode
	pytest-watch tests/

# Docker commands (if needed)
docker-build: ## Build Docker image
	docker build -t storefront-agent .

docker-run: ## Run Docker container
	docker run -it --rm storefront-agent

# Environment setup
env-create: ## Create .env file from template
	cp env_example.txt .env

env-check: ## Check environment configuration
	python -c "from src.storefront_agent.config import config; print('Configuration loaded successfully')"
