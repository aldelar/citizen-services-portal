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

// Load abbreviations for resource naming
var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = {
  'azd-env-name': environmentName
  project: 'citizen-services-portal'
  'managed-by': 'azd'
}

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'aldelar-ama'
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
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
  }
}

// Security - Managed Identity
module managedIdentity './core/security/managed-identity.bicep' = {
  name: 'managed-identity-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    identityName: '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
  }
}

// Security - Key Vault
module keyVault './core/security/key-vault.bicep' = {
  name: 'key-vault-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    keyVaultName: '${abbrs.keyVaultVaults}${resourceToken}'
    principalId: principalId
  }
}

// Storage Account (required for Foundry Hub)
module storageAccount './core/data/storage-account.bicep' = {
  name: 'storage-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    storageAccountName: '${abbrs.storageStorageAccounts}${resourceToken}'
  }
}

// Container Registry
module containerRegistry './core/host/container-registry.bicep' = {
  name: 'container-registry-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    name: '${abbrs.containerRegistryRegistries}${resourceToken}'
  }
}

// Container Apps Environment
module containerAppsEnvironment './core/host/container-apps-environment.bicep' = {
  name: 'container-apps-env-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
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
    searchServiceName: '${abbrs.searchSearchServices}${resourceToken}'
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
    contentSafetyName: '${abbrs.cognitiveServicesAccounts}cs-${resourceToken}'
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
    cosmosDbAccountName: '${abbrs.cosmosDBDatabaseAccounts}${resourceToken}'
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
    apimName: '${abbrs.apiManagementService}${resourceToken}'
    publisherEmail: 'admin@citizenservices.local'
    publisherName: 'Citizen Services Platform'
    sku: 'Standard'
    skuCapacity: 1
  }
}

// AI Foundry Hub
module foundryHub './core/ai/foundry-hub.bicep' = {
  name: 'foundry-hub-deployment'
  scope: rg
  params: {
    location: location
    tags: tags
    hubName: '${abbrs.machineLearningServicesWorkspaces}hub-${resourceToken}'
    friendlyName: 'Citizen Services AI Hub'
    hubDescription: 'AI Foundry Hub for developing citizen service agents and workflows'
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
    projectName: '${abbrs.machineLearningServicesWorkspaces}proj-${resourceToken}'
    friendlyName: 'Citizen Services Project'
    projectDescription: 'Foundry project for building and deploying citizen service AI agents'
    hubId: foundryHub.outputs.id
    apimId: apiManagement.outputs.id
    identityId: managedIdentity.outputs.identityId
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
