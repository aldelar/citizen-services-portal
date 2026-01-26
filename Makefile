# Citizen Services Portal - Development Makefile
#
# Common commands for local development and testing.
# Run `make help` to see all available commands.

.PHONY: help dev dev-web dev-mcp docker-up docker-down clean

# Default target
help:
	@echo ""
	@echo "🏛️  Citizen Services Portal - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start all services (MCP + Agent + Web)"
	@echo "  make dev-mcp      - Start only MCP servers"
	@echo "  make dev-web      - Start only the web application"
	@echo ""
	@echo "Docker Development (production-like):"
	@echo "  make docker-up    - Start all services in Docker"
	@echo "  make docker-down  - Stop all Docker services"
	@echo "  make docker-logs  - Follow Docker logs"
	@echo "  make docker-build - Rebuild all Docker images"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-mcp     - Run MCP server tests"
	@echo "  make test-web     - Run web app tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean up virtual environments and caches"
	@echo "  make sync         - Sync all dependencies"
	@echo ""

# ============================================================================
# Development
# ============================================================================

dev:
	@echo "🚀 Starting all services (MCP + Agent + Web)..."
	cd scripts && uv run python dev-local.py

dev-web:
	@echo "🌐 Starting web application only..."
	cd scripts && uv run python dev-local.py --web-only

dev-mcp:
	@echo "📡 Starting MCP servers only..."
	cd scripts && uv run python dev-local.py --mcp-only

# ============================================================================
# Docker Development
# ============================================================================

docker-up:
	@echo "🐳 Starting all services in Docker..."
	docker compose -f docker-compose.dev.yml up

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker compose -f docker-compose.dev.yml down

docker-logs:
	@echo "📋 Following Docker logs..."
	docker compose -f docker-compose.dev.yml logs -f

docker-build:
	@echo "🔨 Rebuilding Docker images..."
	docker compose -f docker-compose.dev.yml build

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	docker compose -f docker-compose.dev.yml down -v --rmi local

# ============================================================================
# Testing
# ============================================================================

test:
	@echo "🧪 Running all tests..."
	cd src/mcp-servers/ladbs && uv run pytest
	cd src/mcp-servers/ladwp && uv run pytest
	cd src/mcp-servers/lasan && uv run pytest
	cd src/web-app && uv run pytest

test-mcp:
	@echo "🧪 Running MCP server tests..."
	cd src/mcp-servers/ladbs && uv run pytest
	cd src/mcp-servers/ladwp && uv run pytest
	cd src/mcp-servers/lasan && uv run pytest

test-web:
	@echo "🧪 Running web app tests..."
	cd src/web-app && uv run pytest

# ============================================================================
# Utilities
# ============================================================================

sync:
	@echo "📦 Syncing all dependencies..."
	cd src/mcp-servers/ladbs && uv sync
	cd src/mcp-servers/ladwp && uv sync
	cd src/mcp-servers/lasan && uv sync
	cd src/mcp-servers/reporting && uv sync
	cd src/web-app && uv sync

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"
