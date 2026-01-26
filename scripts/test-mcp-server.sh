#!/bin/bash
# ==============================================================================
# MCP Server Test Suite
# 
# Runs comprehensive tests for MCP servers including:
# - Unit tests (no external dependencies)
# - AI Search integration tests (requires AZURE_SEARCH_ENDPOINT)
# - CosmosDB integration tests (requires COSMOS_ENDPOINT)
# - Deployed server tests (requires server to be deployed)
#
# Usage:
#   ./scripts/test-mcp-server.sh <server-name> [--unit|--integration|--deployed|--all]
#
# Examples:
#   ./scripts/test-mcp-server.sh ladwp --unit        # Unit tests only
#   ./scripts/test-mcp-server.sh ladwp --integration # Integration tests only
#   ./scripts/test-mcp-server.sh ladwp --deployed    # Deployed server test only
#   ./scripts/test-mcp-server.sh ladwp --all         # All tests (default)
#   ./scripts/test-mcp-server.sh ladwp               # All tests (default)
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Azure service names (from specs/0-azure-services.md)
SEARCH_ENDPOINT="${AZURE_SEARCH_ENDPOINT:-https://aldelar-csp-search.search.windows.net}"
COSMOS_ENDPOINT="${COSMOS_ENDPOINT:-https://aldelar-csp-cosmos.documents.azure.com:443/}"

# Container App hosts (without https://)
declare -A MCP_HOSTS=(
    ["ladbs"]="aldelar-csp-mcp-ladbs.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io"
    ["ladwp"]="aldelar-csp-mcp-ladwp.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io"
    ["lasan"]="aldelar-csp-mcp-lasan.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io"
    ["reporting"]="aldelar-csp-mcp-reporting.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io"
)

# Database names for each server
declare -A COSMOS_DATABASES=(
    ["ladbs"]="ladbs"
    ["ladwp"]="ladwp"
    ["lasan"]="lasan"
    ["reporting"]="reporting"
)

# Search index names
declare -A SEARCH_INDEXES=(
    ["ladbs"]="ladbs-kb"
    ["ladwp"]="ladwp-kb"
    ["lasan"]="lasan-kb"
    ["reporting"]=""
)

# ==============================================================================
# Helper Functions
# ==============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}==============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ==============================================================================
# Test Functions
# ==============================================================================

run_unit_tests() {
    local server=$1
    local server_dir="$PROJECT_ROOT/src/mcp-servers/$server"
    
    print_header "Unit Tests: $server"
    
    if [ ! -f "$server_dir/tests/test_tools.py" ]; then
        print_warning "No unit tests found at $server_dir/tests/test_tools.py"
        return 0
    fi
    
    cd "$server_dir"
    
    if uv run pytest tests/test_tools.py -v --tb=short; then
        print_success "Unit tests passed"
        return 0
    else
        print_error "Unit tests failed"
        return 1
    fi
}

run_search_integration_tests() {
    local server=$1
    local server_dir="$PROJECT_ROOT/src/mcp-servers/$server"
    local search_index="${SEARCH_INDEXES[$server]}"
    
    print_header "AI Search Integration Tests: $server"
    
    if [ -z "$search_index" ]; then
        print_info "No search index configured for $server, skipping search tests"
        return 0
    fi
    
    if [ ! -f "$server_dir/tests/test_search_integration.py" ]; then
        print_warning "No search integration tests found"
        return 0
    fi
    
    cd "$server_dir"
    
    print_info "Using search endpoint: $SEARCH_ENDPOINT"
    print_info "Using search index: $search_index"
    
    if AZURE_SEARCH_ENDPOINT="$SEARCH_ENDPOINT" \
       AZURE_SEARCH_INDEX_NAME="$search_index" \
       uv run pytest tests/test_search_integration.py -v -m integration --tb=short; then
        print_success "AI Search integration tests passed"
        return 0
    else
        print_error "AI Search integration tests failed"
        return 1
    fi
}

