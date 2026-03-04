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

Tests the CSP Agent deployed to Azure Container Apps.

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

## Agent Evaluation

This package includes evaluation capabilities using the **Microsoft Azure AI Foundry Evaluation SDK**. The evaluation framework uses ONLY SDK built-in evaluators - no custom evaluation logic.

### Quick Start

```bash
# Step 1: Collect agent responses for evaluation
uv run python -m evaluation.data_collector \
    --input evaluation_data/test_queries.jsonl \
    --output evaluation_data/collected_responses.jsonl

# Step 2: Run SDK evaluation
uv run python -m evaluation.run_evaluation \
    --data evaluation_data/collected_responses.jsonl \
    --output evaluation_results/ \
    --thresholds evaluation/thresholds.yaml
```

### Evaluation Scripts

#### Data Collector (`evaluation/data_collector.py`)

Collects agent responses for evaluation by sending test queries to the CSP Agent.

```bash
# Collect responses from test queries
uv run python -m evaluation.data_collector \
    --input evaluation_data/test_queries.jsonl \
    --output evaluation_data/collected_responses.jsonl

# With verbose output (shows tool calls)
uv run python -m evaluation.data_collector \
    --input evaluation_data/test_queries.jsonl \
    --output evaluation_data/collected_responses.jsonl \
    --verbose
```

#### Evaluation Runner (`evaluation/run_evaluation.py`)

Runs evaluation using the Azure AI Evaluation SDK built-in evaluators.

```bash
# Run all evaluators
uv run python -m evaluation.run_evaluation \
    --data evaluation_data/collected_responses.jsonl \
    --output evaluation_results/

# Run specific evaluators only
uv run python -m evaluation.run_evaluation \
    --data evaluation_data/collected_responses.jsonl \
    --evaluators coherence relevance groundedness

# Skip threshold checking
uv run python -m evaluation.run_evaluation \
    --data evaluation_data/collected_responses.jsonl \
    --no-threshold-check
```

### SDK Built-in Evaluators Used

| Evaluator | Purpose | Data Required |
|-----------|---------|---------------|
| **CoherenceEvaluator** | Clear and coherent? | query, response |
| **FluencyEvaluator** | Natural language? | query, response |
| **RelevanceEvaluator** | Relevant to query? | query, response |
| **GroundednessEvaluator** | Grounded in context? | response, context |
| **SimilarityEvaluator** | Similar to ground truth? | response, ground_truth |
| **F1ScoreEvaluator** | Token overlap score | response, ground_truth |

### File Structure

```
scripts/agents/
├── evaluation/
│   ├── __init__.py           # Package init
│   ├── config.py             # Model configuration
│   ├── data_collector.py     # Collect agent responses
│   ├── run_evaluation.py     # Main evaluation runner
│   └── thresholds.yaml       # Pass/fail thresholds
│
└── evaluation_data/
    └── test_queries.jsonl    # Test dataset (30 queries)
```

### Environment Variables for Evaluation

```bash
# Azure OpenAI for evaluation (judge model)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key  # Or use DefaultAzureCredential
AZURE_OPENAI_EVAL_DEPLOYMENT=gpt-4o  # Recommended for evaluation
AZURE_API_VERSION=2024-10-21
```

### Thresholds Configuration

Edit `evaluation/thresholds.yaml` to customize pass/fail thresholds:

```yaml
pass_thresholds:
  coherence.coherence: 4.0      # 1-5 scale
  fluency.fluency: 4.0
  relevance.relevance: 4.0
  groundedness.groundedness: 4.0
  similarity.similarity: 0.7    # 0-1 scale
  f1_score.f1_score: 0.6
```

### Exit Codes

- `0`: All thresholds passed
- `1`: One or more thresholds failed (for CI/CD integration)

### Reference Documentation

- [Azure AI Evaluation SDK](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk)
- [Built-in Evaluators Reference](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/observability#what-are-evaluators)
