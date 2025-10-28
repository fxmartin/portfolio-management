# Portfolio Management - Developer Helper Scripts
# Usage: make <command>

.PHONY: help dev dev-rebuild dev-clean prod logs shell-backend shell-db shell-frontend test test-backend test-frontend format backup restore clean

# Default target
help:
	@echo "Portfolio Management - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start all services in development mode"
	@echo "  make dev-tools        - Start all services with PgAdmin (port 5050)"
	@echo "  make dev-rebuild      - Rebuild and start all services"
	@echo "  make dev-clean        - Clean volumes and start fresh"
	@echo ""
	@echo "Production:"
	@echo "  make prod             - Start all services in production mode"
	@echo ""
	@echo "Logs & Monitoring:"
	@echo "  make logs             - Follow logs from all services"
	@echo "  make logs-backend     - Follow backend logs only"
	@echo "  make logs-frontend    - Follow frontend logs only"
	@echo ""
	@echo "Shell Access:"
	@echo "  make shell-backend    - Open bash shell in backend container"
	@echo "  make shell-db         - Open PostgreSQL shell"
	@echo "  make shell-frontend   - Open bash shell in frontend container"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-backend     - Run backend tests with coverage"
	@echo "  make test-frontend    - Run frontend tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           - Format backend and frontend code"
	@echo "  make format-backend   - Format backend Python code with Black"
	@echo "  make format-frontend  - Format frontend TypeScript with Prettier"
	@echo "  make lint             - Run linters on all code"
	@echo ""
	@echo "Database:"
	@echo "  make backup           - Backup PostgreSQL database"
	@echo "  make restore FILE=<file> - Restore database from backup"
	@echo "  make db-reset         - Reset database (WARNING: deletes all data)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            - Stop all services"
	@echo "  make clean-all        - Stop services and remove volumes"
	@echo "  make prune            - Remove unused Docker resources"

# Development commands
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-tools:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile dev-tools up

dev-rebuild:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-clean:
	docker-compose down -v
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production commands
prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

# Shell access
shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U $${POSTGRES_USER:-trader} $${POSTGRES_DB:-portfolio}

shell-frontend:
	docker-compose exec frontend sh

# Testing
test: test-backend test-frontend

test-backend:
	docker-compose exec backend uv run pytest tests/ -v --cov --cov-report=term-missing

test-frontend:
	docker-compose exec frontend npm test -- --run

# Code quality
format: format-backend format-frontend

format-backend:
	docker-compose exec backend uv run black .
	docker-compose exec backend uv run isort .

format-frontend:
	docker-compose exec frontend npm run format

lint:
	docker-compose exec backend uv run ruff check .
	docker-compose exec frontend npm run lint

# Database operations
backup:
	@mkdir -p ./backups
	@echo "Creating backup..."
	docker-compose exec -T postgres pg_dump -U $${POSTGRES_USER:-trader} $${POSTGRES_DB:-portfolio} > ./backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created in ./backups/"

restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=<backup_file>"; \
		exit 1; \
	fi
	@echo "Restoring from $(FILE)..."
	docker-compose exec -T postgres psql -U $${POSTGRES_USER:-trader} $${POSTGRES_DB:-portfolio} < $(FILE)
	@echo "Database restored!"

db-reset:
	@echo "WARNING: This will delete ALL data!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker-compose down -v
	docker-compose up -d

# Cleanup
clean:
	docker-compose down

clean-all:
	docker-compose down -v
	rm -rf ./backups

prune:
	docker system prune -f
	docker volume prune -f

# Install dependencies
install-backend:
	cd backend && uv sync

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend
