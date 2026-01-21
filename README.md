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
| **Azure AI Foundry** | AI development platform (NEW Foundry) with Hub + Project for building and deploying agents | Project: citizen-services-portal, Models: gpt-5-mini, gpt-5.2, text-embedding-3-small (Global Standard, 1M TPM) |
| **Azure API Management** | AI Gateway for model endpoints + MCP service proxy with request throttling, token governance | Standard tier, APIs: /ai/v1 (models), /mcp/v1 (services) |
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
| **Storage Account** | Required dependency for AI Foundry |

### Architecture Highlights

- **Region:** North Central US
- **Network:** Public endpoints with security controls (VNet integration planned for production)
- **Deployment:** Infrastructure as Code (Bicep) with Azure Developer CLI (azd)

**Key Integration:** API Management is configured as the AI Gateway within the Foundry Project, providing centralized access to AI models (gpt-5-mini, gpt-5.2, text-embedding-3-small) and MCP servers (LADBS) with built-in governance, rate limiting, and token tracking.

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

#### 4. Deploy Infrastructure and Services

**Option A: Deploy Everything (Infrastructure + MCP Servers)**

```bash
# Deploy all Azure resources and services
azd up

# When prompted (first time only):
# - Location: northcentralus (or choose from: eastus, eastus2, westus2, westus3)
# 
# This will:
# - Create resource group 'csp'
# - Deploy all foundation services (Foundry, APIM, Cosmos DB, etc.)
# - Build and deploy LADBS MCP server
# - Configure monitoring and security
# - Take approximately 20-25 minutes
```

**Option B: Deploy Infrastructure Only**

```bash
# Provision infrastructure without deploying services
azd provision

# When prompted (first time only):
# - Location: northcentralus (or choose from: eastus, eastus2, westus2, westus3)
# 
# Takes approximately 15-20 minutes
```

**Option C: Deploy Individual Services**

```bash
# Deploy only LADBS (after infrastructure exists)
azd deploy mcp-ladbs
```

**Note:** azd saves location and subscription in `.azure/<env-name>/.env` - you won't be prompted again on subsequent deployments.

#### 5. Verify Deployment

```bash
# Check deployment status
azd show

# List deployed resources
az resource list --resource-group csp --output table

# View saved environment values
azd env get-values

# Get LADBS MCP Server URI (if deployed)
azd env get-value mcpLadbsUri
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

## MCP Servers

Model Context Protocol (MCP) servers provide specialized tools for AI agents to interact with government services.

### LADBS MCP Server

The **Los Angeles Department of Building and Safety (LADBS)** MCP server provides tools for building permits, inspections, and code violations.

**Tools Available:**
- `submit_permit_application` - Submit building permit applications
- `check_permit_status` - Check status of existing permits
- `schedule_inspection` - Schedule building inspections
- `report_violation` - Report code violations

**Location:** `src/mcp-servers/ladbs/`  
**Documentation:** [src/mcp-servers/ladbs/README.md](src/mcp-servers/ladbs/README.md)

---

## AI Agents

AI agents built using Azure AI Foundry Agent Service, connecting to models via APIM AI Gateway and tools via MCP servers.

### LADBS Assistant

The **LADBS AI Agent** helps citizens with building permits, inspections, and code violations using conversational AI.

**Capabilities:**
- Submit permit applications with guided data collection
- Check permit status and review timeline
- Schedule inspections with preferred dates
- Report code violations (anonymously or with contact info)

**Configuration:**
- **Model:** gpt-5.2 (accessed via APIM AI Gateway)
- **Tools:** mcp-ladbs (LADBS MCP server via APIM)
- **Deployment:** Automated via `azd provision` (postprovision hook)

**Location:** `src/agents/ladbs/`  
**Test Agent:** [Azure AI Foundry Portal](https://ai.azure.com/build/projects/citizen-services-portal/agents)

For agent details and manual deployment, see [src/agents/ladbs/README.md](src/agents/ladbs/README.md).

---

## Next Steps

After successful deployment:

1. ✅ Configure AI Gateway (manual step - see Post-Deployment Configuration above)
2. ✅ LADBS MCP Server deployed and accessible via APIM
3. ✅ LADBS AI Agent deployed to Foundry Agent Service
4. 📝 Define Cosmos DB containers for agent memory and citizen data
5. 🔧 Build additional MCP servers (permits, utilities, etc.)
6. 🌐 Develop citizen portal web application
7. 🤖 Test and refine agents in Foundry Playground
8. 🚀 Set up CI/CD pipeline for automated deployments

---
