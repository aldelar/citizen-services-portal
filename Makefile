# Citizen Services Portal - Development Makefile
#
# Common commands for local development and testing.
# Run `make help` to see all available commands.

.PHONY: help dev dev-web dev-mcp dev-setup rbac docker-up docker-down clean

# Default target
help:
	@echo ""
	@echo "🏛️  Citizen Services Portal - Development Commands"
	@echo "=================================================="
	@echo ""
	@echo "Setup:"
	@echo "  make dev-setup    - Set up dev environment (RBAC, etc.)"
	@echo "  make rbac         - Set up CosmosDB RBAC for current user"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start all services (MCP + Agent + Web)"
	@echo "  make dev-mcp      - Start only MCP servers"
	@echo "  make dev-agent    - Start only CSP Agent (expects MCP on 8001-8004)"
	@echo "  make dev-web      - Start only the web application"
	@echo ""
	@echo "Docker Development (production-like):"
	@echo "  make docker-up    - Start all services in Docker"
	@echo "  make docker-down  - Stop all Docker services"
	@echo "  make docker-logs  - Follow Docker logs"
	@echo "  make docker-build - Rebuild all Docker images"
	@echo ""
	@echo "Observability:"
	@echo "  make aspire-start - Start Aspire Dashboard for OTEL traces"
	@echo "  make aspire-stop  - Stop Aspire Dashboard"
	@echo "  make aspire-logs  - Follow Aspire Dashboard logs"
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run all tests"
	@echo "  make test-mcp          - Run MCP server unit tests"
	@echo "  make test-mcp-integration - Run MCP integration tests (AI Search + CosmosDB)"
	@echo "  make test-mcp-deployed - Run MCP deployed server tests"
	@echo "  make test-mcp-full     - Run full MCP test suite (unit + integration + deployed)"
	@echo "  make test-ladbs        - Run full LADBS test suite"
	@echo "  make test-ladwp        - Run full LADWP test suite"
	@echo "  make test-lasan        - Run full LASAN test suite"
	@echo "  make test-csp          - Run full CSP test suite"
	@echo "  make test-web          - Run web app tests"
	@echo ""
	@echo "Data Management:"
	@echo "  make cosmos-csp-clear-projects  - Clear CSP projects/messages (keeps users)"
	@echo "  make cosmos-csp-clear-users     - Clear CSP users only"
	@echo "  make cosmos-csp-clear           - Clear ALL CSP data"
	@echo "  make cosmos-ladbs-clear         - Clear all LADBS data"
	@echo "  make cosmos-ladwp-clear         - Clear all LADWP data"
	@echo "  make cosmos-lasan-clear         - Clear all LASAN data"
	@echo "  make cosmos-dry                 - Dry run (show what would be deleted)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                - Clean up virtual environments and caches"
	@echo "  make sync                 - Sync all dependencies"
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

dev-agent:
	@echo "🤖 Starting CSP Agent only..."
	@echo "   Expects MCP servers running on ports 8001-8004"
	@echo "   Agent will be available at http://localhost:8088"
	@bash -c '\
		set -a && \
		eval "$$(azd env get-values)" && \
		set +a && \
		export MCP_LADBS_URL=http://localhost:8001/mcp && \
		export MCP_LADWP_URL=http://localhost:8002/mcp && \
		export MCP_LASAN_URL=http://localhost:8003/mcp && \
		export MCP_CSP_URL=http://localhost:8004/mcp && \
		export AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4.1 && \
		export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 && \
		export OTEL_SERVICE_NAME=csp-agent && \
		export LOCAL_DEV=true && \
		cd src/agents/csp-agent && \
		uv run python main.py'

# ============================================================================
# Observability - Aspire Dashboard for OpenTelemetry traces
# ============================================================================

aspire-start:
	@echo "📊 Starting Aspire Dashboard for OpenTelemetry traces..."
	@echo "   Dashboard UI: http://localhost:18888"
	@echo "   OTLP gRPC:    localhost:4317"
	@docker run -d --name aspire-dashboard \
		-p 18888:18888 \
		-p 4317:18889 \
		-p 4318:18890 \
		-e DOTNET_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true \
		mcr.microsoft.com/dotnet/aspire-dashboard:9.0
	@echo "✅ Aspire Dashboard started. Open http://localhost:18888"

