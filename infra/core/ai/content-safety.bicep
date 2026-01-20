metadata description = 'Creates an Azure AI Content Safety service for content moderation and PII detection.'

@description('The Azure region for the Content Safety service')
param location string = resourceGroup().location

@description('Tags to apply to the Content Safety service')
param tags object = {}

@description('Name of the Content Safety service')
param contentSafetyName string

@description('SKU for the Content Safety service')
@allowed([
  'F0'
  'S0'
])
param sku string = 'S0'

resource contentSafety 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: contentSafetyName
  location: location
  tags: tags
  kind: 'ContentSafety'
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: contentSafetyName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

@description('The resource ID of the Content Safety service')
output id string = contentSafety.id

@description('The name of the Content Safety service')
output name string = contentSafety.name

@description('The endpoint of the Content Safety service')
output endpoint string = contentSafety.properties.endpoint

@description('The principal ID of the Content Safety service')
output principalId string = contentSafety.identity.principalId
