metadata description = 'Creates an Azure AI Services account for Content Understanding.'

@description('The Azure region for the resource')
param location string = resourceGroup().location

@description('Tags to apply to the resource')
param tags object = {}

@description('Name of the Content Understanding resource')
param name string

resource contentUnderstanding 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: name
  }
}

@description('The resource ID')
output id string = contentUnderstanding.id

@description('The resource name')
output name string = contentUnderstanding.name

@description('The endpoint URL')
output endpoint string = contentUnderstanding.properties.endpoint
