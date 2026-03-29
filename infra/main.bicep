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
  'southcentralus'
  'eastus'
  'eastus2'
  'westus2'
  'westus3'
])
param location string

@description('Id of the user or app to assign application roles')
param principalId string = ''

@description('Developer IP address for Cosmos DB firewall (for local development)')
param developerIpAddress string = ''

// Tags for all resources
var tags = {
  'azd-env-name': environmentName
  project: 'aldelar-csp-foundry-project'
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

// Storage Account (required for Foundry)
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
    developerIpAddress: developerIpAddress
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

// AI Gateway (BasicV2 APIM) - Required by Foundry for agent registration & governance
// Foundry AI Gateway requires a v2 tier APIM (BasicV2/StandardV2/PremiumV2).
// The existing Standard (classic) APIM does not qualify.
// Linking to Foundry is handled by the foundryAiGatewayLink module below.
module aiGateway './core/gateway/ai-gateway.bicep' = {
  name: 'ai-gateway-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    gatewayName: 'aldelar-csp-ai-gateway'
    publisherEmail: 'admin@citizenservices.local'
    publisherName: 'Citizen Services AI Gateway'
    sku: 'BasicV2'
  }
}

// AI Foundry
module foundry './core/ai/foundry.bicep' = {
  name: 'ai-foundry'
  scope: rg
  params: {
    location: location
    tags: tags
    foundryName: 'aldelar-csp-foundry'
    friendlyName: 'Citizen Services AI Foundry'
    foundryDescription: 'AI Foundry for developing citizen service agents and workflows'
  }
}

// Foundry RBAC - Grant user access to Foundry data plane operations
module foundryRbac './core/security/foundry-rbac.bicep' = if (principalId != '') {
  name: 'foundry-rbac-deployment'
  scope: rg
  params: {
    foundryId: foundry.outputs.id
    principalId: principalId
    principalType: 'User'
  }
}

