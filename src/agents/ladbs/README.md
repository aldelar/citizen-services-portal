# LADBS AI Agent

AI Agent for Los Angeles Department of Building and Safety (LADBS) services.

## Overview

This agent assists citizens with building permits, inspections, violations, and general LADBS inquiries using the MCP-LADBS tool.

**Model:** gpt-5.2 (via APIM AI Gateway)
**Tools:** mcp-ladbs (accessed via APIM MCP Services API)

## Deployment

See [deploy.py](deploy.py) for automated deployment using Azure AI Foundry SDK.

## Files

- `agent.yaml` - Agent configuration
- `system-prompt.md` - Agent instructions and personality
- `tools/mcp-ladbs.yaml` - MCP tool connection specification
- `deploy.py` - Deployment script

## Manual Testing

After deployment, test the agent in Azure AI Foundry Portal:
1. Navigate to the `citizen-services-portal` project
2. Go to **Agents**
3. Select **ladbs-assistant**
4. Open **Playground** to chat with the agent
