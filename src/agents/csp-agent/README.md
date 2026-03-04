# CSP Agent (Citizen Services Portal Agent)

**IMPORTANT!** All samples and other resources made available in this GitHub repository ("samples") are designed to assist in accelerating development of agents, solutions, and agent workflows for various scenarios. Review all provided resources and carefully test output behavior in the context of your use case. AI responses may be inaccurate and AI actions should be monitored with human oversight. Learn more in the transparency documents for [Agent Service](https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/agents/transparency-note) and [Agent Framework](https://github.com/microsoft/agent-framework/blob/main/TRANSPARENCY_FAQ.md).

## Overview

The **CSP Agent** is a unified AI assistant for the City of Los Angeles government services. It serves as a single point of contact for citizens navigating complex government processes across multiple departments:

- **LADBS** (Los Angeles Department of Building and Safety) - Building permits, inspections, code violations
- **LADWP** (Los Angeles Department of Water and Power) - Utility services, solar programs, rebates
- **LASAN** (LA Sanitation & Environment) - Waste collection, bulky items, recycling
- **Reporting** - Cross-agency analytics and reporting

## Architecture

The CSP Agent is implemented as a **containerized Python service** using the Microsoft Agent Framework and deployed to **Azure Container Apps (ACA)**. It exposes an OpenAI-compatible Responses API and connects to four MCP (Model Context Protocol) servers, each providing specialized tools for their respective agencies.

```
                    ┌─────────────────┐
                    │   Citizen/User  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    CSP Agent    │
                    │ (Container App) │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │  LADBS  │         │  LADWP  │         │  LASAN  │
   │   MCP   │         │   MCP   │         │   MCP   │
   └─────────┘         └─────────┘         └─────────┘
```

## How It Works

### MCP Integration

The agent uses `MCPStreamableHTTPTool` to connect to each MCP server:

1. When a user asks a question, the agent determines which MCP tools are relevant
2. Azure OpenAI Responses service automatically invokes the appropriate MCP tools
3. The agent synthesizes results and generates a coherent response

### Plan Generation

For complex requests spanning multiple agencies, the agent generates a **Plan**:

1. Queries relevant knowledge bases to understand requirements
2. Creates a structured multi-step plan with dependencies
3. Guides the user through each step, handling both automated actions and user actions

### User Actions

Some government processes cannot be fully automated (e.g., scheduling inspections requires calling 311). When this occurs:

1. The MCP tool returns a `UserActionResponse` with prepared materials
2. The agent presents phone scripts, email drafts, or checklists
3. The user completes the action and confirms
4. The agent continues with the next step

## Running Locally

### Prerequisites

1. Azure OpenAI endpoint configured
2. Azure CLI installed and authenticated (`az login`)
3. Python 3.12+ installed
4. MCP servers running (locally or in Azure Container Apps)

### Environment Variables

Set the following environment variables:

```bash
# Azure OpenAI Configuration
export AZURE_OPENAI_ENDPOINT="https://your-openai-resource.openai.azure.com/"
export AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="gpt-4o-mini"

# MCP Server URLs
export MCP_LADBS_URL="http://localhost:8001"   # or deployed URL
export MCP_LADWP_URL="http://localhost:8002"   # or deployed URL
export MCP_LASAN_URL="http://localhost:8003"   # or deployed URL
export MCP_CSP_URL="http://localhost:8004"  # or deployed URL
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Agent

```bash
python main.py
```

The agent will start on `http://localhost:8088/`.

### Test the Agent

```bash
curl -sS -H "Content-Type: application/json" \
  -X POST http://localhost:8088/responses \
  -d '{"input": "What documents do I need for a solar panel permit?", "stream": false}'
```

## Deploying to Azure Container Apps

### Using azd (Recommended)

The agent is deployed as an Azure Container App. Deploy all services (including the agent) with:

```bash
azd up
```

Or deploy only the agent after infrastructure exists:

```bash
azd deploy csp-agent
```

This builds the Docker image, pushes it to Azure Container Registry, and updates the Container App.

## File Structure

```
csp-agent/
├── Dockerfile                # Container definition
├── README.md                 # This file
├── agent.yaml                # Agent manifest (metadata and env vars)
├── main.py                   # Agent entry point (FastAPI server)
├── requirements.txt          # Python dependencies
└── prompts/
    └── system_prompt.md      # Agent system instructions
```

## Configuration

### agent.yaml

The agent manifest defines:

- **kind**: `hosted` - Agent kind identifier (retained for manifest compatibility)
- **name**: `csp-agent` - Agent identifier
- **protocols**: `responses` - Uses OpenAI Responses protocol
- **environment_variables**: Configuration for Azure OpenAI and MCP servers

> **Note:** The agent is deployed as an Azure Container App, not as a Foundry Hosted Agent. The `agent.yaml` manifest is kept for metadata and local tooling compatibility.

### System Prompt

The system prompt in `prompts/system_prompt.md` defines:

- Agent identity and role
- Available tools from each MCP server
- Plan generation framework
- Response guidelines
- Multi-agency coordination rules

## Troubleshooting

### Images built on Apple Silicon don't work

We recommend using `azd` cloud build, which always builds with the correct architecture.

For local builds on ARM64 machines:

```bash
docker build --platform=linux/amd64 -t csp-agent .
```

### MCP Server Connection Issues

Verify MCP server URLs are accessible:

```bash
curl -I $MCP_LADBS_URL
curl -I $MCP_LADWP_URL
curl -I $MCP_LASAN_URL
curl -I $MCP_CSP_URL
```

### Missing Environment Variables

Ensure all required environment variables are set:

```bash
env | grep -E "(AZURE_OPENAI|MCP_)"
```

## Related Resources

- [Technical Specification](/specs/4-spec-csp-agent.md)
- [MCP Server Specifications](/specs/1-spec-mcp-servers.md)
- [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Azure AI AgentServer SDK](https://learn.microsoft.com/en-us/dotnet/api/overview/azure/ai.agentserver.agentframework-readme)