run_cosmos_integration_tests() {
    local server=$1
    local server_dir="$PROJECT_ROOT/src/mcp-servers/$server"
    local database="${COSMOS_DATABASES[$server]}"
    
    print_header "CosmosDB Integration Tests: $server"
    
    if [ ! -f "$server_dir/tests/test_cosmosdb_integration.py" ]; then
        print_warning "No CosmosDB integration tests found"
        return 0
    fi
    
    cd "$server_dir"
    
    print_info "Using Cosmos endpoint: $COSMOS_ENDPOINT"
    print_info "Using database: $database"
    
    if AZURE_SEARCH_ENDPOINT="$SEARCH_ENDPOINT" \
       COSMOS_ENDPOINT="$COSMOS_ENDPOINT" \
       COSMOS_DATABASE="$database" \
       uv run pytest tests/test_cosmosdb_integration.py -v -m integration --tb=short; then
        print_success "CosmosDB integration tests passed"
        return 0
    else
        print_error "CosmosDB integration tests failed"
        return 1
    fi
}

run_deployed_tests() {
    local server=$1
    local server_dir="$PROJECT_ROOT/src/mcp-servers/$server"
    local host="${MCP_HOSTS[$server]}"
    local client_script="mcp_client_${server}.py"
    
    print_header "Deployed Server Tests: $server"
    
    if [ ! -f "$server_dir/$client_script" ]; then
        print_warning "No client script found at $server_dir/$client_script"
        return 0
    fi
    
    print_info "Testing deployed server: https://$host/mcp"
    
    cd "$server_dir"
    
    # Run the client and check for success markers
    local output
    if output=$(MCP_SERVER_HOST="$host" MCP_SERVER_PORT="443" \
                timeout 60 uv run python "$client_script" 2>&1); then
        
        # Count successes and failures
        local successes=$(echo "$output" | grep -c "✅" || true)
        local failures=$(echo "$output" | grep -c "❌" || true)
        
        echo "$output" | grep -E "✅|❌|Server Name|Server Version"
        
        if [ "$failures" -gt 0 ]; then
            print_error "Deployed tests: $failures failures, $successes successes"
            return 1
        else
            print_success "Deployed tests: $successes tools passed"
            return 0
        fi
    else
        print_error "Failed to connect to deployed server"
        echo "$output"
        return 1
    fi
}

# ==============================================================================
# Main
# ==============================================================================

usage() {
    echo "Usage: $0 <server-name> [--unit|--integration|--deployed|--all]"
    echo ""
    echo "Available servers: ladbs, ladwp, lasan, reporting"
    echo ""
    echo "Options:"
    echo "  --unit         Run unit tests only"
    echo "  --integration  Run integration tests (AI Search + CosmosDB)"
    echo "  --deployed     Run deployed server tests only"
    echo "  --all          Run all tests (default)"
    echo ""
    echo "Environment variables:"
    echo "  AZURE_SEARCH_ENDPOINT  AI Search endpoint (default: aldelar-csp-search)"
    echo "  COSMOS_ENDPOINT        CosmosDB endpoint (default: aldelar-csp-cosmos)"
    exit 1
}

main() {
    local server=$1
    local mode=${2:---all}
    
    if [ -z "$server" ]; then
        usage
    fi
    
    # Validate server name
    if [ ! -d "$PROJECT_ROOT/src/mcp-servers/$server" ]; then
        print_error "Unknown server: $server"
        echo "Available servers: ladbs, ladwp, lasan, reporting"
        exit 1
    fi
    
    print_header "MCP Server Test Suite: $server"
    echo ""
    echo "Server:    $server"
    echo "Mode:      $mode"
    echo "Search:    $SEARCH_ENDPOINT"
    echo "Cosmos:    $COSMOS_ENDPOINT"
    echo ""
    
    local unit_result=0
    local search_result=0
    local cosmos_result=0
    local deployed_result=0
    
    case "$mode" in
        --unit)
            run_unit_tests "$server" || unit_result=$?
            ;;
        --integration)
            run_search_integration_tests "$server" || search_result=$?
            run_cosmos_integration_tests "$server" || cosmos_result=$?
            ;;
        --deployed)
            run_deployed_tests "$server" || deployed_result=$?
            ;;
        --all)
            run_unit_tests "$server" || unit_result=$?
            run_search_integration_tests "$server" || search_result=$?
            run_cosmos_integration_tests "$server" || cosmos_result=$?
            run_deployed_tests "$server" || deployed_result=$?
            ;;
        *)
            print_error "Unknown mode: $mode"
            usage
            ;;
    esac
    
    # Summary
    local total_failures=$((unit_result + search_result + cosmos_result + deployed_result))
    
    echo ""
    if [ $total_failures -gt 0 ]; then
        print_error "$server: Some tests failed"
        exit 1
    else
        print_success "$server: All tests passed!"
        exit 0
    fi
}

main "$@"
