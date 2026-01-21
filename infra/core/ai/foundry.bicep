metadata description = 'Creates an Azure AI Foundry account (NEW Foundry) for centralized AI development.'
metadata displayName = 'AI Foundry'

@description('The Azure region for the Foundry account')
param location string = resourceGroup().location

@description('Tags to apply to the Foundry account')
param tags object = {}

@description('Name of the AI Foundry account')
param foundryName string

@description('Friendly name for the Foundry account')
param friendlyName string = ''

@description('Description of the Foundry account')
param foundryDescription string = 'AI Foundry for Citizen Services Portal'

// NEW Foundry uses Microsoft.CognitiveServices/accounts with kind='AIServices'
resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: foundryName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    allowProjectManagement: true  // Required for NEW Foundry
    customSubDomainName: foundryName
    disableLocalAuth: false  // Enable for development
    publicNetworkAccess: 'Enabled'
  }
}

@description('The resource ID of the Foundry account')
output id string = foundry.id

@description('The name of the Foundry account')
output name string = foundry.name

@description('The endpoint of the Foundry account')
output endpoint string = foundry.properties.endpoint

@description('The principal ID of the Foundry account')
output principalId string = foundry.identity.principalId
