metadata description = 'Creates an Azure AI Foundry Project (NEW Foundry) for AI development.'

@description('The Azure region for the Foundry Project')
param location string = resourceGroup().location

@description('Tags to apply to the Foundry Project')
param tags object = {}

@description('Name of the Foundry Project')
param projectName string

@description('Friendly name for the Foundry Project')
param friendlyName string = ''

@description('Description of the Foundry Project')
param projectDescription string = 'AI Foundry Project for Citizen Services Portal agents'

@description('Foundry account name (parent)')
param foundryName string

// Reference the parent Foundry account
resource foundry 'Microsoft.CognitiveServices/accounts@2025-10-01-preview' existing = {
  name: foundryName
}

// NEW Foundry Project
resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-10-01-preview' = {
  name: projectName
  parent: foundry
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

@description('The resource ID of the Foundry Project')
output id string = foundryProject.id

@description('The name of the Foundry Project')
output name string = foundryProject.name

@description('The principal ID of the Foundry Project')
output principalId string = foundryProject.identity.principalId
