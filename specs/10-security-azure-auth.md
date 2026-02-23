# Security Specification: Azure AD Authentication & Identity Flow

This document specifies the authentication architecture for the Citizen Services Portal using **Microsoft Entra ID** (Azure AD), covering the web application, CSP Agent, and MCP servers.

---

## 1. Overview

### 1.1 Goals

- **Secure citizen access** to the web application using Microsoft Entra ID
- **Propagate user identity** through the system (Web App → Agent → MCP Servers)
- **Enable per-user data isolation** in Cosmos DB (projects/plans scoped to user)
- **Support both development and production** scenarios
- **Maintain zero-trust principles** for inter-service communication

### 1.2 Current State

| Component | Current Auth | Identity Propagation |
|-----------|-------------|---------------------|
| Web App | Mock auth (local) / Easy Auth ready | User ID in Cosmos queries |
| CSP Agent | None (internal) | No user context |
| MCP Servers | None (internal) | No user context |

### 1.3 Target State

| Component | Target Auth | Identity Propagation |
|-----------|-------------|---------------------|
| Web App | Easy Auth (Entra ID) | User claims from headers |
| CSP Agent | Managed Identity + User context header | Forward user claims |
| MCP Servers | Managed Identity verification | Receive user context |

---

## 2. Architecture Options

### 2.1 Option A: Easy Auth + Header Propagation (Recommended)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CITIZEN BROWSER                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Azure Container Apps - Web App                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Easy Auth Middleware                             │   │
│  │         (Microsoft-managed, zero-code authentication)                 │   │
│  │                                                                       │   │
│  │  • Redirects unauthenticated users to Entra ID login                 │   │
│  │  • Validates tokens automatically                                     │   │
│  │  • Injects user identity headers:                                     │   │
│  │    - X-MS-CLIENT-PRINCIPAL-ID (user object ID)                       │   │
│  │    - X-MS-CLIENT-PRINCIPAL-NAME (email/UPN)                          │   │
│  │    - X-MS-TOKEN-AAD-ACCESS-TOKEN (if configured)                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       NiceGUI Web Application                         │   │
│  │                                                                       │   │
│  │  • Reads user identity from Easy Auth headers                        │   │
│  │  • Stores user context in session                                    │   │
│  │  • Propagates user ID in all downstream calls                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ X-User-Context header
                                    │ (signed or verified via internal network)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Azure Container Apps - CSP Agent                          │
│                                                                              │
│  • Receives user context via X-User-Context header                          │
│  • Uses Managed Identity for Azure OpenAI, Cosmos DB                        │
│  • Propagates user context to MCP servers                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ X-User-Context header
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Azure Container Apps - MCP Servers                        │
│                                                                              │
│  • Receives user context for data filtering                                 │
│  • Uses Managed Identity for Azure resources (AI Search, Cosmos DB)         │
│  • Applies user-scoped queries                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Zero-code authentication at the web app level
- Simple header propagation within trusted Container Apps Environment
- All services in same VNet, no external token exchange needed
- Easy Auth handles token refresh automatically

**Cons:**
- User context header not cryptographically signed (relies on network isolation)
- No true end-to-end token for MCP servers

---

### 2.2 Option B: On-Behalf-Of (OBO) Token Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CITIZEN BROWSER                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS + Entra ID Token
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Web App (with Easy Auth)                                  │
│                                                                              │
│  • Receives user access token via Easy Auth                                 │
│  • Exchanges user token for Agent-scoped token (OBO flow)                   │
│  • Calls Agent with delegated token                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Authorization: Bearer <delegated-token>
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CSP Agent (with Entra auth)                               │
│                                                                              │
│  • Validates delegated token (verifies user identity)                       │
│  • Extracts user claims from token                                          │
│  • Exchanges for MCP-scoped token (another OBO)                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Authorization: Bearer <mcp-delegated-token>
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MCP Servers (with Entra auth)                             │
│                                                                              │
│  • Validates token and extracts user context                                │
│  • Applies user-scoped data access                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Cryptographically verified user identity at every hop
- True delegation - MCP servers can verify the actual user
- Audit trail shows real user identity at each service
- Required for production/multi-tenant scenarios

