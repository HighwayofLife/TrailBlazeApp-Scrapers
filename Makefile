.PHONY: build up down restart test test-dev format lint logs clean update-deps init setup-reports setup help test-docker test-docker-dev test-docker-cov

# Colors for terminal output
BLUE=\033[0;34m
GREEN=\033[0;32m
RED=\033[0;31m
YELLOW=\033[0;33m
PURPLE=\033[0;35m
CYAN=\033[0;36m
NC=\033[0m # No Color

# Default target
## Display help information about available targets
help:
	@echo "${BLUE}TrailBlazeApp-Scrapers${NC} - Web scraping framework for endurance riding events"
	@echo ""
	@echo "${CYAN}Available commands:${NC}"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}make %-15s${NC} %s\n", $$1, $$2}'

# Build Docker containers
build: ## Build the Docker containers
	@echo "${YELLOW}Building Docker containers...${NC}"
	docker-compose build
	@echo "${GREEN}✓ Docker containers built successfully${NC}"

# Start Docker containers
up: ## Start the Docker containers in the background
	@echo "${YELLOW}Starting Docker containers...${NC}"
	docker-compose up -d
	@echo "${GREEN}✓ Docker containers started successfully${NC}"
	@echo "${BLUE}ℹ To view logs, run:${NC} make logs"

# Stop Docker containers
down: ## Stop the Docker containers
	@echo "${YELLOW}Stopping Docker containers...${NC}"
	docker-compose down
	@echo "${GREEN}✓ Docker containers stopped successfully${NC}"

# Restart Docker containers
restart: ## Restart the Docker containers
	@echo "${YELLOW}Restarting Docker containers...${NC}"
	docker-compose restart
	@echo "${GREEN}✓ Docker containers restarted successfully${NC}"

# Run all tests
test: ## Run all tests
	@echo "${YELLOW}Running tests...${NC}"
	docker-compose run --rm app python -m pytest
	@echo "${GREEN}✓ Tests completed${NC}"

# Run tests with detailed output
test-dev: ## Run tests in development mode (with detailed output)
	@echo "${YELLOW}Running tests in development mode...${NC}"
	docker-compose run --rm app python -m pytest -v
	@echo "${GREEN}✓ Tests completed${NC}"

# Run tests in the test container
test-docker: ## Run tests in the dedicated test container (following TDD principles)
	@echo "${YELLOW}Running tests in dedicated test container...${NC}"
	docker-compose run --rm test python -m pytest
	@echo "${GREEN}✓ Tests completed${NC}"

# Run tests in the test container with detailed output
test-docker-dev: ## Run tests in the dedicated test container with detailed output (following TDD principles)
	@echo "${YELLOW}Running tests in dedicated test container (development mode)...${NC}"
	docker-compose run --rm test python -m pytest -v
	@echo "${GREEN}✓ Tests completed${NC}"

# Run tests with coverage report in test container
test-docker-cov: ## Run tests with coverage report in the dedicated test container
	@echo "${YELLOW}Running tests with coverage in dedicated test container...${NC}"
	docker-compose run --rm test python -m pytest --cov=app --cov-report=term --cov-report=html
	@echo "${GREEN}✓ Tests with coverage completed${NC}"
	@echo "${BLUE}ℹ Coverage report available in htmlcov/index.html${NC}"

# Format code
format: ## Format code with Black
	@echo "${YELLOW}Formatting code with Black...${NC}"
	docker-compose run --rm app python -m black app tests
	@echo "${GREEN}✓ Code formatting completed${NC}"

# Run linting
lint: ## Run linting with flake8
	@echo "${YELLOW}Running linting with flake8...${NC}"
	docker-compose run --rm app python -m flake8 app tests
	@echo "${GREEN}✓ Linting completed${NC}"

# View Docker container logs
logs: ## View Docker container logs
	@echo "${CYAN}Showing container logs (Ctrl+C to exit)...${NC}"
	docker-compose logs -f

# Clean up cache and test artifacts
clean: ## Remove cache files and test artifacts
	@echo "${YELLOW}Cleaning up cache files and test artifacts...${NC}"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name "*.pyc" -delete
	@echo "${GREEN}✓ Cleanup completed${NC}"

# Update dependencies
update-deps: ## Update dependencies in requirements.txt
	@echo "${YELLOW}Updating dependencies...${NC}"
	docker-compose run --rm app pip freeze > requirements.txt
	@echo "${GREEN}✓ Dependencies updated in requirements.txt${NC}"

# Create initial .env file from sample if it doesn't exist
init: ## Create .env file from .env.sample if it doesn't exist
	@if [ ! -f .env ]; then \
		echo "${YELLOW}Creating .env file from .env.sample...${NC}"; \
		cp .env.sample .env; \
		echo "${GREEN}✓ Created .env file${NC}"; \
		echo "${RED}⚠ Please edit .env file with your actual settings${NC}"; \
	else \
		echo "${BLUE}ℹ .env file already exists${NC}"; \
	fi

# Create reports directory if it doesn't exist
setup-reports: ## Create reports directory for test results
	@if [ ! -d reports ]; then \
		echo "${YELLOW}Creating reports directory...${NC}"; \
		mkdir -p reports; \
		echo "${GREEN}✓ Created reports directory${NC}"; \
	else \
		echo "${BLUE}ℹ Reports directory already exists${NC}"; \
	fi

# Setup project (runs init and setup-reports)
setup: init setup-reports ## Setup project (initialize .env and reports directory)
	@echo "${GREEN}✓ Project setup completed${NC}"
	@echo "${BLUE}ℹ Next steps:${NC}"
	@echo "  1. Edit .env file with your settings"
	@echo "  2. Run 'make build' to build containers"
	@echo "  3. Run 'make up' to start the application"