aspire-stop:
	@echo "🛑 Stopping Aspire Dashboard..."
	@docker stop aspire-dashboard 2>/dev/null || true
	@docker rm aspire-dashboard 2>/dev/null || true
	@echo "✅ Aspire Dashboard stopped"

aspire-logs:
	@docker logs -f aspire-dashboard

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
	@echo "🧪 Running MCP server unit tests..."
	cd src/mcp-servers/ladbs && uv run pytest tests/test_tools.py -v
	cd src/mcp-servers/ladwp && uv run pytest tests/test_tools.py -v
	cd src/mcp-servers/lasan && uv run pytest tests/test_tools.py -v

test-mcp-integration:
	@echo "🧪 Running MCP server integration tests..."
	./scripts/test-mcp-server.sh ladbs --integration
	./scripts/test-mcp-server.sh ladwp --integration
	./scripts/test-mcp-server.sh lasan --integration

test-mcp-deployed:
	@echo "🧪 Running MCP server deployed tests..."
	./scripts/test-mcp-server.sh ladbs --deployed
	./scripts/test-mcp-server.sh ladwp --deployed
	./scripts/test-mcp-server.sh lasan --deployed

test-mcp-full:
	@echo "🧪 Running full MCP server test suite..."
	./scripts/test-mcp-server.sh ladbs --all
	./scripts/test-mcp-server.sh ladwp --all
	./scripts/test-mcp-server.sh lasan --all

test-ladbs:
	@./scripts/test-mcp-server.sh ladbs --all

test-ladwp:
	@./scripts/test-mcp-server.sh ladwp --all

test-lasan:
	@./scripts/test-mcp-server.sh lasan --all

test-csp:
	@./scripts/test-mcp-server.sh csp --all

test-web:
	@echo "🧪 Running web app tests..."
	cd src/web-app && uv run pytest

# ============================================================================
# Setup
# ============================================================================

dev-setup:
	@echo "🔧 Setting up development environment..."
	@./scripts/setup-dev-rbac.sh
	@echo ""
	@echo "✅ Development setup complete!"

rbac:
	@echo "🔐 Setting up CosmosDB RBAC roles..."
	@./scripts/setup-dev-rbac.sh

# ============================================================================
# Data Management
# ============================================================================

# CSP Database
cosmos-csp-clear-projects:
	@echo "🗑️  Clearing CSP projects/messages (keeping users)..."
	cd scripts && uv run python clear-cosmos-data.py --confirm --database csp --containers projects,messages

cosmos-csp-clear-users:
	@echo "🗑️  Clearing CSP users..."
	cd scripts && uv run python clear-cosmos-data.py --confirm --database csp --containers users

cosmos-csp-clear:
	@echo "🗑️  Clearing ALL CSP data..."
	cd scripts && uv run python clear-cosmos-data.py --confirm --database csp

# Agency Databases
cosmos-ladbs-clear:
	@echo "🗑️  Clearing LADBS data..."
	cd scripts && uv run python clear-cosmos-data.py --confirm --database ladbs

cosmos-ladwp-clear:
	@echo "🗑️  Clearing LADWP data..."
	cd scripts && uv run python clear-cosmos-data.py --confirm --database ladwp

cosmos-lasan-clear:
	@echo "🗑️  Clearing LASAN data..."
	cd scripts && uv run python clear-cosmos-data.py --confirm --database lasan

# Dry run (defaults to csp)
cosmos-dry:
	@echo "🗑️  Dry run - showing what would be deleted..."
	cd scripts && uv run python clear-cosmos-data.py --database csp

# ============================================================================
# Utilities
# ============================================================================

sync:
	@echo "📦 Syncing all dependencies..."
	cd src/mcp-servers/ladbs && uv sync
	cd src/mcp-servers/ladwp && uv sync
	cd src/mcp-servers/lasan && uv sync
	cd src/mcp-servers/csp && uv sync
	cd src/web-app && uv sync

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete"
