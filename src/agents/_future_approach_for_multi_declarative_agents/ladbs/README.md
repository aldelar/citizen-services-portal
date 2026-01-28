# LADBS AI Agent

AI assistant for Los Angeles Department of Building and Safety (LADBS) services.

## Overview

This agent provides intelligent assistance for LADBS-related queries, including:
- Building permit information
- Inspection scheduling
- Code compliance guidance
- Service navigation

## Architecture

- **Agent Definition**: `agent.yaml` - Configuration for the AI agent
- **System Prompt**: `system-prompt.md` - Instructions and behavior definition
- **Tools**: `tools/` - MCP tool definitions for extended capabilities

## Deployment

The agent deployment uses generic scripts located in the `src/agents/` directory that work with any agent.

### Deploy All Services

```bash
azd deploy
```

This deploys both the MCP server (container app) and the agent definition.

### Deploy Only LADBS Agent

To deploy only the LADBS agent and its tools (skip MCP server):

```bash
azd deploy ladbs-agent
```

### Manual Deployment

You can also run the deployment scripts directly:

```bash
cd src/agents

# Deploy everything (tools + agent)
python deploy.py ladbs

# Or deploy individually
python deploy_tools.py ladbs
python deploy_agent.py ladbs
```

See [../README.md](../README.md) for detailed documentation on the deployment scripts.

## Configuration

### Environment Variables

Required for deployment:

- `foundryProjectEndpoint` - Azure AI Foundry project endpoint (set by azd)
- Format: `https://{foundry-name}.services.ai.azure.com/api/projects/{project-name}`
- Credentials are obtained via Azure CLI (`az login`)

### Agent Configuration

Edit [agent.yaml](agent.yaml) to modify:
- Model deployment name
- Temperature and max_tokens
- Tool references

## Idempotency

Both deployment scripts are idempotent:
- **Tools**: Validated on each deployment (registration API support pending)
- **Agent**: New version created automatically if definition changed
- Safe to run multiple times without duplicates

## Change Detection

Currently, deployments run on every `azd deploy` call. To skip unnecessary deployments:

1. **Manual approach**: Run scripts individually only when needed
2. **Git-based**: Add pre-deploy check to compare git status
3. **Hash-based**: Calculate config file hashes and skip if unchanged

For production, consider implementing one of these approaches in `deploy.py`.

## Testing

After deployment, test the agent:
- Azure AI Foundry Portal: https://ai.azure.com
- Navigate to your project → Agents
- Find `ladbs-assistant` and start a conversation

### Test MCP Server

```bash
cd ../../mcp-servers/ladbs
MCP_SERVER_HOST="<your-aca-host>" MCP_SERVER_PORT="443" uv run python mcp_client_ladbs.py
```

## Development Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Azure CLI (`az login` required)
