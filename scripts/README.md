# Scripts

This directory contains automation scripts for the Citizen Services Portal project, organized by function.

## Directory Structure

```
scripts/
├── knowledge-base/     # Knowledge base ingestion and testing
├── mcp/                # MCP server authentication and setup
├── ai-gateway/         # AI Gateway configuration
└── README.md           # This file
```

## Knowledge Base Scripts (`knowledge-base/`)

Scripts for setting up and testing the Azure AI Search knowledge bases.

| Script | Purpose |
|--------|---------|
| `setup-kb-permissions.sh` | Configure RBAC permissions for the ingestion pipeline |
| `upload-kb-documents.py` | Upload documents from `/assets/` to blob storage |
| `setup-knowledge-base.py` | Create indexes, skillsets, data sources, and indexers |
| `run-kb-indexers.sh` | Run all indexers to process documents |
| `run-all-tests.sh` | Run all knowledge base tests |
| `test-document-counts.py` | Verify document counts in indexes |
| `test-regular-search.py` | Test keyword search functionality |
| `test-semantic-search.py` | Test semantic search functionality |

**Quick Start:**
```bash
cd scripts/knowledge-base
./setup-kb-permissions.sh
python upload-kb-documents.py
python setup-knowledge-base.py
./run-kb-indexers.sh
./run-all-tests.sh
```

See [knowledge-base/README.md](knowledge-base/README.md) for detailed documentation.

## MCP Server Scripts (`mcp/`)

Scripts for configuring MCP server authentication and access.

| Script | Purpose |
|--------|---------|
| `setup-mcp-auth.sh` | Configure authentication for MCP servers |
| `test-mcp-auth.sh` | Test MCP server authentication |
| `fix-mcp-auth.sh` | Fix common MCP authentication issues |
| `grant-agent-mcp-access.sh` | Grant agent access to MCP servers |

## AI Gateway Scripts (`ai-gateway/`)

Scripts for configuring the Azure API Management AI Gateway.

| Script | Purpose |
|--------|---------|
| `configure-ai-gateway.sh` | Configure AI Gateway settings |
| `configure_ai_gateway.py` | Python script for AI Gateway configuration |
| `configure_ai_gateway_arm.py` | ARM-based AI Gateway configuration |

## Local Development Orchestrator

The `dev-local.py` script starts all services locally for rapid development:

```bash
# Install dependencies and run
cd scripts
uv sync
uv run python dev-local.py

# Or use Make from project root
make dev
```

**Options:**
| Flag | Description |
|------|-------------|
| `--mcp-only` | Start only MCP servers |
| `--web-only` | Start only web application |
| `--no-logs` | Run services in background without log streaming |

**Prerequisites:**
- Azure CLI logged in: `az login`
- azd environment: `azd env select <env-name>`

The script automatically loads `AZURE_OPENAI_ENDPOINT` from `azd env get-values` for the CSP Agent.

See [dev-local.py](dev-local.py) for full documentation.

## Python Environment

Scripts use UV for Python package management:

```bash
cd scripts
uv sync
uv run python <script.py>
```

## Prerequisites

- Azure CLI (`az`) installed and logged in
- Python 3.12+ 
- UV package manager (`pip install uv` or https://docs.astral.sh/uv/)
- Azure Developer CLI (`azd`) for infrastructure deployment
- Infrastructure deployed via `azd up`
