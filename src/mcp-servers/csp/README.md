# CSP MCP Server (Citizen Services Portal)

Model Context Protocol (MCP) server for plan lifecycle management and step analytics.

## Overview

This MCP server provides tools for:
- **Plan Lifecycle Management**: Create, update, and track project plans
- **Step Status Tracking**: Update step statuses with automatic timing capture
- **Analytics**: Query historical completion data for realistic estimates
- **Rework Handling**: Support for rework scenarios with chain-based duration tracking

## Tools

### Plan Lifecycle Tools

| Tool | Type | Action | Key Inputs | Returns |
|------|------|--------|------------|---------|
| `plan.get` | Query | Get current plan | `projectId`, `userId` | Complete plan with steps |
| `plan.create` | **Automated** | Create new plan | `projectId`, `userId`, `title`, `steps` | Created plan with estimates |
| `plan.update` | **Automated** | Update full plan | `projectId`, `userId`, `steps` | Updated plan |
| `plan.updateStep` | **Automated** | Update single step | `projectId`, `userId`, `stepId`, `status`, `result?` | Updated step with action card |

### Analytics Tools

| Tool | Type | Action | Key Inputs | Returns |
|------|------|--------|------------|---------|
| `steps.getAverageDuration` | Query | Get average duration | `stepType` | Average days, sample count |

### Step Status Values

| Status | Description |
|--------|-------------|
| `defined` | Step created but not started (initial state) |
| `scheduled` | Step scheduled to begin (starts timing) |
| `in_progress` | Step actively being worked on |
| `completed` | Step finished successfully (stops timing, logs completion) |
| `needs_rework` | Step failed and requires retry |
| `rejected` | Step permanently blocked/cancelled |

### Step Types

| stepType | Description |
|----------|-------------|
| `permits.submit` | Permit application (any type) |
| `inspection.schedule` | Schedule an inspection |
| `tou.enroll` | TOU rate enrollment |
| `interconnection.submit` | Solar interconnection application |
| `rebates.apply` | Rebate application |
| `pickup.schedule` | Waste pickup scheduling |
| `user.action` | Manual user action required |

### How It Works

1. **Creating a Plan**: Agent calls `plan.create` with project ID, title, and steps. The service auto-populates `estimated_duration_days` from historical data.

2. **Updating Step Status**: Agent calls `plan.updateStep` with step ID and new status. Timing is automatic:
   - → `scheduled` or `in_progress`: sets `started_at`
   - → `completed`, `needs_rework`, or `rejected`: sets `completed_at` and logs to analytics

3. **Rework Handling**: When a step fails:
   - Call `plan.updateStep` with status `needs_rework`
   - Call `plan.update` adding a new step with `supersedes` pointing to the failed step
   - Chain duration is calculated across all attempts

4. **UI Refresh Signal**: After updating a step, emit `<<PLAN_UPDATED:project_id>>` to trigger UI refresh.

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
# Navigate to the CSP MCP server directory
cd src/mcp-servers/csp

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
# Run the server
uv run python mcp_server_csp.py
```

Server will start on `http://localhost:8000`

### Test the Server

```bash
# In a separate terminal, run the test client
uv run python mcp_client_csp.py
```

## Development

### Project Structure

```
csp/
├── mcp_server_csp.py        # Main server entry point
├── mcp_client_csp.py        # Test client
├── src/                      # Implementation
│   ├── tools.py             # MCP tools definitions
│   ├── models.py            # Pydantic models
│   ├── services.py          # Business logic
│   ├── config.py            # Configuration
│   └── repositories/        # Data access layer
│       ├── project_repository.py       # Plan CRUD in csp DB
│       └── step_completion_repository.py # Step timing in csp DB
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

The CSP MCP server uses a single CosmosDB database:

### csp Database

| Container | Partition Key | Content |
|-----------|---------------|----------|
| `projects` | `/userId` | Project documents with embedded plan and steps |
| `step_completions` | `/stepType` | Completed step timing data for analytics |
| `users` | `/id` | User profile data |
| `messages` | `/projectId` | Message history |

## Deployment

The server is deployed as an Azure Container App via the infrastructure templates in `/infra/app/mcp-csp.bicep`.

See the main project README for deployment instructions.
