# LADBS MCP Server

Model Context Protocol (MCP) server for Los Angeles Department of Building and Safety (LADBS) services.

## Overview

This MCP server provides tools for interacting with LADBS services, including:
- Building permit applications
- Permit status inquiries
- Inspection scheduling
- Violation reporting

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
# Navigate to the LADBS MCP server directory
cd src/mcp-servers/ladbs

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
uv run python mcp_server_ladbs.py
```

Server will start on `http://localhost:8000`

### Test the Server

```bash
# In a separate terminal, run the test client
uv run python mcp_client_ladbs.py
```

## Development

### Project Structure

```
ladbs/
├── mcp_server_ladbs.py      # Main server entry point
├── mcp_client_ladbs.py      # Test client
├── src/                      # Implementation
│   ├── tools.py             # MCP tools definitions
│   ├── models.py            # Pydantic models
│   ├── services.py          # Business logic
│   └── config.py            # Configuration
└── tests/                    # Unit tests
```

### Adding New Tools

1. Define tool function in `src/tools.py`
2. Register with FastMCP in `mcp_server_ladbs.py`
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

## Docker

### Build Container

```bash
# Build the image
docker build -t mcp-ladbs:latest .

# Run container
docker run -p 8000:8000 --env-file .env mcp-ladbs:latest
```

### Deploy to Azure Container Apps

See the main repository documentation for Azure deployment instructions.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_HOST` | Server host | localhost |
| `MCP_SERVER_PORT` | Server port | 8000 |
| `LADBS_API_ENDPOINT` | LADBS API endpoint | - |
| `LADBS_API_KEY` | LADBS API key | - |

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
