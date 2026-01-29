# CSP Agent Test Scripts

Test scripts for the Citizen Services Portal (CSP) Agent and MCP Servers.

## Setup

```bash
cd scripts/agents
uv sync
```

## Scripts

### 1. MCP Servers Health Check (`test_mcp_servers.py`)

Tests connectivity and discovers tools from all deployed MCP servers.

```bash
# Test Azure-deployed servers (default)
uv run python test_mcp_servers.py

# Test with tool calls
uv run python test_mcp_servers.py --test-tools

# Verbose output with all tools listed
uv run python test_mcp_servers.py -v

# Test local servers
uv run python test_mcp_servers.py --local

# Test specific server
uv run python test_mcp_servers.py --server ladbs
```

### 2. CSP Agent Local Test (`test_csp_agent_local.py`)

Tests the CSP Agent locally using deployed MCP servers and Azure OpenAI.

```bash
# Run predefined test queries
uv run python test_csp_agent_local.py

# Run with verbose output (shows tool calls)
uv run python test_csp_agent_local.py -v

# Run a single query
uv run python test_csp_agent_local.py --query "How do I get an electrical permit?"

# Interactive chat mode
uv run python test_csp_agent_local.py --interactive
```

### 3. CSP Agent Azure Test (`test_csp_agent_azure.py`)

Tests the CSP Agent deployed to Azure AI Foundry Agent Service.

```bash
# Run health check and test query
uv run python test_csp_agent_azure.py

# List deployed agents
uv run python test_csp_agent_azure.py --list

# Run a single query
uv run python test_csp_agent_azure.py --query "What permits do I need for solar panels?"

# Interactive chat mode
uv run python test_csp_agent_azure.py --interactive
```

## Environment Variables

The scripts use the following environment variables (with defaults for the deployed infrastructure):

```bash
# MCP Server URLs
MCP_LADBS_URL=https://aldelar-csp-mcp-ladbs.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp
MCP_LADWP_URL=https://aldelar-csp-mcp-ladwp.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp
MCP_LASAN_URL=https://aldelar-csp-mcp-lasan.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp
MCP_CSP_URL=https://aldelar-csp-mcp-csp.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://aldelar-csp-foundry.cognitiveservices.azure.com/
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4.1

# Foundry Project
FOUNDRY_PROJECT_ENDPOINT=https://aldelar-csp-foundry.services.ai.azure.com/api/projects/aldelar-csp-foundry-project
CSP_AGENT_NAME=csp-agent
```

## Authentication

All scripts use `DefaultAzureCredential` for authentication. Make sure you're logged in:

```bash
az login
```

## Test Results

### MCP Servers
| Server | Status | Tools |
|--------|--------|-------|
| LADBS | ✓ Healthy | 6 tools |
| LADWP | ✓ Healthy | 9 tools |
| LASAN | ✓ Healthy | 4 tools |
| CSP | ✓ Healthy | 4 tools |

### Available Tools (23 total)
- **LADBS**: queryKB, permits_search, permits_submit, permits_getStatus, inspections_scheduled, inspections_schedule
- **LADWP**: queryKB, account_show, plans_list, tou_enroll, interconnection_submit, interconnection_getStatus, rebates_filed, rebates_apply, rebates_getStatus
- **LASAN**: queryKB, pickup_scheduled, pickup_schedule, pickup_getEligibility
- **CSP**: plan_create, plan_get, plan_update, plan_updateStep
