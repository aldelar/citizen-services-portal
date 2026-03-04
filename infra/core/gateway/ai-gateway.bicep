metadata description = 'Creates a BasicV2 Azure API Management instance for Foundry AI Gateway.'

@description('The Azure region for the API Management instance')
param location string = resourceGroup().location

@description('Tags to apply to the API Management instance')
param tags object = {}

@description('Name of the API Management instance used as AI Gateway')
param gatewayName string

@description('Publisher email for the API Management instance')
param publisherEmail string = 'admin@contoso.com'

@description('Publisher name for the API Management instance')
param publisherName string = 'AI Gateway'

@description('SKU for the API Management instance - must be a v2 tier for AI Gateway')
@allowed([
  'BasicV2'
  'StandardV2'
])
param sku string = 'BasicV2'

resource apimGateway 'Microsoft.ApiManagement/service@2024-06-01-preview' = {
  name: gatewayName
  location: location
  tags: tags
  sku: {
    name: sku
    capacity: 1
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
    publicNetworkAccess: 'Enabled'
  }
}

@description('The resource ID of the AI Gateway APIM instance')
output id string = apimGateway.id

@description('The name of the AI Gateway APIM instance')
output name string = apimGateway.name

@description('The gateway URL of the AI Gateway APIM instance')
output gatewayUrl string = apimGateway.properties.gatewayUrl

@description('The principal ID of the AI Gateway APIM managed identity')
output principalId string = apimGateway.identity.principalId
