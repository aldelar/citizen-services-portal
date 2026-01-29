# Azure Services Reference

| Service Type | Azure Resource Name | Azure Region | Description |
|--------------|------|--------|-------------|
| Resource Group | `csp` | North Central US | Citizen Services Portal resources |
| Container App | `aldelar-csp-mcp-ladbs` | North Central US | LADBS MCP Server |
| Container App | `aldelar-csp-mcp-ladwp` | North Central US | LADWP MCP Server |
| Container App | `aldelar-csp-mcp-lasan` | North Central US | LASAN MCP Server |
| Container App | `aldelar-csp-mcp-csp` | North Central US | CSP MCP Server (plans, analytics) |
| Container Apps Environment | `aldelar-csp-cae` | North Central US | Hosts all Container Apps |
| Container Registry | `aldelarcspcr` | North Central US | aldelarcspcr.azurecr.io |
| AI Foundry | `aldelar-csp-foundry` | North Central US | Main AI hub with OpenAI models |
| Cognitive Services | `aldelar-csp-cu-westus` | West US | Content Understanding (West US for API availability) |
| Content Safety | `aldelar-csp-contentsafety` | North Central US | Content moderation |
| AI Search | `aldelar-csp-search` | North Central US | Knowledge base vector search |
| Cosmos DB | `aldelar-csp-cosmos` | North Central US | Agent memory (serverless) |
| Storage Account | `aldelarcspstorage` | North Central US | Blob storage for documents |
| API Management | `aldelar-csp-apim` | North Central US | AI Gateway (https://aldelar-csp-apim.azure-api.net) |
| Key Vault | `aldelar-csp-kv` | North Central US | Secrets management |
| Managed Identity | `aldelar-csp-identity` | North Central US | Service authentication |
| Application Insights | `aldelar-csp-insights` | North Central US | Application monitoring |
| Log Analytics | `aldelar-csp-log` | North Central US | Centralized logging |

## Model Deployments

### On `aldelar-csp-foundry` (Main AI Hub)

| Deployment | Model | Version |
|------------|-------|---------|
| `gpt-4.1-mini` | gpt-4.1-mini | 2025-04-14 |
| `gpt-4.1` | gpt-4.1 | 2025-04-14 |
| `text-embedding-3-small` | text-embedding-3-small | 1 |

### On `aldelar-csp-cu-westus` (Content Understanding)

| Deployment | Model | Version |
|------------|-------|---------|
| `gpt-4.1-mini` | gpt-4.1-mini | 2025-04-14 |
| `gpt-4.1` | gpt-4.1 | 2025-04-14 |
| `text-embedding-3-large` | text-embedding-3-large | 1 |