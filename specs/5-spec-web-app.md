# Web Application Specification

This document provides the comprehensive technical specification for the **Citizen Services Portal Web Application**, including deployment configuration, authentication, local development setup, and integration patterns.

---

## 1. Overview

### 1.1 Purpose

The Web Application is the citizen-facing frontend for the Citizen Services Portal. It provides:

- **Chat Interface**: Primary interaction point with the CSP Agent
- **Project Management**: Track multi-step government service journeys
- **Plan Visualization**: Dynamic DAG view of project steps
- **User Account**: Profile management and preferences

### 1.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **UI Framework** | NiceGUI | Python-native, Vue.js/Quasar components, FastAPI integration |
| **Runtime** | Python 3.12 | Consistency with MCP servers |
| **Styling** | Tailwind CSS + Quasar | Built into NiceGUI |
| **Package Manager** | UV | Fast, modern Python package management |
| **Containerization** | Docker | Azure Container Apps compatibility |
| **Deployment** | Azure Container Apps | Existing infrastructure |
| **Authentication** | Easy Auth (Built-in Authentication) | Zero-code Azure-native auth |

### 1.3 Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  Citizen Services Portal                                   │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌───────────────┐                                                                          │
│  │    Web App    │                                                                          │
│  │     :8080     │                                                                          │
│  └───────┬───────┘                                                                          │
│          │                                                                                  │
│          ▼                                                                                  │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           CSP Agent (Microsoft Foundry)                                │ │
│  └───────┬───────────────────────┬───────────────────────┬───────────────────┬───────────┘ │
│          │                       │                       │                   │              │
│          ▼                       ▼                       ▼                   ▼              │
│  ┌───────────────┐       ┌───────────────┐       ┌───────────────┐   ┌───────────────┐     │
│  │  MCP LADBS    │       │  MCP LADWP    │       │  MCP LASAN    │   │ MCP Reporting │     │
│  │    :8000      │       │    :8000      │       │    :8000      │   │     :8000     │     │
│  └───────────────┘       └───────────────┘       └───────────────┘   └───────────────┘     │
│                                                                                             │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│                                    Foundation Services                                      │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│        ┌───────────────────────────┐            ┌───────────────────────────┐              │
│        │     Azure AI Search       │            │        Cosmos DB          │              │
│        │     (Knowledge Base)      │            │    (citizen-services)     │              │
│        └───────────────────────────┘            └───────────────────────────┘              │
│                                                                                             │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

---


## 2. Project Structure

```
src/webapp/
├── main.py                     # NiceGUI app entry point
├── pyproject.toml              # UV/Python project config
├── requirements.txt            # Python dependencies (for Docker)
├── Dockerfile                  # Container definition
├── .env.example                # Environment variable template
├── config.py                   # Configuration management
│
├── models/                     # Pydantic data models
│   ├── __init__.py
│   ├── user.py                 # User model
│   ├── project.py              # Project and Plan models
│   └── message.py              # Chat message models
│
├── pages/                      # NiceGUI page routes
│   ├── __init__.py
│   ├── main_page.py            # Main app page (/)
│   ├── auth.py                 # Login redirect handling
│   └── profile.py              # User profile page (/profile)
│
├── components/                 # Reusable UI components
│   ├── __init__.py
│   ├── header.py               # App header with user menu
│   ├── projects_panel.py       # Left drawer - projects list
│   ├── chat_panel.py           # Center - chat interface
│   ├── plan_widget.py          # Right drawer - plan visualization
│   ├── status_chips.py         # Status indicator components
│   ├── user_action_card.py     # User action cards
│   └── project_card.py         # Project list cards
│
├── services/                   # Backend integrations
│   ├── __init__.py
│   ├── cosmos_service.py       # CosmosDB client
│   ├── agent_service.py        # CSP Agent API client
│   └── auth_service.py         # Easy Auth identity parsing
│
└── static/                     # Static assets
    └── logo.svg
```

---

## 3. Authentication

### 3.1 Azure Container Apps Easy Auth

The web application uses **Azure Container Apps Built-in Authentication** (Easy Auth) for zero-code authentication. This provides:

- Microsoft Entra ID (Azure AD) authentication
- Optional social providers (Google, Facebook, etc.)
- Automatic token management
- User identity injection via headers

### 3.2 How It Works

```
┌─────────────┐     ┌────────────────────────┐     ┌─────────────┐
│   Browser   │────▶│  Easy Auth Middleware  │────▶│   Web App   │
│             │     │  (Azure-managed)       │     │  (NiceGUI)  │
└─────────────┘     └────────────────────────┘     └─────────────┘
                              │
                              │ Injects headers:
                              │ - X-MS-CLIENT-PRINCIPAL-NAME
                              │ - X-MS-CLIENT-PRINCIPAL-ID
                              │ - X-MS-TOKEN-AAD-ACCESS-TOKEN
                              ▼
```