**Cons:**
- Complex setup (multiple App Registrations with OBO permissions)
- Token caching and refresh logic required
- Latency from token exchanges
- More Entra ID configuration

---

### 2.3 Option C: API Management Gateway with JWT Validation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CITIZEN BROWSER                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Azure API Management                                      │
│                                                                              │
│  • JWT validation policy                                                    │
│  • Rate limiting                                                            │
│  • Request routing                                                          │
│  • Injects validated claims into headers                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            ┌───────────────┐               ┌───────────────┐
            │   Web App     │               │   CSP Agent   │
            └───────────────┘               └───────────────┘
```

**Pros:**
- Centralized authentication policy
- APIM already provisioned in infrastructure
- Rich policy capabilities (rate limiting, caching, transformation)
- Single point of token validation

**Cons:**
- Adds latency through APIM
- More complex routing configuration
- APIM needs careful sizing for production

---

## 3. Recommended Approach: Phased Implementation

### Phase 1: Easy Auth + Header Propagation (MVP)

**Goal:** Secure web app with Entra ID, propagate user identity via headers

**Components:**
1. Enable Easy Auth on Web App Container App
2. Create App Registration in Entra ID
3. Parse Easy Auth headers in NiceGUI
4. Propagate user context to Agent/MCP via custom header

**Timeline:** 1-2 days

### Phase 2: Secure Internal Communication (Production-Ready)

**Goal:** Add authentication between services within Container Apps Environment

**Components:**
1. Enable Easy Auth on CSP Agent (validates internal calls)
2. Web App obtains token for Agent using Managed Identity client credentials
3. Agent validates calling identity (Web App's Managed Identity)

**Timeline:** 2-3 days

### Phase 3: On-Behalf-Of Flow (Enterprise)

**Goal:** True user delegation through all services

**Components:**
1. Configure OBO permissions in App Registrations
2. Implement token exchange in Web App
3. Implement token validation in Agent and MCP servers

**Timeline:** 3-5 days

---

## 4. Phase 1 Implementation Details

### 4.1 Entra ID App Registration

Create a single App Registration for the Web App:

```
App Registration: "Citizen Services Portal"
├── Application (client) ID: <client-id>
├── Directory (tenant) ID: <tenant-id>
├── Redirect URIs:
│   ├── https://<webapp-fqdn>/.auth/login/aad/callback
│   └── http://localhost:8080/.auth/login/aad/callback (dev)
├── Implicit grant: ID tokens ✓
├── Supported account types: Single tenant (or multi-tenant)
└── API Permissions:
    ├── Microsoft Graph: User.Read (delegated)
    └── (optional) openid, profile, email
```

### 4.2 Web App Easy Auth Configuration

Update `infra/app/webapp.bicep`:

```bicep
// Easy Auth configuration
resource containerAppAuthConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = if (enableAuthentication) {
  name: 'current'
  parent: containerApp
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'azureactivedirectory'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          openIdIssuer: 'https://login.microsoftonline.com/${tenantId}/v2.0'
          clientId: appClientId
          clientSecretSettingName: 'microsoft-provider-authentication-secret'
        }
        validation: {
          allowedAudiences: [
            'api://${appClientId}'
            appClientId
          ]
        }
        login: {
          loginParameters: ['scope=openid profile email']
        }
      }
    }
    login: {
      tokenStore: {
        enabled: true
      }
      preserveUrlFragmentsForLogins: true
    }
  }
}
```

### 4.3 Reading User Identity in Web App

Update `src/web-app/services/auth_service.py`:

```python
"""Authentication service for the Citizen Services Portal."""

import base64
import json
from typing import Optional
from pydantic import BaseModel
from nicegui import app
from config import settings


