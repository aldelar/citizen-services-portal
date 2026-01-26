# Citizen Services Portal - Infrastructure

This directory contains the Azure infrastructure as code (IaC) using Bicep for the Citizen Services Portal project.

## Structure

```
infra/
├── main.bicep                 # Main orchestration file (subscription scope)
├── main.parameters.json       # Environment parameters
├── abbreviations.json         # Azure resource naming conventions
│
├── core/                      # Reusable infrastructure modules
│   ├── ai/
│   │   ├── foundry.bicep             # AI Foundry
│   │   ├── foundry-project.bicep     # AI Foundry Project  
│   │   ├── ai-search.bicep           # Azure AI Search
│   │   └── content-safety.bicep      # Content Safety
│   │
│   ├── data/
│   │   ├── cosmos-db.bicep           # Cosmos DB (NoSQL)
│   │   └── storage-account.bicep     # Storage Account
│   │
│   ├── host/
│   │   ├── container-apps-environment.bicep
│   │   ├── container-app.bicep
│   │   └── container-registry.bicep
│   │
│   ├── gateway/
│   │   └── api-management.bicep      # API Management (AI Gateway)
│   │
│   ├── security/
│   │   ├── key-vault.bicep
│   │   └── managed-identity.bicep
│   │
│   └── monitor/
│       └── monitoring.bicep          # Log Analytics + App Insights
│
└── app/                       # Application-specific modules (future)
    ├── mcp-servers.bicep
    └── web-apps.bicep
```

## Prerequisites

1. **Azure CLI** - [Install](https://learn.microsoft.com/cli/azure/install-azure-cli)
2. **Azure Developer CLI (azd)** - [Install](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
3. **Azure Subscription** with appropriate permissions
4. **Principal ID** - Your Azure AD user/service principal ID

## Deployment

### Initialize Environment

```bash
# From repository root
azd auth login

# Initialize environment - sets environment name
azd init
```

### Deploy Infrastructure

```bash
# Provision all resources (will prompt for location on first deployment)
azd provision
```

**Note:** Location and subscription selections are saved in `.azure/<env-name>/.env` and automatically reused for all future deployments.

### Post-Deployment Configuration

**AI Gateway Setup (Manual Step Required):**

The AI Gateway configuration linking API Management to the Foundry Project must be completed manually:

1. Navigate to Azure Portal
2. Go to: Foundry Project → Settings → AI Gateway
3. Select the API Management instance that was deployed
4. Configure gateway policies for model endpoints (gpt-5-mini, gpt-5.2)

This step will be automated when ARM/Bicep support is available.

## Deployed Resources

| Resource | Purpose | SKU/Tier | Region |
|----------|---------|----------|--------|
| Resource Group | `csp` | N/A | North Central US |
| AI Foundry | AI development workspace | Basic | North Central US |
| AI Foundry Project | Agent/workflow environment | Basic | North Central US |
| AI Search | Vector/semantic search | Standard S1 | North Central US |
| API Management | AI Gateway for models | Standard | North Central US |
| Container Apps | MCP servers, web apps | Consumption | North Central US |
| Content Safety | Content moderation | S0 | North Central US |
| **Content Understanding** | **Document processing for KB** | **S0** | **West US** |
| Cosmos DB | Agent memory + data | Serverless | North Central US |
| Key Vault | Secrets management | Standard | North Central US |
| Log Analytics | Centralized logging | PerGB2018 | North Central US |
| Application Insights | APM & tracing | Web | North Central US |
| Container Registry | Container images | Basic | North Central US | North Central US |
| Storage Account | Foundry dependency | Standard LRS | North Central US |

**Region Note:** Content Understanding (`aldelar-csp-cu-westus`) is deployed in West US because the Content Understanding API is only available in specific regions (westus, swedencentral, australiaeast). All other resources are deployed in North Central US.

## Configuration

### Environment-Specific Parameters

Edit `main.parameters.json` to customize deployment:

```json
{
  "environmentName": { "value": "dev" },
  "location": { "value": "northcentralus" },
  "principalId": { "value": "<your-principal-id>" }
}
```

### Region Selection

**Current:** North Central US (supports AI Foundry capabilities)

**Alternatives:** East US, East US 2, West US 2, West US 3

### Scaling Configuration

- **AI Search:** 1 replica, 1 partition (adjustable)
- **API Management:** 1 unit Standard tier
- **Container Apps:** CPU-based autoscaling (0.5-10 instances)
- **Cosmos DB:** Serverless (auto-scaling RU/s)

## Cost Estimation

**Monthly estimate (Dev environment):**

- API Management Standard: ~$650
- AI Search Standard S1: ~$250
- Cosmos DB Serverless: ~$25-100 (usage-based)
- Container Apps: ~$20-50 (scale-to-zero)
- Storage + Misc: ~$50
- **Total: ~$1,000-1,100/month**

## Security

- **Authentication:** Azure AD + Managed Identities
- **Secrets:** Stored in Key Vault
- **Network:** Public endpoints with IP restrictions
- **RBAC:** Least privilege access
- **TLS:** Enforced (minimum TLS 1.2)

## Troubleshooting

### Deployment Failures

```bash
# Check deployment status
az deployment sub show --name <deployment-name>

# View deployment logs
az monitor activity-log list --resource-group csp
```

### Validate Bicep

```bash
# Lint all bicep files
az bicep build --file infra/main.bicep

# What-if analysis
az deployment sub what-if \
  --location northcentralus \
  --template-file infra/main.bicep \
  --parameters infra/main.parameters.json
```

## Cleanup

```bash
# Delete all resources
azd down

# Or manually delete resource group
az group delete --name csp --yes
```

## Next Steps

1. ✅ Infrastructure deployed
2. ⏭️ Configure AI Gateway in Foundry Project (manual)
3. ⏭️ Deploy MCP servers to Container Apps
4. ⏭️ Create Cosmos DB containers for agent memory
5. ⏭️ Set up CI/CD pipeline (GitHub Actions)

## References

- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-studio/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [API Management AI Gateway](https://learn.microsoft.com/azure/api-management/api-management-using-with-ai)
