# Reporting MCP Server

Model Context Protocol (MCP) server for tracking step durations and providing average time estimates.

## Overview

This MCP server provides tools for:
- Logging completed plan steps for reporting
- Querying average durations based on historical data
- Filtering by city for local relevance

## Tools

| Tool | Type | Action | Key Inputs | Returns |
|------|------|--------|------------|---------|
| `steps.logCompleted` | **Automated** | Log a completed step | `toolName`, `city`, `startedAt`, `completedAt` | Confirmation |
| `steps.getAverageDuration` | Query | Get average duration | `toolName`, `city?` | Average days, sample count |

### How It Works

1. When agent completes a plan step, it calls `steps.logCompleted` with:
   - `toolName`: The MCP tool used (e.g., `permits.submit`, `tou.enroll`)
   - `city`: Geographic filter (e.g., `Los Angeles`)
   - `startedAt` / `completedAt`: Timestamps from the step

2. When building a plan or answering "how long will this take?", agent calls `steps.getAverageDuration`:
   - Returns average duration based on last 6 months of data
   - Filtered by city for local relevance

### Normalized Tool Names

Step names are normalized to MCP tool names for consistent aggregation:

| toolName | Description |
|----------|-------------|
| `permits.submit` | Permit application (any type) |
| `permits.getStatus` | Permit status check |
| `inspections.schedule` | Schedule an inspection |
| `tou.enroll` | TOU rate enrollment |
| `interconnection.submit` | Solar interconnection application |
| `rebates.apply` | Rebate application |
| `pickup.schedule` | Waste pickup scheduling |

### Example Usage

```
Agent: "Based on recent data in Los Angeles, electrical permits 
        typically take 6-8 weeks from submission to approval."
        
        [calls steps.getAverageDuration with toolName="permits.submit", city="Los Angeles"]
        → { "averageDays": 47, "sampleCount": 234 }
```

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

### Setup Development Environment

```bash
# Navigate to the Reporting MCP server directory
cd src/mcp-servers/reporting

# Create virtual environment and install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### Run the Server Locally

```bash
# Activate virtual environment (optional with uv)
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Run the server
uv run python mcp_server_reporting.py
```

Server will start on `http://localhost:8000`

### Test the Server

```bash
# In a separate terminal, run the test client
uv run python mcp_client_reporting.py
```

## Development

### Project Structure

```
reporting/
├── mcp_server_reporting.py  # Main server entry point
├── mcp_client_reporting.py  # Test client
├── src/                      # Implementation
│   ├── tools.py             # MCP tools definitions
│   ├── models.py            # Pydantic models
│   ├── services.py          # Business logic
│   └── config.py            # Configuration
└── tests/                    # Unit tests
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Data Storage

The current implementation uses in-memory storage with mock historical data for demo purposes.

For production, the service is designed to integrate with Azure Cosmos DB:
- Database: `reporting`
- Container: `step_logs`
- Partition key: `/tool_name`

To enable Cosmos DB:
1. Set `COSMOS_ENDPOINT` in `.env`
2. Ensure the managed identity has read/write access
3. Uncomment the Cosmos DB integration code in `services.py`

## Deployment

The server is deployed as an Azure Container App via the infrastructure templates in `/infra/app/mcp-reporting.bicep`.

See the main project README for deployment instructions.
