# Citizen Services Portal

## Overview

A modern, AI-powered digital platform designed to transform how citizens interact with government services. This project aims to increase operational efficiency while building transparency and trust into public sector organizations through intelligent automation, seamless service delivery, and accessible self-service capabilities.

**Industry:** Public Sector & Smart Cities  
**Primary Goal:** Deliver digital-first government services that meet citizen expectations while reducing administrative overhead

---

## Overarching Deliverable

This project focuses on **selecting and showcasing high-impact government use cases** in a comprehensive, production-ready manner. The deliverable encompasses:

- **Use Case Selection & Implementation**: Identify citizen service scenarios with the highest potential for AI-driven transformation
- **Production-Grade Architecture**: Deploy scalable, resilient infrastructure on Azure following cloud best practices
- **Enterprise Security**: Implement identity management, data protection, compliance controls (GDPR, accessibility standards)
- **Comprehensive Testing Strategy**: Unit, integration, end-to-end, and accessibility testing
- **Observability & Monitoring**: Application insights, logging, alerting, and performance tracking
- **Documentation & Knowledge Transfer**: Technical documentation, runbooks, and citizen-facing guides

The goal is to demonstrate what's possible when modern AI capabilities meet citizen services, providing a blueprint for government digital transformation.

---

## Use Cases

This section catalogs potential citizen service scenarios for AI-powered transformation. Use cases are evaluated based on impact, frequency, and current pain points.

| Use Case Name | Description | Current Pain Points |
|--------------|-------------|-------------------|
| **Building Permits & Renovations** | Submit and track applications for construction, remodeling, or home improvement permits | Lengthy approval process (weeks to months), complex documentation requirements, unclear status updates, in-person submissions |
| **Business License Applications** | Apply for new business licenses or renew existing ones | Multi-department coordination, confusing requirements, manual document review, long processing times |
| **Property Tax Inquiries & Payments** | Check assessment values, understand tax bills, make payments, file appeals | Complex terminology, limited payment options, difficult appeal process, lack of transparency in assessments |
| **Utility Connection & Disconnection** | Request water, electricity, or waste services for new residences or businesses | Multiple point-of-contact, scheduling delays, lack of coordination between utilities, redundant paperwork |
| **Vital Records Requests** | Obtain birth certificates, death certificates, marriage licenses | In-person or mail-only requests, processing delays, identity verification challenges, notarization requirements |
| **School Enrollment & Registration** | Register children for public schools, submit required documents, track enrollment status | District boundary confusion, missing document notifications, limited enrollment windows, manual verification |
| **Parking Permits & Violations** | Apply for residential/visitor parking permits, contest parking tickets | Limited online access, manual application review, unclear violation appeal processes, payment friction |
| **Waste & Recycling Services** | Schedule bulk pickup, report missed collections, understand recycling rules | Unclear schedules, inconsistent service, limited reporting channels, confusion about acceptable materials |
| **Public Records Requests** | Submit FOIA/public records requests, track status, receive documents | Manual request processing, unclear timelines, inconsistent responses, limited online access |
| **Address Changes & Updates** | Update address across all government departments and services | Multiple separate updates required, inconsistent systems, voter registration disconnected, missed notifications |
| **Code Violation Reporting** | Report property maintenance issues, abandoned vehicles, illegal dumping | Limited reporting channels, no follow-up updates, slow response times, unclear resolution process |


---

## Business Challenge

Citizens expect digital-first government services, but many agencies still rely on outdated systems that are slow, fragmented, and resource-intensive. Long queues, inconsistent communication, and limited self-service options erode trust in public institutions.

Without AI-enabled citizen engagement, governments face rising costs, lower satisfaction scores, and widening gaps between public expectations and delivered services.

---

## Expected Outcomes

By deploying AI-powered citizen service portals, governments can deliver consistent, accessible, and responsive experiences. Residents access services faster, while agencies reduce administrative overhead and improve transparency.

**Long-term Impact:**
- Stronger citizen trust and satisfaction
- Reduced operational costs
- More digitally mature public sector
- Improved accessibility and equity in service delivery

---

## AI Infusion Point

AI-driven virtual assistants handling routine inquiries and guiding citizens through complex service applications, providing 24/7 support in multiple languages with personalized guidance based on citizen context and history.

---

---

# Infrastructure

## Azure Services

The solution is built on a modern, AI-first Azure architecture optimized for intelligent citizen services:

### Foundation Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Azure AI Foundry** | AI development platform with Hub + Project for building and deploying agents | Basic tier, models: gpt-5-mini, gpt-5.2 |
| **Azure API Management** | AI Gateway for model endpoints, request throttling, token governance | Standard tier |
| **Azure AI Search** | Vector and semantic search for citizen knowledge base, FAQs, policy documents | Standard S1 (1 replica, 1 partition) |
| **Azure Cosmos DB** | NoSQL database for agent memory (conversation history) and citizen operational data | Serverless, Session consistency |
| **Azure Content Safety** | Content moderation, PII detection, and ethical AI guardrails | S0 tier |
| **Azure Container Apps** | Host MCP servers, web applications, and background services | CPU-based autoscaling, scale-to-zero |

### Supporting Infrastructure

| Service | Purpose |
|---------|---------|
| **Container Registry** | Store and manage container images for Container Apps |
| **Key Vault** | Secure secrets, connection strings, API keys with RBAC |
| **Log Analytics + Application Insights** | Centralized logging, APM, distributed tracing |
| **Managed Identity** | Service-to-service authentication without credentials |
| **Storage Account** | Required dependency for AI Foundry Hub |

### Architecture Highlights

- **Region:** North Central US
- **Network:** Public endpoints with security controls (VNet integration planned for production)
- **Deployment:** Infrastructure as Code (Bicep) with Azure Developer CLI (azd)

