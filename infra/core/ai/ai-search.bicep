metadata description = 'Creates an Azure AI Search service for vector and semantic search.'

@description('The Azure region for the search service')
param location string = resourceGroup().location

@description('Tags to apply to the search service')
param tags object = {}

@description('Name of the AI Search service')
param searchServiceName string

@description('SKU for the search service')
@allowed([
  'free'
  'basic'
  'standard'
  'standard2'
  'standard3'
  'storage_optimized_l1'
  'storage_optimized_l2'
])
param sku string = 'standard'

@description('Number of replicas')
@minValue(1)
@maxValue(12)
param replicaCount int = 1

@description('Number of partitions')
@allowed([
  1
  2
  3
  4
  6
  12
])
param partitionCount int = 1

@description('Managed identity resource ID for authentication')
param identityId string = ''

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  identity: !empty(identityId) ? {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  } : {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    networkRuleSet: {
      ipRules: []
    }
    encryptionWithCmk: {
      enforcement: 'Unspecified'
    }
    disableLocalAuth: false
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

@description('The resource ID of the AI Search service')
output id string = searchService.id

@description('The name of the AI Search service')
output name string = searchService.name

@description('The endpoint of the AI Search service')
output endpoint string = 'https://${searchService.name}.search.windows.net'

@description('The principal ID of the search service (if using system-assigned identity)')
output principalId string = empty(identityId) ? searchService.identity.principalId : ''