class UserIdentity(BaseModel):
    """User identity from Entra ID."""
    user_id: str           # Object ID (oid claim)
    email: str             # Email or UPN
    name: str              # Display name
    tenant_id: str = ""    # Tenant ID
    roles: list[str] = []  # App roles (if configured)


def get_current_user() -> Optional[UserIdentity]:
    """Get current user from Easy Auth headers or mock for local dev."""
    
    if settings.USE_MOCK_AUTH:
        return UserIdentity(
            user_id=settings.MOCK_USER_ID,
            email=settings.MOCK_USER_EMAIL,
            name=settings.MOCK_USER_NAME,
        )
    
    # Easy Auth injects these headers after authentication
    request = app.storage.request_headers
    
    # Primary headers
    principal_id = request.get('x-ms-client-principal-id')
    principal_name = request.get('x-ms-client-principal-name')
    
    if not principal_id:
        return None
    
    # Parse the full principal for additional claims
    principal_b64 = request.get('x-ms-client-principal')
    roles = []
    tenant_id = ""
    display_name = principal_name.split('@')[0] if principal_name else 'User'
    
    if principal_b64:
        try:
            principal_json = base64.b64decode(principal_b64).decode('utf-8')
            principal = json.loads(principal_json)
            
            # Extract claims
            claims = {c['typ']: c['val'] for c in principal.get('claims', [])}
            display_name = claims.get('name', display_name)
            tenant_id = claims.get('tid', '')
            
            # Extract roles
            roles = [c['val'] for c in principal.get('claims', []) 
                    if c['typ'] == 'roles']
        except Exception:
            pass  # Fall back to basic identity
    
    return UserIdentity(
        user_id=principal_id,
        email=principal_name or '',
        name=display_name,
        tenant_id=tenant_id,
        roles=roles,
    )
```

### 4.4 User Context Header for Downstream Services

Define a standard header for propagating user context:

```python
# src/shared/auth/user_context.py

import json
import base64
import hmac
import hashlib
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone


class UserContext(BaseModel):
    """User context propagated between services."""
    user_id: str
    email: str
    name: str
    tenant_id: str = ""
    timestamp: str = ""  # ISO timestamp for freshness validation
    
    def to_header(self, secret: str = "") -> str:
        """Encode user context for header transmission."""
        self.timestamp = datetime.now(timezone.utc).isoformat()
        payload = self.model_dump_json()
        encoded = base64.b64encode(payload.encode()).decode()
        
        if secret:
            # Sign for integrity (optional, adds security within internal network)
            signature = hmac.new(
                secret.encode(), 
                encoded.encode(), 
                hashlib.sha256
            ).hexdigest()[:16]
            return f"{encoded}.{signature}"
        
        return encoded
    
    @classmethod
    def from_header(cls, header: str, secret: str = "") -> Optional["UserContext"]:
        """Decode user context from header."""
        try:
            if secret and '.' in header:
                encoded, signature = header.rsplit('.', 1)
                expected = hmac.new(
                    secret.encode(), 
                    encoded.encode(), 
                    hashlib.sha256
                ).hexdigest()[:16]
                if not hmac.compare_digest(signature, expected):
                    return None
            else:
                encoded = header
            
            payload = base64.b64decode(encoded).decode()
            return cls.model_validate_json(payload)
        except Exception:
            return None


# Header name constant
USER_CONTEXT_HEADER = "X-User-Context"
```

### 4.5 Agent Service Client with User Context

Update `src/web-app/services/agent_service.py`:

```python
"""CSP Agent client with user context propagation."""

import httpx
from typing import Optional
from config import settings
from services.auth_service import get_current_user
from shared.auth.user_context import UserContext, USER_CONTEXT_HEADER


