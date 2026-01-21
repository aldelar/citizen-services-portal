metadata description = 'Creates an Azure AI Foundry workspace for centralized AI development.'
metadata displayName = 'AI Foundry'

@description('The Azure region for the Foundry workspace')
param location string = resourceGroup().location

@description('Tags to apply to the Foundry workspace')
param tags object = {}

@description('Name of the AI Foundry workspace')
param foundryName string

@description('Friendly name for the Foundry workspace')
param friendlyName string = ''

@description('Description of the Foundry workspace')
param foundryDescription string = 'AI Foundry for Citizen Services Portal'

@description('Storage account resource ID')
param storageAccountId string

@description('Key Vault resource ID')
param keyVaultId string

@description('Application Insights resource ID')
param applicationInsightsId string

@description('Container Registry resource ID')
param containerRegistryId string

@description('Managed identity resource ID')
param identityId string = ''

resource foundry 'Microsoft.MachineLearningServices/workspaces@2024-10-01-preview' = {
  name: foundryName
  location: location
  tags: tags
  identity: !empty(identityId) ? {
    type: 'SystemAssigned,UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  } : {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: !empty(friendlyName) ? friendlyName : foundryName
    description: foundryDescription
    storageAccount: storageAccountId
    keyVault: keyVaultId
    applicationInsights: applicationInsightsId
    containerRegistry: containerRegistryId
    publicNetworkAccess: 'Enabled'
    v1LegacyMode: false
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}

@description('The resource ID of the Foundry workspace')
output id string = foundry.id

@description('The name of the Foundry workspace')
output name string = foundry.name

@description('The principal ID of the Foundry workspace')
output principalId string = foundry.identity.principalId
