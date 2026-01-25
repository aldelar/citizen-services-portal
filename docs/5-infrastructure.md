# Azure Infrastructure - Citizen Services Portal

## Landing Zone Overview

This document defines the Azure infrastructure foundation for the Citizen Services Portal, a production-grade AI-powered platform for government digital services.

**Deployment Tool:** Azure Developer CLI (azd)  
**Infrastructure as Code:** Bicep  
**Scope:** Subscription-level deployment with dedicated resource group  
**Environment:** Development (single environment)  
**Region:** North Central US  
**Network Architecture:** Public endpoints with security controls (VNet integration planned for future phase)

---

## Foundation Services

### 1. Resource Group
- **Name:** `csp`
- **Purpose:** Logical container for all project resources
- **Environment:** Development
- **Lifecycle:** Managed via azd

### 2. Azure AI Foundry
- **Components:**
  - AI Foundry (workspace for AI development)
  - AI Foundry Project (scoped environment for agents/workflows)
- **Models:** gpt-5-mini, gpt-5.2
- **Integration:** API Management configured as AI Gateway in Foundry Resource
- **Model Access:** All model endpoints exposed through APIM Gateway
- **Purpose:** Centralized AI development platform with governance
- **Note:** APIM must be registered as AI Gateway in Foundry Project configuration

### 3. Azure AI Search
- **Tier:** Standard S1
- **Purpose:** Vector search, semantic search for citizen knowledge base
- **Use Cases:** Document retrieval, FAQ matching, policy search
- **Expected Scale:** MVP - low to moderate query volume

### 4. Azure API Management
- **Tier:** Standard (sufficient for public endpoints)
- **Role:** AI Gateway for model endpoints
- **Functions:**
  - Request throttling and rate limiting
  - Token usage tracking and governance
  - API versioning and security
- **Note:** Premium tier only required for VNet integration (future phase)

### 5. Azure Container Apps
- **Workloads:**
  - MCP (Model Context Protocol) servers
  - Web application frontends
  - Background processing services
- **Environment:** Shared Container Apps Environment
- **Scaling:** CPU threshold-based autoscaling
- **Network:** Public endpoints with ingress controls

### 6. Azure Content Safety
- **Purpose:** Content moderation and PII detection
- **Integration:** Pre/post-processing pipeline for agent interactions
- **Compliance:** GDPR, accessibility, ethical AI guardrails
- **Network:** Public endpoint

### 7. Azure Cosmos DB
- **Purpose:** 
  - Agent memory store (conversation history, context)
  - Citizen operational data (requests, status tracking)
- **API:** NoSQL (document model)
- **Configuration:** Resource created, collections defined in application deployment phase
- **Consistency:** Session (default - good balance for this use case)

---

## Supporting Infrastructure

### Monitoring & Observability
- **Log Analytics Workspace:** Centralized logging
- **Application Insights:** APM and distributed tracing
- **Dashboard:** Unified view of agent performance, API usage, citizen interactions

### Security & Identity
- **Key Vault:** Secrets, connection strings, API keys
- **Managed Identities:** Service-to-service authentication
- **RBAC:** Principle of least privilege

### Networking (Future Phase)
- **Current State:** Public endpoints with IP restrictions, managed identities, Key Vault
- **VNet Integration Path:**
  - Virtual Network with subnets for Container Apps, private endpoints
  - Private Endpoints for: Cosmos DB, AI Search, Key Vault, Container Registry
  - API Management Premium (required for VNet injection)
  - NSGs and route tables for traffic control
- **Impact of Starting Public:**
  - ✅ **Faster deployment** - no subnet planning, NSG configuration
  - ✅ **Lower cost** - Standard APIM vs Premium (~$2.5k/month savings)
  - ✅ **Simpler troubleshooting** - direct connectivity for debugging
  - ⚠️ **Migration effort** - ~2-3 days to retrofit VNet integration
  - ⚠️ **Temporary exposure** - mitigated by Key Vault, RBAC, IP allowlists
  - ⚠️ **APIM tier upgrade** - requires recreation or in-place upgrade (30-45 min downtime)
- **Mitigation Strategy:**
  - Use Managed Identities (no secrets in transit)
  - Enable Azure DDoS Protection Standard on future VNet
  - Implement IP restrictions on all PaaS services
  - Use Azure Front Door WAF when adding VNet

---

## Proposed Bicep Structure

