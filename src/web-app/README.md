# Citizen Services Portal - Web Application

The Citizen Services Portal Web Application is built with NiceGUI and provides a chat-first interface for citizens to navigate multi-agency government processes.

## Features

- **Three-panel layout**: Projects list, Chat interface, and Plan visualization
- **Mock data**: Pre-populated with sample projects and messages for testing
- **Mermaid DAG visualization**: Dynamic graph showing project plan steps and dependencies
- **User action cards**: Interactive cards for tasks that require user action

## Quick Start

### Prerequisites

- Python 3.12+
- UV package manager (https://docs.astral.sh/uv/)

### Local Development

```bash
# Navigate to web-app directory
cd src/web-app

# Install dependencies
uv sync

# Run the application
uv run python main.py

# Open http://localhost:8080 in your browser
```

### Docker

```bash
# Build the Docker image
docker build -t csp-webapp .

# Run the container
docker run -p 8080:8080 csp-webapp

# Open http://localhost:8080 in your browser
```

## Project Structure

```
src/web-app/
├── main.py                  # Entry point
├── pyproject.toml           # UV config
├── requirements.txt         # For Docker
├── Dockerfile
├── config.py               # Configuration
├── models/                 # Pydantic data models
│   ├── user.py
│   ├── project.py
│   └── message.py
├── components/             # UI components
│   ├── projects_panel.py
│   ├── project_card.py
│   ├── chat_panel.py
│   ├── plan_widget.py
│   ├── status_chips.py
│   └── user_action_card.py
├── services/               # Backend services
│   ├── auth_service.py
│   └── mock_data.py
└── pages/                  # Page routes
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_MOCK_AUTH` | `true` | Use mock authentication |
| `MOCK_USER_ID` | `local-dev-user` | Mock user ID |
| `MOCK_USER_EMAIL` | `dev@example.com` | Mock user email |
| `NICEGUI_PORT` | `8080` | Server port |
| `NICEGUI_HOST` | `0.0.0.0` | Server host |

## Mock Data

The application includes mock data for testing:

- **User**: John Smith (john.smith@example.com)
- **Projects**: 
  - Home Renovation (80% complete, with action needed)
  - Bulk Pickup (100% complete)
- **Plan steps**: P1-P3 (permits), U1-U2 (utility), I1 (inspection), F1 (final)
- **Sample messages**: Conversation history for the Home Renovation project
