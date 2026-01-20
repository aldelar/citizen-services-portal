# Deploy MCP Weather Service to Azure Container Apps

This guide explains how to deploy the MCP Weather Service to Azure Container Apps using Azure Developer CLI (azd).

## Prerequisites

- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
- An Azure subscription
- Docker installed locally (for testing)

## Quick Start

### 1. Initialize the environment

```bash
azd auth login
azd init
```

When prompted:
- Environment name: Choose a unique name (e.g., `mcp-weather-dev`)
- Azure location: Select your preferred region (e.g., `eastus`)

### 2. Deploy to Azure

```bash
azd up
```

This command will:
- Create an Azure Resource Group
- Set up a Container Apps Environment
- Create a Container Registry
- Build and push your Docker image
- Deploy the container app
- Set up monitoring with Log Analytics and Application Insights

### 3. Get the service URL

After deployment completes, you'll see output including:

```
MCP_WEATHER_SERVICE_URI: https://ca-mcp-weather-xxxxx.region.azurecontainerapps.io
```

## Manual Deployment Steps

If you prefer to deploy step by step:

### 1. Provision infrastructure

```bash
azd provision
```

### 2. Build and deploy the service

```bash
azd deploy
```

## View Logs

```bash
azd monitor --logs
```

Or view in Azure Portal:
1. Navigate to your Container App
2. Click on "Log stream" or "Logs" in the Monitoring section

## Update the Service

After making code changes:

```bash
azd deploy
```

## Clean Up Resources

To remove all Azure resources:

```bash
azd down
```

## Configuration

The deployment is configured through:
- `azure.yaml` - Service and infrastructure configuration
- `infra/main.bicep` - Infrastructure as Code (Bicep)
- `infra/main.parameters.json` - Deployment parameters

## Customization

### Adjust Container Resources

Edit [infra/main.bicep](infra/main.bicep):

```bicep
containerCpuCoreCount: '1.0'  // Increase CPU
containerMemory: '2Gi'        // Increase memory
containerMaxReplicas: 5       // Scale up to 5 instances
```

### Add Environment Variables

Edit [infra/main.bicep](infra/main.bicep) and add to the `mcpWeather` module:

```bicep
env: [
  {
    name: 'API_KEY'
    value: 'your-api-key'
  }
]
```

## Troubleshooting

### Check deployment status
```bash
azd show
```

### View service logs
```bash
azd monitor --logs
```

### Verify container is running
```bash
az containerapp revision list \
  --name <container-app-name> \
  --resource-group <resource-group-name> \
  --output table
```

## Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
