# LASAN MCP Server

Model Context Protocol (MCP) server for Los Angeles Bureau of Sanitation (LASAN) services.

## Overview

This MCP server provides tools for interacting with LASAN waste management and sanitation services, including:
- Collection schedule lookups
- Bulky item pickup scheduling
- Illegal dumping reports
- Bin replacement requests
- Recycling information
- Missed collection reports

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
# Navigate to the LASAN MCP server directory
cd src/mcp-servers/lasan

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
uv run python mcp_server_lasan.py
```

Server will start on `http://localhost:8000`

### Test the Server

```bash
# In a separate terminal, run the test client
uv run python mcp_client_lasan.py
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_collection_schedule` | Get trash/recycling pickup schedule for an address |
| `schedule_bulky_pickup` | Request bulky item pickup (furniture, appliances, etc.) |
| `check_pickup_status` | Check status of scheduled bulky item pickup |
| `report_illegal_dumping` | Report illegal dumping at a location |
| `check_dumping_report_status` | Check status of illegal dumping report |
| `request_bin_replacement` | Request replacement of damaged/missing trash bin |
| `get_recycling_info` | Get recycling guidelines and accepted materials |
| `report_missed_collection` | Report a missed trash/recycling pickup |

## Development

### Project Structure

```
lasan/
├── mcp_server_lasan.py      # Main server entry point
├── mcp_client_lasan.py      # Test client
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
2. Register with FastMCP in `mcp_server_lasan.py`
3. Add tests in `tests/test_tools.py`

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_tools.py -v
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

From the **repository root**, deploy the entire stack including LASAN:

```bash
# Deploy infrastructure + all services
azd up

# Or deploy only LASAN (after infrastructure exists)
azd deploy mcp-lasan
```

This will:
1. Build the Docker image
2. Push to Azure Container Registry
3. Deploy to Azure Container Apps
4. Output the service URI

**View deployment outputs:**
```bash
azd env get-values

# Get LASAN URI
azd env get-value mcpLasanUri
```

### Option 2: Manual Docker Deployment

If you need to deploy manually:

```bash
# From this directory (src/mcp-servers/lasan)
cd src/mcp-servers/lasan

# Build image
docker build -t aldelarcspcr.azurecr.io/mcp-lasan:latest .

# Login to ACR
az acr login --name aldelarcspcr

# Push image
docker push aldelarcspcr.azurecr.io/mcp-lasan:latest
```

### Verify Deployment

Test the deployed server:

```bash
# Get the deployed URL
MCP_URI=$(azd env get-value mcpLasanUri)

# Test with client
cd src/mcp-servers/lasan
MCP_SERVER_HOST="${MCP_URI#https://}" MCP_SERVER_PORT="443" uv run python mcp_client_lasan.py
```

## Local Development

### Build Container Locally

```bash
# Build the image
docker build -t mcp-lasan:latest .

# Run container
docker run -p 8000:8000 --env-file .env mcp-lasan:latest
```

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_HOST` | Server host | localhost |
| `MCP_SERVER_PORT` | Server port | 8000 |
| `LASAN_API_ENDPOINT` | LASAN API endpoint | - |
| `LASAN_API_KEY` | LASAN API key | - |

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
