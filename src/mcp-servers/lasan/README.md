# LADWP MCP Server

Model Context Protocol (MCP) server for Los Angeles Department of Water and Power (LADWP) services.

## Overview

This MCP server provides tools for interacting with LADWP utility services, including:
- Account balance inquiries
- Bill history retrieval
- Payment submissions
- Outage reporting and status checks
- Service start/stop requests
- Usage history retrieval

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
# Navigate to the LADWP MCP server directory
cd src/mcp-servers/ladwp

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
uv run python mcp_server_ladwp.py
```

Server will start on `http://localhost:8000`

### Test the Server

```bash
# In a separate terminal, run the test client
uv run python mcp_client_ladwp.py
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_account_balance` | Check utility account balance |
| `get_bill_history` | Retrieve billing history |
| `make_payment` | Submit utility payment |
| `report_outage` | Report power/water outage |
| `check_outage_status` | Check status of reported outages |
| `request_service_start` | Start new utility service |
| `request_service_stop` | Stop utility service |
| `get_usage_history` | Get water/power usage data |

## Development

### Project Structure

```
ladwp/
├── mcp_server_ladwp.py      # Main server entry point
├── mcp_client_ladwp.py      # Test client
├── src/                      # Implementation
│   ├── __init__.py
│   ├── tools.py             # MCP tools definitions
│   ├── models.py            # Pydantic models
│   ├── services.py          # Business logic
│   └── config.py            # Configuration
└── tests/                    # Unit tests
```

### Adding New Tools

1. Define tool function in `src/tools.py`
2. Register with FastMCP in `mcp_server_ladwp.py`
3. Add tests in `tests/test_tools.py`

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_tools.py
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .
```

### Update Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade

# Generate requirements.txt for Docker
uv pip compile pyproject.toml -o requirements.txt
```

## Deploy to Azure

### Prerequisites

- Azure subscription with required resources deployed (see root [README.md](../../../README.md))
- Azure CLI (`az`) - [Install Guide](https://learn.microsoft.com/cli/azure/install-azure-cli)
- Azure Developer CLI (`azd`) - [Install Guide](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- Docker (for manual deployments)

### Option 1: Deploy with azd (Recommended)

From the **repository root**, deploy the entire stack including LADWP:

```bash
# Deploy infrastructure + all services
azd up

# Or deploy only LADWP (after infrastructure exists)
azd deploy mcp-ladwp
```

This will:
1. Build the Docker image
2. Push to Azure Container Registry
3. Deploy to Azure Container Apps
4. Output the service URI

**View deployment outputs:**
```bash
azd env get-values

# Get LADWP URI
azd env get-value mcpLadwpUri
```

### Option 2: Manual Docker Deployment

If you need to deploy manually:

```bash
# From this directory (src/mcp-servers/ladwp)
cd src/mcp-servers/ladwp

# Build image
docker build -t aldelarcspcr.azurecr.io/mcp-ladwp:latest .

# Login to ACR
az acr login --name aldelarcspcr

# Push image
docker push aldelarcspcr.azurecr.io/mcp-ladwp:latest
```

### Verify Deployment

Test the deployed server:

```bash
# Get the deployed URL
MCP_URI=$(azd env get-value mcpLadwpUri)

# Test with client
cd src/mcp-servers/ladwp
MCP_SERVER_HOST="${MCP_URI#https://}" MCP_SERVER_PORT="443" uv run python mcp_client_ladwp.py
```

## Local Development

### Build Container Locally

```bash
# Build the image
docker build -t mcp-ladwp:latest .

# Run container
docker run -p 8000:8000 --env-file .env mcp-ladwp:latest
```

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_HOST` | Server host | localhost |
| `MCP_SERVER_PORT` | Server port | 8000 |
| `LADWP_API_ENDPOINT` | LADWP API endpoint | - |
| `LADWP_API_KEY` | LADWP API key | - |

## API Endpoints

When running, the server exposes:

- **POST** `/mcp` - Main MCP endpoint
- **GET** `/health` - Health check (if implemented)

## Troubleshooting

### Virtual Environment Issues

```bash
# Remove and recreate virtual environment
rm -rf .venv
uv sync
```

### Dependency Conflicts

```bash
# Clear uv cache
uv cache clean

# Reinstall dependencies
uv sync --reinstall
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in .env
```

## Contributing

1. Create a feature branch
2. Make changes
3. Run tests: `uv run pytest`
4. Format code: `uv run ruff format .`
5. Submit pull request

## License

Part of the Citizen Services Portal project.