// Foundry RBAC - Grant managed identity access to Foundry for Azure OpenAI calls
module foundryIdentityRbac './core/security/foundry-rbac.bicep' = {
  name: 'foundry-identity-rbac-deployment'
  scope: rg
  params: {
    foundryId: foundry.outputs.id
    principalId: managedIdentity.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// Foundry RBAC - Grant AI Search service access to Foundry (for AI enrichment)
module foundrySearchRbac './core/security/foundry-rbac.bicep' = {
  name: 'foundry-search-rbac-deployment'
  scope: rg
  params: {
    foundryId: foundry.outputs.id
    principalId: aiSearch.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// =================================
// South Central US AI Foundry (for GPT-5.2)
// =================================

// AI Foundry - South Central US region for GPT-5.2 deployment
module foundrySouthCentralUs './core/ai/foundry.bicep' = {
  name: 'ai-foundry-southcentralus'
  scope: rg
  params: {
    location: 'southcentralus'
    tags: tags
    foundryName: 'aldelar-csp-foundry-southcentralus'
    friendlyName: 'Citizen Services AI Foundry - South Central US'
    foundryDescription: 'AI Foundry in South Central US for GPT-5.2 model deployment'
  }
}

// GPT-5.2 Model Deployment in South Central US Foundry
module gpt52 './core/ai/openai-deployment.bicep' = {
  name: 'gpt52-deployment'
  scope: rg
  params: {
    foundryName: foundrySouthCentralUs.outputs.name
    deploymentName: 'gpt-5.2'
    modelName: 'gpt-5.2'
    modelVersion: '2025-04-14'
    sku: 'GlobalStandard'
    capacity: 1000
  }
}

// Foundry RBAC - Grant user access to South Central US Foundry
module foundrySouthCentralUsRbac './core/security/foundry-rbac.bicep' = if (principalId != '') {
  name: 'foundry-southcentralus-rbac-deployment'
  scope: rg
  params: {
    foundryId: foundrySouthCentralUs.outputs.id
    principalId: principalId
    principalType: 'User'
  }
}

// Foundry RBAC - Grant managed identity access to South Central US Foundry for cross-region Azure OpenAI calls
module foundrySouthCentralUsIdentityRbac './core/security/foundry-rbac.bicep' = {
  name: 'foundry-southcentralus-identity-rbac-deployment'
  scope: rg
  params: {
    foundryId: foundrySouthCentralUs.outputs.id
    principalId: managedIdentity.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// Storage RBAC - Grant access to blob storage for user, search, and managed identity
module storageRbac './core/security/storage-rbac.bicep' = {
  name: 'storage-rbac-deployment'
  scope: rg
  params: {
    storageAccountName: storageAccount.outputs.name
    userPrincipalId: principalId
    searchPrincipalId: aiSearch.outputs.principalId
    identityPrincipalId: managedIdentity.outputs.principalId
  }
}

// AI Search RBAC - Grant access to search indexes for user and managed identity
module searchRbac './core/security/search-rbac.bicep' = {
  name: 'search-rbac-deployment'
  scope: rg
  params: {
    searchServiceName: aiSearch.outputs.name
    userPrincipalId: principalId
    identityPrincipalId: managedIdentity.outputs.principalId
  }
}

// Cosmos DB RBAC - Grant data plane access to user and managed identity
module cosmosRbac './core/security/cosmos-rbac.bicep' = {
  name: 'cosmos-rbac-deployment'
  scope: rg
  params: {
    cosmosDbAccountName: cosmosDb.outputs.name
    userPrincipalId: principalId
    identityPrincipalId: managedIdentity.outputs.principalId
  }
}

// AI Foundry Project
module foundryProject './core/ai/foundry-project.bicep' = {
  name: 'foundry-project-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    projectName: 'aldelar-csp-foundry-project'
    friendlyName: 'Citizen Services AI Foundry Project'
    projectDescription: 'Foundry project for building and deploying citizen service AI agents'
    foundryName: foundry.outputs.name
  }
}

// AI Gateway ↔ Foundry linking is handled by the postprovision hook
// (infra/hooks/postprovision.sh) using `az rest` with the logged-in identity.
// deploymentScripts was removed because it requires storage key access.

// AI Gateway RBAC – grant the AI Gateway APIM's managed identity access to Foundry
module aiGatewayFoundryRbac './core/security/foundry-rbac.bicep' = {
  name: 'ai-gateway-foundry-rbac-deployment'
  scope: rg
  params: {
    foundryId: foundry.outputs.id
    principalId: aiGateway.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

// ACR Connection for Hosted Agents
// Required for capability host to pull agent container images
module acrConnection './core/ai/acr-connection.bicep' = {
  name: 'acr-connection-deployment'
  scope: rg
  params: {
    foundryName: foundry.outputs.name
    projectName: foundryProject.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    connectionName: 'acr-connection'
  }
}

// OpenAI Model Deployments
module gpt41Mini './core/ai/openai-deployment.bicep' = {
  name: 'gpt41-mini-deployment'
  scope: rg
  params: {
    foundryName: foundry.outputs.name
    deploymentName: 'gpt-4.1-mini'
    modelName: 'gpt-4.1-mini'
    modelVersion: '2025-04-14'
    sku: 'GlobalStandard'
    capacity: 5000
  }
}

module gpt41 './core/ai/openai-deployment.bicep' = {
  name: 'gpt41-deployment'
  scope: rg
  params: {
    foundryName: foundry.outputs.name
    deploymentName: 'gpt-4.1'
    modelName: 'gpt-4.1'
    modelVersion: '2025-04-14'
    sku: 'GlobalStandard'
    capacity: 1000
  }
  dependsOn: [
    gpt41Mini
  ]
}

module textEmbedding3Small './core/ai/openai-deployment.bicep' = {
  name: 'text-embedding-3-small-deployment'
  scope: rg
  params: {
    foundryName: foundry.outputs.name
    deploymentName: 'text-embedding-3-small'
    modelName: 'text-embedding-3-small'
    modelVersion: '1'
    sku: 'GlobalStandard'
    capacity: 1000
  }
  dependsOn: [
    gpt41
  ]
}

// Content Understanding for document processing
// NOTE: Content Understanding API is only available in specific regions (westus, swedencentral, australiaeast for preview)
// We deploy to westus regardless of the main location to ensure API availability
module contentUnderstanding './core/ai/content-understanding.bicep' = {
  name: 'content-understanding-deployment'
  scope: rg
  params: {
    location: 'westus'  // Content Understanding requires specific regions - see language-region-support docs
    tags: tags
    name: 'aldelar-csp-cu-westus'  // New name to avoid conflict with existing northcentralus resource
  }
}

// Content Understanding Model Deployments - Required for ContentUnderstandingSkill
// Content Understanding requires GPT-4.1, GPT-4.1-mini, and text-embedding-3-large
module cuGpt41Mini './core/ai/openai-deployment.bicep' = {
  name: 'cu-gpt41-mini-deployment'
  scope: rg
  params: {
    foundryName: contentUnderstanding.outputs.name
    deploymentName: 'gpt-4.1-mini'
    modelName: 'gpt-4.1-mini'
    modelVersion: '2025-04-14'
    sku: 'GlobalStandard'
    capacity: 1000
  }
}

module cuGpt41 './core/ai/openai-deployment.bicep' = {
  name: 'cu-gpt41-deployment'
  scope: rg
  params: {
    foundryName: contentUnderstanding.outputs.name
    deploymentName: 'gpt-4.1'
    modelName: 'gpt-4.1'
    modelVersion: '2025-04-14'
    sku: 'GlobalStandard'
    capacity: 1000
  }
  dependsOn: [
    cuGpt41Mini
  ]
}

module cuTextEmbedding3Large './core/ai/openai-deployment.bicep' = {
  name: 'cu-text-embedding-3-large-deployment'
  scope: rg
  params: {
    foundryName: contentUnderstanding.outputs.name
    deploymentName: 'text-embedding-3-large'
    modelName: 'text-embedding-3-large'
    modelVersion: '1'
    sku: 'GlobalStandard'
    capacity: 1000
  }
  dependsOn: [
    cuGpt41
  ]
}

// Content Understanding RBAC - Grant access to CU for user, search, and managed identity
module contentUnderstandingRbac './core/security/content-understanding-rbac.bicep' = {
  name: 'content-understanding-rbac-deployment'
  scope: rg
  params: {
    contentUnderstandingId: contentUnderstanding.outputs.id
    userPrincipalId: principalId
    searchPrincipalId: aiSearch.outputs.principalId
    identityPrincipalId: managedIdentity.outputs.principalId
  }
}

// Knowledge Base Storage Containers
module kbContainers './app/knowledge-base/kb-storage-containers.bicep' = {
  name: 'kb-containers-deployment'
  scope: rg
  params: {
    storageAccountName: storageAccount.outputs.name
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
    apiDescription: 'API for accessing OpenAI models (gpt-4.1-mini, gpt-4.1, text-embedding-3-small)'
    foundryEndpoint: foundry.outputs.endpoint
  }
  dependsOn: [
    gpt41Mini
    gpt41
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
    identityClientId: managedIdentity.outputs.clientId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    cosmosDbAccountName: cosmosDb.outputs.name
    cosmosEndpoint: cosmosDb.outputs.endpoint
    enableAuthentication: false  // Disabled - see technical-specs/mcp-authentication.md for details
    appClientId: ''
  }
}

// Grant Foundry Project identity access to MCP server
// This enables agents to authenticate and call MCP tools using their identity
module mcpLadbsRbac './core/security/mcp-server-rbac.bicep' = {
  name: 'mcp-ladbs-rbac-deployment'
  scope: rg
  params: {
    containerAppId: mcpLadbs.outputs.id
    principalIds: [
      foundryProject.outputs.principalId  // Foundry Project managed identity for development/testing
    ]
    principalType: 'ServicePrincipal'
  }
}

// LADWP MCP Server
module mcpLadwp './app/mcp-ladwp.bicep' = {
  name: 'mcp-ladwp-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppName: 'aldelar-csp-mcp-ladwp'
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    containerImage: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - azd will update
    identityId: managedIdentity.outputs.identityId
    identityClientId: managedIdentity.outputs.clientId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    cosmosDbAccountName: cosmosDb.outputs.name
    cosmosEndpoint: cosmosDb.outputs.endpoint
    searchEndpoint: aiSearch.outputs.endpoint
    enableAuthentication: false  // Disabled - see technical-specs/mcp-authentication.md for details
    appClientId: ''
  }
}

// Grant Foundry Project identity access to LADWP MCP server
module mcpLadwpRbac './core/security/mcp-server-rbac.bicep' = {
  name: 'mcp-ladwp-rbac-deployment'
  scope: rg
  params: {
    containerAppId: mcpLadwp.outputs.id
    principalIds: [
      foundryProject.outputs.principalId
    ]
    principalType: 'ServicePrincipal'
  }
}

// LASAN MCP Server
module mcpLasan './app/mcp-lasan.bicep' = {
  name: 'mcp-lasan-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppName: 'aldelar-csp-mcp-lasan'
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    containerImage: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - azd will update
    identityId: managedIdentity.outputs.identityId
    identityClientId: managedIdentity.outputs.clientId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    cosmosDbAccountName: cosmosDb.outputs.name
    cosmosEndpoint: cosmosDb.outputs.endpoint
    searchEndpoint: aiSearch.outputs.endpoint
    enableAuthentication: false  // Disabled - see technical-specs/mcp-authentication.md for details
    appClientId: ''
  }
}

// Grant Foundry Project identity access to LASAN MCP server
module mcpLasanRbac './core/security/mcp-server-rbac.bicep' = {
  name: 'mcp-lasan-rbac-deployment'
  scope: rg
  params: {
    containerAppId: mcpLasan.outputs.id
    principalIds: [
      foundryProject.outputs.principalId
    ]
    principalType: 'ServicePrincipal'
  }
}

// CSP MCP Server (Plan Lifecycle & Analytics)
module mcpCsp './app/mcp-csp.bicep' = {
  name: 'mcp-csp-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppName: 'aldelar-csp-mcp-csp'
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    containerImage: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - azd will update
    identityId: managedIdentity.outputs.identityId
    identityClientId: managedIdentity.outputs.clientId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    cosmosEndpoint: cosmosDb.outputs.endpoint
    enableAuthentication: false  // Disabled - see technical-specs/mcp-authentication.md for details
    appClientId: ''
  }
}

// Grant Foundry Project identity access to CSP MCP server
module mcpCspRbac './core/security/mcp-server-rbac.bicep' = {
  name: 'mcp-csp-rbac-deployment'
  scope: rg
  params: {
    containerAppId: mcpCsp.outputs.id
    principalIds: [
      foundryProject.outputs.principalId
    ]
    principalType: 'ServicePrincipal'
  }
}

// CSP Agent (Azure Container App)
module cspAgent './app/csp-agent.bicep' = {
  name: 'csp-agent-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppName: 'aldelar-csp-agent'
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    containerImage: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - azd will update
    identityId: managedIdentity.outputs.identityId
    identityClientId: managedIdentity.outputs.clientId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    azureOpenAiEndpoint: 'https://${foundrySouthCentralUs.outputs.name}.openai.azure.com/'
    azureOpenAiChatDeploymentName: 'gpt-5.2'
    mcpLadbsUrl: mcpLadbs.outputs.uri
    mcpLadwpUrl: mcpLadwp.outputs.uri
    mcpLasanUrl: mcpLasan.outputs.uri
    mcpCspUrl: mcpCsp.outputs.uri
    agentProjectResourceId: foundryProject.outputs.id
    agentProjectEndpoint: 'https://${foundry.outputs.name}.services.ai.azure.com/api/projects/${foundryProject.outputs.name}'
    external: true
  }
  dependsOn: [
    gpt52  // Ensure GPT-5.2 is deployed before agent configuration
  ]
}

// Web App (Azure Container App)
module webApp './app/webapp.bicep' = {
  name: 'webapp-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    containerAppName: 'aldelar-csp-webapp'
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    containerImage: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder - azd will update
    identityId: managedIdentity.outputs.identityId
    identityClientId: managedIdentity.outputs.clientId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    cosmosEndpoint: cosmosDb.outputs.endpoint
    cosmosDatabase: 'csp'
    cspAgentUrl: cspAgent.outputs.uri
    mcpLadbsUrl: mcpLadbs.outputs.uri
    mcpLadwpUrl: mcpLadwp.outputs.uri
    mcpLasanUrl: mcpLasan.outputs.uri
    mcpCspUrl: mcpCsp.outputs.uri
    enableAuthentication: false
    appClientId: ''
    appClientSecret: ''
    external: true
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

@description('CSP Agent Container App URL')
output cspAgentUrl string = cspAgent.outputs.uri

@description('Web App Container App URL')
output webAppUrl string = webApp.outputs.uri

// AI Services
@description('AI Search service name')
output aiSearchName string = aiSearch.outputs.name

@description('AI Search endpoint')
output aiSearchEndpoint string = aiSearch.outputs.endpoint

@description('Content Safety service name')
output contentSafetyName string = contentSafety.outputs.name

@description('Content Safety endpoint')
output contentSafetyEndpoint string = contentSafety.outputs.endpoint

@description('Content Understanding service name')
output contentUnderstandingName string = contentUnderstanding.outputs.name

@description('Content Understanding endpoint')
output contentUnderstandingEndpoint string = contentUnderstanding.outputs.endpoint

// Data
@description('Cosmos DB account name')
output cosmosDbAccountName string = cosmosDb.outputs.name

@description('Cosmos DB endpoint')
output cosmosDbEndpoint string = cosmosDb.outputs.endpoint

// API Management
@description('API Management name')
output apiManagementName string = apiManagement.outputs.name

@description('API Management resource ID')
output apiManagementId string = apiManagement.outputs.id

@description('API Management gateway URL')
output apiManagementGatewayUrl string = apiManagement.outputs.gatewayUrl

// AI Gateway (v2 APIM for Foundry)
@description('AI Gateway (v2 APIM) name')
output aiGatewayName string = aiGateway.outputs.name

@description('AI Gateway (v2 APIM) resource ID')
output aiGatewayId string = aiGateway.outputs.id

@description('AI Gateway URL')
output aiGatewayUrl string = aiGateway.outputs.gatewayUrl

// AI Foundry
@description('Foundry account ARM resource ID')
output foundryId string = foundry.outputs.id

@description('Foundry project ARM resource ID')
output foundryProjectId string = foundryProject.outputs.id

@description('Foundry name')
output foundryName string = foundry.outputs.name

@description('Foundry Hub endpoint')
output foundryEndpoint string = foundry.outputs.endpoint

@description('Foundry Project name')
output foundryProjectName string = foundryProject.outputs.name

@description('Foundry Project endpoint - Use this for agent deployment')
output foundryProjectEndpoint string = 'https://${foundry.outputs.name}.services.ai.azure.com/api/projects/${foundryProject.outputs.name}'

// AI Foundry - South Central US (for GPT-5.2)
@description('Foundry name - South Central US')
output foundrySouthCentralUsName string = foundrySouthCentralUs.outputs.name

@description('Foundry endpoint - South Central US (for GPT-5.2)')
output foundrySouthCentralUsEndpoint string = foundrySouthCentralUs.outputs.endpoint

@description('Azure OpenAI endpoint for GPT-5.2 - South Central US')
output azureOpenAiEndpointGpt52 string = 'https://${foundrySouthCentralUs.outputs.name}.openai.azure.com/'

@description('Cosmos DB endpoint for agent thread persistence')
output COSMOS_ENDPOINT string = cosmosDb.outputs.endpoint

// Application Services
@description('LADBS MCP Server FQDN')
output mcpLadbsFqdn string = mcpLadbs.outputs.fqdn

@description('LADBS MCP Server URI')
output mcpLadbsUri string = mcpLadbs.outputs.uri

@description('LADBS MCP Server Scope URI for Microsoft Entra authentication')
output mcpLadbsScopeUri string = 'https://${mcpLadbs.outputs.fqdn}'

@description('LADWP MCP Server FQDN')
output mcpLadwpFqdn string = mcpLadwp.outputs.fqdn

@description('LADWP MCP Server URI')
output mcpLadwpUri string = mcpLadwp.outputs.uri

@description('LADWP MCP Server Scope URI for Microsoft Entra authentication')
output mcpLadwpScopeUri string = 'https://${mcpLadwp.outputs.fqdn}'

@description('LASAN MCP Server FQDN')
output mcpLasanFqdn string = mcpLasan.outputs.fqdn

@description('LASAN MCP Server URI')
output mcpLasanUri string = mcpLasan.outputs.uri

@description('LASAN MCP Server Scope URI for Microsoft Entra authentication')
output mcpLasanScopeUri string = 'https://${mcpLasan.outputs.fqdn}'

@description('CSP MCP Server FQDN')
output mcpCspFqdn string = mcpCsp.outputs.fqdn

@description('CSP MCP Server URI')
output mcpCspUri string = mcpCsp.outputs.uri

@description('CSP MCP Server Scope URI for Microsoft Entra authentication')
output mcpCspScopeUri string = 'https://${mcpCsp.outputs.fqdn}'

// MCP Server URLs with /mcp path for agent configuration
@description('LADBS MCP Server URL for agent configuration')
output MCP_LADBS_URL string = '${mcpLadbs.outputs.uri}/mcp'

@description('LADWP MCP Server URL for agent configuration')
output MCP_LADWP_URL string = '${mcpLadwp.outputs.uri}/mcp'

@description('LASAN MCP Server URL for agent configuration')
output MCP_LASAN_URL string = '${mcpLasan.outputs.uri}/mcp'

@description('CSP MCP Server URL for agent configuration')
output MCP_CSP_URL string = '${mcpCsp.outputs.uri}/mcp'