### 3.3 Bicep Configuration

Add to the Container App Bicep definition:

```bicep
resource webapp 'Microsoft.App/containerApps@2024-03-01' = {
  name: webappName
  location: location
  properties: {
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
      }
    }
    // ... other config
  }
}

// Easy Auth configuration
resource webappAuth 'Microsoft.App/containerApps/authConfigs@2024-03-01' = {
  parent: webapp
  name: 'current'
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: entraAppClientId
          clientSecretSettingName: 'MICROSOFT_PROVIDER_AUTHENTICATION_SECRET'
          openIdIssuer: 'https://login.microsoftonline.com/${tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: [
            'api://${entraAppClientId}'
          ]
        }
      }
    }
  }
}
```

### 3.4 Reading User Identity in Code

```python
# services/auth_service.py
from nicegui import app
from typing import Optional
from pydantic import BaseModel

class UserIdentity(BaseModel):
    """User identity from Easy Auth headers."""
    user_id: str
    email: str
    name: str
    
def get_current_user() -> Optional[UserIdentity]:
    """Extract user identity from Easy Auth headers."""
    request = app.native.request
    
    principal_id = request.headers.get('X-MS-CLIENT-PRINCIPAL-ID')
    principal_name = request.headers.get('X-MS-CLIENT-PRINCIPAL-NAME')
    
    if not principal_id:
        return None
    
    return UserIdentity(
        user_id=principal_id,
        email=principal_name or '',
        name=principal_name.split('@')[0] if principal_name else 'User'
    )
```

### 3.5 Local Development Without Auth

For local development, Easy Auth is not available. Use mock authentication:

```python
# config.py
import os

class Settings:
    # When running locally, use mock auth
    USE_MOCK_AUTH: bool = os.getenv('USE_MOCK_AUTH', 'true').lower() == 'true'
    MOCK_USER_ID: str = os.getenv('MOCK_USER_ID', 'local-dev-user')
    MOCK_USER_EMAIL: str = os.getenv('MOCK_USER_EMAIL', 'dev@example.com')
```

```python
# services/auth_service.py
from config import Settings

def get_current_user() -> Optional[UserIdentity]:
    """Get current user - mock for local dev, Easy Auth for Azure."""
    if Settings.USE_MOCK_AUTH:
        return UserIdentity(
            user_id=Settings.MOCK_USER_ID,
            email=Settings.MOCK_USER_EMAIL,
            name='Local Developer'
        )
    
    # Easy Auth headers (Azure deployment)
    # ... (see above)
```

---

## 4. Local Development

### 4.1 Prerequisites

