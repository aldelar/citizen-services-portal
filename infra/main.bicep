targetScope = 'subscription'

metadata name = 'Citizen Services Portal - Azure Infrastructure'
metadata description = 'Complete infrastructure deployment for AI-powered citizen services platform'

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g., dev, staging, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
@allowed([
  'northcentralus'
  'eastus'
  'eastus2'
  'westus2'
  'westus3'
])
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

// Tags for all resources
var tags = {
  'azd-env-name': environmentName
  project: 'citizen-services-portal'
  'managed-by': 'azd'
}

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'csp'
  location: location
  tags: tags
}

// Monitoring - deployed first as other services depend on it
module monitoring './core/monitor/monitoring.bicep' = {
  name: 'monitoring-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    logAnalyticsName: 'aldelar-csp-log'
    applicationInsightsName: 'aldelar-csp-insights'
  }
}

// Security - Managed Identity
module managedIdentity './core/security/managed-identity.bicep' = {
  name: 'managed-identity-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    identityName: 'aldelar-csp-identity'
  }
}

// Security - Key Vault
module keyVault './core/security/key-vault.bicep' = {
  name: 'key-vault-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    keyVaultName: 'aldelar-csp-kv'
    principalId: principalId
  }
}

// Storage Account (required for Foundry Hub)
// Note: Storage account names must be globally unique, lowercase, no hyphens
module storageAccount './core/data/storage-account.bicep' = {
  name: 'storage-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    storageAccountName: 'aldelarcspstorage'
  }
}

// Container Registry
module containerRegistry './core/host/container-registry.bicep' = {
  name: 'container-registry-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    name: 'aldelarcspcr'
  }
}

// Container Apps Environment
module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
  name: 'container-apps-env-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    name: 'aldelar-csp-cae'
    logAnalyticsWorkspaceName: monitoring.outputs.logAnalyticsWorkspaceName
  }
}

// Azure AI Search
module aiSearch './core/ai/ai-search.bicep' = {
  name: 'ai-search-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    searchServiceName: 'aldelar-csp-search'
    sku: 'standard'
    replicaCount: 1
    partitionCount: 1
  }
}

// Azure Content Safety
module contentSafety './core/ai/content-safety.bicep' = {
  name: 'content-safety-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    contentSafetyName: 'aldelar-csp-contentsafety'
    sku: 'S0'
  }
}

// Azure Cosmos DB
module cosmosDb './core/data/cosmos-db.bicep' = {
  name: 'cosmos-db-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    cosmosDbAccountName: 'aldelar-csp-cosmos'
    enableServerless: true
    defaultConsistencyLevel: 'Session'
  }
}

// API Management
module apiManagement './core/gateway/api-management.bicep' = {
  name: 'apim-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    apimName: 'aldelar-csp-apim'
    publisherEmail: 'admin@citizenservices.local'
    publisherName: 'Citizen Services Platform'
    sku: 'Standard'
    skuCapacity: 1
  }
}

// AI Foundry Hub
module foundryHub './core/ai/foundry.bicep' = {
  name: 'foundry-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    hubName: 'aldelar-csp-foundry'
    friendlyName: 'Citizen Services AI Foundry'
    hubDescription: 'AI Foundry for developing citizen service agents and workflows'
    storageAccountId: storageAccount.outputs.id
    keyVaultId: keyVault.outputs.keyVaultId
    applicationInsightsId: monitoring.outputs.applicationInsightsId
    containerRegistryId: containerRegistry.outputs.id
    identityId: managedIdentity.outputs.identityId
  }
}

// AI Foundry Project
module foundryProject './core/ai/foundry-project.bicep' = {
  name: 'foundry-project-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    projectName: 'citizen-services-portal'
    friendlyName: 'Citizen Services Portal'
    projectDescription: 'Foundry project for building and deploying citizen service AI agents'
    hubId: foundryHub.outputs.id
    apimId: apiManagement.outputs.id
    identityId: managedIdentity.outputs.identityId
  }
}

// OpenAI Model Deployments
module gpt5Mini './core/ai/openai-deployment.bicep' = {
  name: 'gpt5-mini-deployment'
  scope: rg
  params: {
    hubName: foundryHub.outputs.name
    deploymentName: 'gpt-5-mini'
    modelName: 'gpt-5-mini'
    modelVersion: 'latest'
    sku: 'GlobalStandard'
    capacity: 1000000
  }
}

