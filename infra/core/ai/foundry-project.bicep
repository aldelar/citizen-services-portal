metadata description = 'Creates an Azure AI Foundry Project with AI Gateway integration via API Management.'

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

@description('Foundry Hub resource ID')
param hubId string

@description('API Management resource ID for AI Gateway')
param apimId string = ''

@description('Managed identity resource ID')
param identityId string = ''

resource foundryProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: projectName
  location: location
  tags: tags
  kind: 'Project'
  identity: !empty(identityId) ? {
    type: 'SystemAssigned,UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  } : {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: !empty(friendlyName) ? friendlyName : projectName
    description: projectDescription
    hubResourceId: hubId
    publicNetworkAccess: 'Enabled'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}

// Note: AI Gateway configuration (linking APIM to Foundry Project) is typically done post-deployment
// via Azure Portal or separate API calls, as it's not directly supported in Bicep ARM templates yet.
// The apimId parameter is reserved for future use when this capability becomes available in ARM/Bicep.
// For now, configure AI Gateway manually:
// 1. Navigate to Foundry Project in Azure Portal
// 2. Go to Settings > AI Gateway
// 3. Select the API Management instance created by this deployment

@description('The resource ID of the Foundry Project')
output id string = foundryProject.id

@description('The name of the Foundry Project')
output name string = foundryProject.name

@description('The principal ID of the Foundry Project')
output principalId string = foundryProject.identity.principalId

@description('Manual configuration required: Link APIM as AI Gateway in Foundry Project settings')
output configurationNote string = 'Configure AI Gateway: Navigate to ${projectName} > Settings > AI Gateway > Select ${apimId}'
