metadata description = 'Creates an Azure API Management instance for AI Gateway pattern.'

@description('The Azure region for the API Management instance')
param location string = resourceGroup().location

@description('Tags to apply to the API Management instance')
param tags object = {}

@description('Name of the API Management instance')
param apimName string

@description('Publisher email for the API Management instance')
param publisherEmail string = 'admin@contoso.com'

@description('Publisher name for the API Management instance')
param publisherName string = 'Contoso'

@description('SKU for the API Management instance')
@allowed([
  'Consumption'
  'Developer'
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Standard'

@description('SKU capacity (not applicable for Consumption tier)')
@minValue(1)
param skuCapacity int = 1

resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: apimName
  location: location
  tags: tags
  sku: {
    name: sku
    capacity: sku == 'Consumption' ? 0 : skuCapacity
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
    publicNetworkAccess: 'Enabled'
    virtualNetworkType: 'None'
  }
}

@description('The resource ID of the API Management instance')
output id string = apim.id

@description('The name of the API Management instance')
output name string = apim.name

@description('The gateway URL of the API Management instance')
output gatewayUrl string = apim.properties.gatewayUrl

@description('The principal ID of the API Management instance')
output principalId string = apim.identity.principalId