module gpt52 './core/ai/openai-deployment.bicep' = {
  name: 'gpt52-deployment'
  scope: rg
  params: {
    hubName: foundryHub.outputs.name
    deploymentName: 'gpt-5.2'
    modelName: 'gpt-5.2'
    modelVersion: 'latest'
    sku: 'GlobalStandard'
    capacity: 1000000
  }
}

module textEmbedding3Small './core/ai/openai-deployment.bicep' = {
  name: 'text-embedding-3-small-deployment'
  scope: rg
  params: {
    hubName: foundryHub.outputs.name
    deploymentName: 'text-embedding-3-small'
    modelName: 'text-embedding-3-small'
    modelVersion: 'latest'
    sku: 'GlobalStandard'
    capacity: 1000000
  }
}

// =================================
// API Management - API Configuration
// =================================

// AI Models API (for accessing OpenAI models through APIM)
module apimAiApi './core/gateway/apim-ai-api.bicep' = {
  name: 'apim-ai-api-deployment'
  scope: rg
  params: {
    apimName: apiManagement.outputs.name
    displayName: 'AI Models API'
    apiDescription: 'API for accessing OpenAI models (gpt-5-mini, gpt-5.2, text-embedding-3-small)'
    foundryEndpoint: foundryHub.outputs.name // Will be configured post-deployment
  }
  dependsOn: [
    gpt5Mini
    gpt52
    textEmbedding3Small
  ]
}

// MCP Services API (for accessing MCP servers through APIM)
module apimMcpApi './core/gateway/apim-mcp-api.bicep' = {
  name: 'apim-mcp-api-deployment'
  scope: rg
  params: {
    apimName: apiManagement.outputs.name
    displayName: 'MCP Services API'
    apiDescription: 'API for accessing MCP servers providing government service tools'
    ladbsMcpUri: mcpLadbs.outputs.uri
  }
}

// =================================
// Application Services
// =================================

// LADBS MCP Server
module mcpLadbs './app/mcp-ladbs.bicep' = {
  name: 'mcp-ladbs-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppName: 'aldelar-csp-mcp-ladbs'
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    containerImage: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - azd will update
    identityId: managedIdentity.outputs.identityId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
  }
}

// =================================
// Outputs
// =================================

@description('The name of the resource group')
output resourceGroupName string = rg.name

@description('The location of deployed resources')
output location string = location

@description('The environment name')
output environmentName string = environmentName

// Monitoring
@description('Application Insights connection string')
output applicationInsightsConnectionString string = monitoring.outputs.applicationInsightsConnectionString

@description('Log Analytics workspace name')
output logAnalyticsWorkspaceName string = monitoring.outputs.logAnalyticsWorkspaceName

// Security
@description('Key Vault name')
output keyVaultName string = keyVault.outputs.keyVaultName

@description('Key Vault URI')
output keyVaultUri string = keyVault.outputs.keyVaultUri

@description('Managed Identity principal ID')
output managedIdentityPrincipalId string = managedIdentity.outputs.principalId

// Storage
@description('Storage account name')
output storageAccountName string = storageAccount.outputs.name

// Container Apps
@description('Container Registry name')
output containerRegistryName string = containerRegistry.outputs.name

@description('Container Registry login server')
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer

@description('Container Apps Environment name')
output containerAppsEnvironmentName string = containerAppsEnvironment.outputs.name

// AI Services
@description('AI Search service name')
output aiSearchName string = aiSearch.outputs.name

@description('AI Search endpoint')
output aiSearchEndpoint string = aiSearch.outputs.endpoint

@description('Content Safety service name')
output contentSafetyName string = contentSafety.outputs.name

@description('Content Safety endpoint')
output contentSafetyEndpoint string = contentSafety.outputs.endpoint

// Data
@description('Cosmos DB account name')
output cosmosDbAccountName string = cosmosDb.outputs.name

@description('Cosmos DB endpoint')
output cosmosDbEndpoint string = cosmosDb.outputs.endpoint

// API Management
@description('API Management name')
output apiManagementName string = apiManagement.outputs.name

@description('API Management gateway URL')
output apiManagementGatewayUrl string = apiManagement.outputs.gatewayUrl

// AI Foundry
@description('Foundry Hub name')
output foundryHubName string = foundryHub.outputs.name

@description('Foundry Project name')
output foundryProjectName string = foundryProject.outputs.name

@description('Post-deployment configuration note for AI Gateway')
output aiGatewayConfigurationNote string = foundryProject.outputs.configurationNote

// Application Services
@description('LADBS MCP Server FQDN')
output mcpLadbsFqdn string = mcpLadbs.outputs.fqdn

@description('LADBS MCP Server URI')
output mcpLadbsUri string = mcpLadbs.outputs.uri
