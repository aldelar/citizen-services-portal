metadata description = 'Creates an Azure AI Foundry Hub for centralized AI development.'

@description('The Azure region for the Foundry Hub')
param location string = resourceGroup().location

@description('Tags to apply to the Foundry Hub')
param tags object = {}

@description('Name of the Foundry Hub')
param hubName string

@description('Friendly name for the Foundry Hub')
param friendlyName string = ''

@description('Description of the Foundry Hub')
param hubDescription string = 'AI Foundry Hub for Citizen Services Portal'

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

resource foundryHub 'Microsoft.MachineLearningServices/workspaces@2024-10-01-preview' = {
  name: hubName
  location: location
  tags: tags
  kind: 'Foundry'
  identity: !empty(identityId) ? {
    type: 'SystemAssigned,UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  } : {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: !empty(friendlyName) ? friendlyName : hubName
    description: hubDescription
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

@description('The resource ID of the Foundry Hub')
output id string = foundryHub.id

@description('The name of the Foundry Hub')
output name string = foundryHub.name

@description('The principal ID of the Foundry Hub')
output principalId string = foundryHub.identity.principalId