- **Python 3.12+**
- **UV** package manager (https://docs.astral.sh/uv/)
- **Docker** (optional, for container testing)
- **Azure CLI** with active subscription (for AI Search access)

### 4.2 Port Allocation

To run all services locally without conflicts, use the following port assignments:

| Service | Port | URL |
|---------|------|-----|
| **Web App** | 8080 | http://localhost:8080 |
| **MCP LADBS** | 8001 | http://localhost:8001 |
| **MCP LADWP** | 8002 | http://localhost:8002 |
| **MCP LASAN** | 8003 | http://localhost:8003 |
| **MCP Reporting** | 8004 | http://localhost:8004 |

### 4.3 Environment Setup

Create environment files for each service:

#### Web App (.env)

```bash
# src/webapp/.env
USE_MOCK_AUTH=true
MOCK_USER_ID=local-dev-user
MOCK_USER_EMAIL=dev@example.com

# Backend URLs (local MCP servers)
MCP_LADBS_URL=http://localhost:8001
MCP_LADWP_URL=http://localhost:8002
MCP_LASAN_URL=http://localhost:8003
MCP_REPORTING_URL=http://localhost:8004

# Agent URL (if running locally, otherwise use Azure)
AGENT_URL=http://localhost:8090

# CosmosDB (use Azure - no local emulator needed for dev)
COSMOS_ENDPOINT=https://<your-cosmos-account>.documents.azure.com:443/
COSMOS_DATABASE=citizen-services

# Azure AI Search (always Azure - no local option)
AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
```

#### MCP Server (.env) - Example for LADBS

```bash
# src/mcp-servers/ladbs/.env
MCP_SERVER_PORT=8001

# Azure AI Search (always Azure)
AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_INDEX_NAME=ladbs-kb

# CosmosDB (use Azure)
COSMOS_ENDPOINT=https://<your-cosmos-account>.documents.azure.com:443/
COSMOS_DATABASE=ladbs
```

### 4.4 Running Locally

#### Option A: Run All Services (Recommended for Full Testing)

Use a shell script to start all services:

```bash
#!/bin/bash
# scripts/run-local.sh

# Start MCP servers in background
echo "Starting MCP servers..."

cd src/mcp-servers/ladbs
MCP_SERVER_PORT=8001 uv run python mcp_server_ladbs.py &
LADBS_PID=$!

cd ../ladwp
MCP_SERVER_PORT=8002 uv run python mcp_server_ladwp.py &
LADWP_PID=$!

cd ../lasan
MCP_SERVER_PORT=8003 uv run python mcp_server_lasan.py &
LASAN_PID=$!

cd ../reporting
MCP_SERVER_PORT=8004 uv run python mcp_server_reporting.py &
REPORTING_PID=$!

echo "MCP servers started on ports 8001-8004"

# Start web app in foreground
cd ../../webapp
echo "Starting web app on port 8080..."
uv run python main.py

# Cleanup on exit
trap "kill $LADBS_PID $LADWP_PID $LASAN_PID $REPORTING_PID 2>/dev/null" EXIT
```

Make it executable:
```bash
chmod +x scripts/run-local.sh
./scripts/run-local.sh
```

#### Option B: Run Web App Only (Use Azure MCP Servers)

If you just want to work on the UI and use deployed MCP servers:

```bash
# Set environment to use Azure-deployed services
export MCP_LADBS_URL=https://<deployed-ladbs-url>
export MCP_LADWP_URL=https://<deployed-ladwp-url>
export MCP_LASAN_URL=https://<deployed-lasan-url>

cd src/webapp
uv run python main.py
```

### 4.5 UV Project Setup

Each service uses UV with a `pyproject.toml`:

```toml
# src/webapp/pyproject.toml
[project]
name = "csp-webapp"
version = "0.1.0"
description = "Citizen Services Portal Web Application"
requires-python = ">=3.12"
dependencies = [
    "nicegui>=2.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "azure-cosmos>=4.7.0",
    "azure-identity>=1.17.0",
]

[project.scripts]
csp-webapp = "main:main"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

First-time setup:
```bash
cd src/webapp
uv sync
```

### 4.6 Quick Development Cycle

For rapid iteration on the web app:

```bash
# Terminal 1: Run web app with hot reload
cd src/webapp
uv run python main.py --reload

# Terminal 2: (Optional) Run a single MCP server if needed
cd src/mcp-servers/ladbs
MCP_SERVER_PORT=8001 uv run python mcp_server_ladbs.py
```

NiceGUI supports hot reload for UI changes. Just save your file and the browser refreshes automatically.

---

## 5. Docker Configuration

### 5.1 Dockerfile

```dockerfile
# src/webapp/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install UV for dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml .
COPY requirements.txt .

# Install dependencies
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Environment variables
ENV NICEGUI_PORT=8080
ENV NICEGUI_HOST=0.0.0.0
ENV USE_MOCK_AUTH=false

# Run the application
CMD ["python", "main.py"]
```

### 5.2 requirements.txt

Generate from pyproject.toml for Docker builds:

```bash
cd src/webapp
uv pip compile pyproject.toml -o requirements.txt
```

### 5.3 Local Docker Testing

```bash
cd src/webapp

# Build the image
docker build -t csp-webapp .

# Run with environment variables
docker run -p 8080:8080 \
  -e COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/ \
  -e MCP_LADBS_URL=http://host.docker.internal:8001 \
  csp-webapp

# Open http://localhost:8080
```

---

## 6. Azure Deployment

### 6.1 Infrastructure (Bicep)

Add the web app to the existing infrastructure:

```bicep
// infra/app/webapp.bicep
param name string
param location string = resourceGroup().location
param containerAppsEnvironmentId string
param containerRegistryName string
param imageName string = 'webapp'
param imageTag string = 'latest'
param cosmosEndpoint string
param entraAppClientId string
param tenantId string = tenant().tenantId

resource webapp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
      }
      registries: [
        {
          server: '${containerRegistryName}.azurecr.io'
          identity: 'system'
        }
      ]
      secrets: [
        {
          name: 'microsoft-provider-authentication-secret'
          value: entraAppClientSecret
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'webapp'
          image: '${containerRegistryName}.azurecr.io/${imageName}:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'COSMOS_ENDPOINT', value: cosmosEndpoint }
            { name: 'USE_MOCK_AUTH', value: 'false' }
            // MCP URLs injected by main.bicep
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Easy Auth configuration
resource webappAuth 'Microsoft.App/containerApps/authConfigs@2024-03-01' = {
  parent: webapp
  name: 'current'
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: entraAppClientId
          clientSecretSettingName: 'microsoft-provider-authentication-secret'
          openIdIssuer: 'https://login.microsoftonline.com/${tenantId}/v2.0'
        }
      }
    }
  }
}

