metadata description = 'Creates an Azure Cosmos DB account with NoSQL API for agent memory and citizen data.'

@description('The Azure region for the Cosmos DB account')
param location string = resourceGroup().location

@description('Tags to apply to the Cosmos DB account')
param tags object = {}

@description('Name of the Cosmos DB account')
param cosmosDbAccountName string

@description('Enable serverless capacity mode')
param enableServerless bool = true

@description('Default consistency level')
@allowed([
  'Eventual'
  'ConsistentPrefix'
  'Session'
  'BoundedStaleness'
  'Strong'
])
param defaultConsistencyLevel string = 'Session'

@description('Enable automatic failover')
param enableAutomaticFailover bool = false

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' = {
  name: cosmosDbAccountName
  location: location
  tags: tags
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: defaultConsistencyLevel
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: enableServerless ? [
      {
        name: 'EnableServerless'
      }
    ] : []
    enableAutomaticFailover: enableAutomaticFailover
    enableMultipleWriteLocations: false
    publicNetworkAccess: 'Enabled'
    networkAclBypass: 'AzureServices'
    disableKeyBasedMetadataWriteAccess: false
    enableFreeTier: false
  }
}

@description('The resource ID of the Cosmos DB account')
output id string = cosmosDbAccount.id

@description('The name of the Cosmos DB account')
output name string = cosmosDbAccount.name

@description('The endpoint of the Cosmos DB account')
output endpoint string = cosmosDbAccount.properties.documentEndpoint

@description('The principal ID of the Cosmos DB account')
output principalId string = cosmosDbAccount.identity.principalId
