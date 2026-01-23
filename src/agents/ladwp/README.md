# LADWP Agent

AI assistant for Los Angeles Department of Water and Power services.

## Overview

This agent helps citizens with LADWP utility services through natural conversation.

## Capabilities

- Account balance and billing inquiries
- Payment processing
- Outage reporting and status
- Service start/stop requests
- Usage history queries

## Deployment

Deploy using the master deployment script:
```bash
cd src/agents
uv run python deploy.py ladwp
```

## Configuration

The agent connects to the LADWP MCP server for tool access.
See `agent.yaml` for configuration details.