output webappUrl string = 'https://${webapp.properties.configuration.ingress.fqdn}'
```

### 6.2 Update azure.yaml

Add the webapp service to `azure.yaml`:

```yaml
services:
  # ... existing MCP servers ...
  
  webapp:
    project: ./src/webapp
    language: py
    host: containerapp
    docker:
      path: ./Dockerfile
      context: .
      registry: ${AZURE_CONTAINER_REGISTRY_NAME}.azurecr.io
```

### 6.3 Deployment Commands

#### Full Deployment (Infrastructure + Apps)

```bash
# Deploy everything
azd up
```

#### Web App Only (After Infrastructure Exists)

```bash
# Deploy just the webapp service
azd deploy webapp
```

#### Test the Deployment

```bash
# Get the webapp URL
azd env get-value SERVICE_WEBAPP_URI

# Open in browser
open $(azd env get-value SERVICE_WEBAPP_URI)
```

---

## 7. Configuration Reference

### 7.1 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USE_MOCK_AUTH` | No | `true` | Use mock authentication (local dev) |
| `MOCK_USER_ID` | No | `local-dev-user` | Mock user ID for local dev |
| `MOCK_USER_EMAIL` | No | `dev@example.com` | Mock email for local dev |
| `COSMOS_ENDPOINT` | Yes | - | CosmosDB account endpoint |
| `COSMOS_DATABASE` | No | `citizen-services` | CosmosDB database name |
| `MCP_LADBS_URL` | Yes | - | LADBS MCP server URL |
| `MCP_LADWP_URL` | Yes | - | LADWP MCP server URL |
| `MCP_LASAN_URL` | Yes | - | LASAN MCP server URL |
| `MCP_REPORTING_URL` | Yes | - | Reporting MCP server URL |
| `AGENT_URL` | Yes | - | CSP Agent endpoint |
| `NICEGUI_PORT` | No | `8080` | Port for NiceGUI server |
| `NICEGUI_HOST` | No | `0.0.0.0` | Host binding |

### 7.2 Config Class

```python
# src/webapp/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Auth
    use_mock_auth: bool = True
    mock_user_id: str = "local-dev-user"
    mock_user_email: str = "dev@example.com"
    
    # Server
    nicegui_port: int = 8080
    nicegui_host: str = "0.0.0.0"
    
    # Backend services
    cosmos_endpoint: str
    cosmos_database: str = "citizen-services"
    
    mcp_ladbs_url: str
    mcp_ladwp_url: str
    mcp_lasan_url: str
    mcp_reporting_url: str
    
    agent_url: str

settings = Settings()
```

---

## 8. UI Reference

The UI implementation follows the wireframes in `/docs/ui-wireframes/`:

| Wireframe | Purpose | Key Components |
|-----------|---------|----------------|
| `ui-wireframes-overview.md` | Three-panel layout | `ui.header`, `ui.left_drawer`, `ui.right_drawer` |
| `ui-wireframes-chat.md` | Chat interface | `ui.chat_message`, `ui.scroll_area` |
| `ui-wireframes-projects.md` | Projects panel | `ui.card`, `ui.linear_progress` |
| `ui-wireframes-plan-widget.md` | Plan DAG | `ui.mermaid` |
| `ui-wireframes-components.md` | Component library | `ui.chip`, `ui.button`, `ui.expansion` |
| `ui-wireframes-user-actions.md` | User action cards | `ui.expansion`, `ui.checkbox` |
| `ui-wireframes-user-account.md` | Account pages | `ui.input`, `ui.card` |

---

## 9. Summary

| Aspect | Implementation |
|--------|---------------|
| **Framework** | NiceGUI (Python) |
| **Authentication** | Azure Container Apps Easy Auth |
| **Local Dev Auth** | Mock authentication with `USE_MOCK_AUTH=true` |
| **Package Manager** | UV |
| **Ports** | Webapp: 8080, MCP servers: 8001-8004 |
| **Local Run** | `./scripts/run-local.sh` or `uv run python main.py` |
| **Docker Build** | `docker build -t csp-webapp .` |
| **Azure Deploy** | `azd up` or `azd deploy webapp` |