```
infra/
├── main.bicep                          # Entry point (subscription scope)
├── main.parameters.json                # Environment-specific parameters
├── abbreviations.json                  # Azure resource naming abbreviations
│
├── core/                               # Reusable modules
│   ├── ai/
│   │   ├── foundry.bicep              # AI Foundry
│   │   ├── foundry-project.bicep      # AI Foundry Project
│   │   ├── ai-search.bicep            # Azure AI Search
│   │   └── content-safety.bicep       # Content Safety service
│   │
│   ├── data/
│   │   └── cosmos-db.bicep            # Cosmos DB account + databases
│   │
│   ├── host/
│   │   ├── container-apps-environment.bicep
│   │   ├── container-app.bicep        # Reusable container app module
│   │   └── container-registry.bicep
│   │
│   ├── gateway/
│   │   └── api-management.bicep       # APIM instance + AI Gateway config
│   │
│   ├── security/
│   │   ├── key-vault.bicep
│   │   └── managed-identity.bicep
│   │
│   └── monitor/
│       └── monitoring.bicep           # Log Analytics + App Insights
│
├── app/                                # Application-specific deployments
│   ├── mcp-servers.bicep              # MCP server container apps
│   └── web-apps.bicep                 # Citizen portal web apps
│
└── README.md                           # Deployment instructions
```

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Region** | North Central US | Supports AI Foundry Hosted Agents capability |
| **Environment Strategy** | Single Dev environment | Simplify initial deployment, expand to staging/prod later |
| **Resource Group** | `csp` | Single logical container for all resources |
| **AI Search Tier** | Standard S1 | Right-sized for MVP with moderate query load |
| **API Management Tier** | Standard | Sufficient for public endpoints; Premium only needed for VNet |
| **Cosmos DB API** | NoSQL | Flexible document model for agent memory + citizen data |
| **Cosmos Collections** | Defer to app phase | Define containers/partitions during app deployment |
| **Network Architecture** | Public endpoints | Faster deployment; VNet retrofit planned for production phase |
| **Foundry Models** | gpt-5-mini, gpt-5.2 | Accessed through APIM AI Gateway for governance and scale |
| **Container Scaling** | CPU threshold | Resource-based autoscaling for predictable performance |

---

## VNet Integration Impact Analysis

### Starting Public (Current Approach)

**Benefits:**
- Deploy in 1-2 days vs 1-2 weeks
- Standard APIM tier saves ~$2,500/month
- Simplified debugging and troubleshooting
- No subnet CIDR planning or IP exhaustion issues

**Risks (Mitigated):**
- Services exposed to internet → **Mitigated by:** IP allowlists, RBAC, Managed Identities, Key Vault
- Data in transit over public network → **Mitigated by:** TLS 1.3, service-managed certificates
- Broader attack surface → **Mitigated by:** Azure DDoS Basic, API Management policies

**Migration Path to VNet:**
- Estimated effort: 2-3 days
- Steps: Create VNet → Enable private endpoints → Upgrade APIM to Premium → Update DNS
- Downtime: 30-45 minutes for APIM tier change (can be scheduled)

### Recommendation
✅ **Proceed with public endpoints** for MVP/Dev environment. Security controls (Key Vault, Managed Identities, IP restrictions) provide adequate protection. VNet integration is a tactical upgrade, not architectural rework

---

## Cost Optimization Considerations

- **Cosmos DB:** Serverless mode for MVP (pay per request vs provisioned RU/s)
- **AI Search:** Standard S1 with no reserved capacity initially
- **API Management:** Standard tier (~$650/month vs Premium ~$3,150/month)
- **Container Apps:** Scale-to-zero for MCP servers during off-hours
- **Model Selection:** Use gpt-5-mini for non-critical workloads, gpt-5.2 for complex reasoning
- **Application Insights:** 5GB/month free tier, then sampling to control costs

---

## Next Steps

1. **Review & Refine:** Discuss open questions and finalize service tiers
2. **Define Parameters:** Create environment-specific parameters (dev, prod)
3. **Write Bicep Modules:** Implement core modules following proposed structure
4. **azd Configuration:** Create `azure.yaml` for azd deployment workflow
5. **Deploy & Test:** Validate infrastructure in dev environment
6. **CI/CD Integration:** Automate deployments via GitHub Actions

---

## References

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [API Management as AI Gateway](https://learn.microsoft.com/azure/api-management/api-management-using-with-ai)
- [azd Templates](https://learn.microsoft.com/azure/developer/azure-developer-cli/azd-templates)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Cosmos DB Best Practices](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