**Key Integration:** API Management is configured as the AI Gateway within the Foundry Project, providing centralized access to AI models (gpt-5-mini, gpt-5.2) with built-in governance, rate limiting, and token tracking.

For detailed infrastructure documentation, see [infrastructure.md](infrastructure.md).

---

## Repository Structure

```
citizen-services-portal/
├── README.md                           # This file - project overview and getting started
├── infrastructure.md                   # Detailed infrastructure design and decisions
├── architecture.md                     # Solution architecture and design patterns
├── azure.yaml                          # Azure Developer CLI configuration
│
├── infra/                              # Infrastructure as Code (Bicep)
│   ├── main.bicep                      # Main orchestration template
│   ├── main.parameters.json            # Environment parameters
│   ├── abbreviations.json              # Azure resource naming conventions
│   ├── README.md                       # Deployment guide and troubleshooting
│   │
│   └── core/                           # Reusable Bicep modules
│       ├── ai/                         # AI services (Foundry, Search, Content Safety)
│       ├── data/                       # Data services (Cosmos DB, Storage)
│       ├── host/                       # Container Apps hosting
│       ├── gateway/                    # API Management
│       ├── security/                   # Key Vault, Managed Identity
│       └── monitor/                    # Log Analytics, App Insights
│
├── src/                                # Application code (future)
│   ├── mcp-servers/                    # MCP server implementations
│   ├── web/                            # Web application frontends
│   └── agents/                         # AI agent workflows
│
└── docs/                               # Additional documentation
    ├── use-cases.md                    # Detailed use case specifications
    ├── story-line.md                   # Project narrative and vision
    └── presentation-approach.md        # Demo and presentation guide
```

---

## How to Deploy

This section provides step-by-step instructions to deploy the Citizen Services Portal infrastructure to Azure.

### Prerequisites

Before deploying, ensure you have:

1. **Azure Subscription** with Owner or Contributor + User Access Administrator permissions
2. **Azure CLI** (version 2.50.0 or later) - [Install Guide](https://learn.microsoft.com/cli/azure/install-azure-cli)
3. **Azure Developer CLI (azd)** - [Install Guide](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
4. **Git** (for cloning the repository)

### Deployment Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_ORG/citizen-services-portal.git
cd citizen-services-portal
```

#### 2. Authenticate with Azure

```bash
# Login to Azure CLI
az login

# Login to Azure Developer CLI (may use same credentials)
azd auth login

# Verify you're in the correct subscription
az account show
```

#### 3. Initialize azd Environment

```bash
# Initialize azd environment (first time only)
azd init

# When prompted:
# - Environment name: dev (or your preferred name)
```

#### 4. Provision Infrastructure

```bash
# Deploy all Azure resources
azd provision

# When prompted (first time only):
# - Location: northcentralus (or choose from: eastus, eastus2, westus2, westus3)
# 
# This will:
# - Create resource group 'csp'
# - Deploy all foundation services (Foundry, APIM, Cosmos DB, etc.)
# - Configure monitoring and security
# - Take approximately 15-20 minutes
```

**Note:** azd saves location and subscription in `.azure/<env-name>/.env` - you won't be prompted again on subsequent deployments.

#### 5. Verify Deployment

```bash
# Check deployment status
azd show

# List deployed resources
az resource list --resource-group aldelar-csp --output table

# View saved environment values
azd env get-values
```

#### 6. Post-Deployment Configuration

**Manual Step Required - Configure AI Gateway:**

The AI Gateway integration between API Management and Foundry Project must be configured manually:

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to your Foundry Project resource (name will be in azd output)
3. Navigate to **Settings** → **AI Gateway**
4. Click **Configure Gateway**
5. Select the API Management instance that was deployed
6. Save the configuration

This enables model access (gpt-5-mini, gpt-5.2) through the APIM AI Gateway.


### Validation

After deployment, validate the infrastructure:

```bash
# Check resource group exists
az group show --name csp

# Verify key resources
az resource list \
  --resource-group csp \
  --query "[].{Name:name, Type:type, Location:location}" \
  --output table

# Test API Management is accessible
APIM_NAME=$(az apim list --resource-group csp --query "[0].name" -o tsv)
az apim show --name $APIM_NAME --resource-group csp

# Test Cosmos DB is accessible
COSMOS_NAME=$(az cosmosdb list --resource-group csp --query "[0].name" -o tsv)
az cosmosdb show --name $COSMOS_NAME --resource-group csp
```

### Troubleshooting

**Issue:** `azd provision` fails with permission errors
- **Solution:** Ensure your account has Owner or Contributor + User Access Administrator role

**Issue:** Region not available for certain services
- **Solution:** Try alternative regions: `eastus`, `eastus2`, `westus2`, `westus3`

**Issue:** Quota exceeded for AI services
- **Solution:** Request quota increase via Azure Portal → Quotas → Cognitive Services

**Issue:** Resource names already exist
- **Solution:** Resources are named using unique tokens. If conflicts occur, delete existing resources or modify `resourceToken` in main.bicep

For detailed troubleshooting, see [infra/README.md](infra/README.md).

### Clean Up

To remove all deployed resources:

```bash
# Using azd (recommended)
azd down

# Or using Azure CLI
az group delete --name csp --yes --no-wait
```

---

## Next Steps

After successful deployment:

1. ✅ Configure AI Gateway (manual step - see Post-Deployment Configuration above)
2. 📝 Define Cosmos DB containers for agent memory and citizen data
3. 🔧 Build and deploy MCP servers to Container Apps
4. 🌐 Develop citizen portal web application
5. 🤖 Create AI agents and workflows in Foundry
6. 🚀 Set up CI/CD pipeline for automated deployments

---