class AgentService:
    def __init__(self):
        self.base_url = settings.CSP_AGENT_URL
    
    def _get_headers(self) -> dict:
        """Build headers including user context."""
        headers = {"Content-Type": "application/json"}
        
        user = get_current_user()
        if user:
            context = UserContext(
                user_id=user.user_id,
                email=user.email,
                name=user.name,
                tenant_id=user.tenant_id,
            )
            headers[USER_CONTEXT_HEADER] = context.to_header(
                secret=settings.USER_CONTEXT_SECRET  # Optional signing
            )
        
        return headers
    
    async def send_message(self, message: str, project_id: str) -> dict:
        """Send message to agent with user context."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/responses",
                headers=self._get_headers(),
                json={
                    "input": message,
                    "project_id": project_id,
                }
            )
            return response.json()
```

### 4.6 Agent: Receiving User Context

Update the CSP Agent to parse and use user context:

```python
# src/agents/csp-agent/middleware/auth.py

from fastapi import Request, HTTPException
from shared.auth.user_context import UserContext, USER_CONTEXT_HEADER
from config import settings


async def get_user_context(request: Request) -> UserContext:
    """Extract user context from request headers."""
    
    header = request.headers.get(USER_CONTEXT_HEADER)
    
    if not header:
        if settings.REQUIRE_USER_CONTEXT:
            raise HTTPException(status_code=401, detail="User context required")
        # Return anonymous context for development
        return UserContext(
            user_id="anonymous",
            email="anonymous@local",
            name="Anonymous",
        )
    
    context = UserContext.from_header(
        header, 
        secret=settings.USER_CONTEXT_SECRET
    )
    
    if not context:
        raise HTTPException(status_code=401, detail="Invalid user context")
    
    return context
```

---

## 5. Data Isolation by User

### 5.1 Cosmos DB Query Patterns

All queries should include user_id filter:

```python
# Query projects for current user
def get_user_projects(user_id: str) -> list[Project]:
    query = """
        SELECT * FROM c 
        WHERE c.user_id = @user_id 
        ORDER BY c.updated_at DESC
    """
    return container.query_items(
        query=query,
        parameters=[{"name": "@user_id", "value": user_id}]
    )
```

### 5.2 Partition Strategy

Current Cosmos DB design uses `user_id` as partition key for `projects` container:

```
Container: projects
├── Partition Key: /user_id
└── Items: { id, user_id, name, description, plan, ... }

Container: messages
├── Partition Key: /project_id
└── Items: { id, project_id, user_id, role, content, ... }
```

This ensures efficient queries scoped to a user.

---

## 6. Security Considerations

### 6.1 Network Security

| Layer | Control |
|-------|---------|
| Container Apps Environment | Internal VNet with private endpoints |
| Inter-service communication | Internal ingress only (Agent, MCP) |
| External access | Web App only via HTTPS |
| Azure resources | Private endpoints for Cosmos DB, AI Search |

### 6.2 Secrets Management

| Secret | Storage | Access |
|--------|---------|--------|
| App Registration Client Secret | Key Vault → Container App Secret | Web App only |
| User Context Signing Key | Key Vault → Environment Variable | All services |
| Cosmos DB | Managed Identity | RBAC |
| Azure OpenAI | Managed Identity | RBAC |

### 6.3 Token Security (Easy Auth)

| Setting | Value | Rationale |
|---------|-------|-----------|
| Token store | Enabled | Secures tokens server-side |
| Token refresh | Automatic | Easy Auth handles refresh |
| Session cookie | HttpOnly, Secure | Prevents XSS access |
| CORS | Web App origin only | Prevents cross-origin attacks |

---

## 7. Local Development

### 7.1 Mock Authentication

For local development without Azure, use mock auth:

```bash
# .env
USE_MOCK_AUTH=true
MOCK_USER_ID=dev-user-001
MOCK_USER_EMAIL=developer@localhost
MOCK_USER_NAME=Local Developer
```

### 7.2 Testing with Real Entra ID (Optional)

For testing auth flow locally:

1. Register a local redirect URI: `http://localhost:8080/.auth/login/aad/callback`
2. Use Azure CLI to get tokens: `az account get-access-token`
3. Inject headers manually or use a local auth proxy

---

## 8. Configuration Summary

### 8.1 Environment Variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `USE_MOCK_AUTH` | Web App | Enable/disable mock auth |
| `ENTRA_CLIENT_ID` | Web App | App Registration client ID |
| `ENTRA_CLIENT_SECRET` | Web App | App Registration secret (Key Vault ref) |
| `ENTRA_TENANT_ID` | All | Azure AD tenant ID |
| `USER_CONTEXT_SECRET` | All | HMAC signing key for user context |
| `REQUIRE_USER_CONTEXT` | Agent, MCP | Enforce user context in requests |

### 8.2 Bicep Parameters

```bicep
// main.parameters.json additions
{
  "enableWebAppAuthentication": { "value": true },
  "entraClientId": { "value": "<from-keyvault>" },
  "entraClientSecret": { "value": "<from-keyvault>" }
}
```

---

## 9. Future Considerations

### 9.1 Multi-Tenant Support

If supporting multiple organizations:
- Configure App Registration for multi-tenant
- Add tenant validation logic
- Consider tenant-specific data isolation

### 9.2 Role-Based Access Control

Future app roles could include:
- `Citizen` - Standard user access
- `Agent` - Customer service representative
- `Admin` - Administrative functions

### 9.3 B2C for External Citizens

For true citizen-facing scenarios:
- Azure AD B2C for consumer identity
- Social identity providers (Google, Facebook)
- Self-service registration
- Custom branding

---

## 10. Decision Points for Discussion

### 10.1 Internal Service Authentication

**Question:** Should Agent and MCP servers require authentication for internal calls?

| Option | Complexity | Security | Recommendation |
|--------|------------|----------|----------------|
| Network isolation only | Low | Medium | ✓ MVP |
| Managed Identity client credentials | Medium | High | Production |
| Full OBO delegation | High | Highest | Enterprise |

### 10.2 User Context Signing

**Question:** Should the X-User-Context header be cryptographically signed?

| Option | Complexity | Security | Recommendation |
|--------|------------|----------|----------------|
| No signing (trusted network) | Low | Medium | MVP |
| HMAC signing | Low | High | ✓ Recommended |
| JWT with asymmetric keys | High | Highest | Enterprise |

### 10.3 Session Duration

**Question:** How long should user sessions last?

| Option | UX | Security | Recommendation |
|--------|-----|----------|----------------|
| 1 hour | Poor | High | Not recommended |
| 8 hours | Good | Medium | ✓ Default |
| 24 hours | Best | Lower | With re-auth for sensitive ops |

### 10.4 Anonymous Access

**Question:** Should any functionality be available without authentication?

| Option | Use Case | Recommendation |
|--------|----------|----------------|
| No anonymous access | All features require login | ✓ Recommended |
| Anonymous browsing | View public info only | Future consideration |
| Guest mode | Limited functionality | Not recommended |

---

## 11. Implementation Checklist

### Phase 1: Easy Auth MVP

- [ ] Create Entra ID App Registration
- [ ] Add client secret to Key Vault
- [ ] Update `webapp.bicep` with auth parameters
- [ ] Implement `auth_service.py` header parsing
- [ ] Add `UserContext` header propagation
- [ ] Update Agent to parse user context
- [ ] Update MCP servers to receive user context
- [ ] Test end-to-end flow
- [ ] Update local dev documentation

### Phase 2: Secure Internal Communication

- [ ] Enable Easy Auth on Agent Container App
- [ ] Implement Managed Identity token acquisition in Web App
- [ ] Validate calling identity in Agent
- [ ] Add authentication middleware to MCP servers

### Phase 3: Enterprise Features

- [ ] Implement OBO token flow
- [ ] Add app roles in Entra ID
- [ ] Implement RBAC in application
- [ ] Consider B2C for citizen access
