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

// Database resource
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosDbAccount
  name: 'citizen-services'
  properties: {
    resource: {
      id: 'citizen-services'
    }
  }
}

// Users container
resource usersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'users'
  properties: {
    resource: {
      id: 'users'
      partitionKey: {
        paths: [
          '/id'
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/email/?'
          }
          {
            path: '/createdAt/?'
          }
        ]
        excludedPaths: [
          {
            path: '/preferences/*'
          }
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

// Projects container
resource projectsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'projects'
  properties: {
    resource: {
      id: 'projects'
      partitionKey: {
        paths: [
          '/userId'
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/userId/?'
          }
          {
            path: '/status/?'
          }
          {
            path: '/createdAt/?'
          }
          {
            path: '/updatedAt/?'
          }
          {
            path: '/context/address/?'
          }
          {
            path: '/references/permits/*/?'
          }
        ]
        excludedPaths: [
          {
            path: '/*'
          }
        ]
        compositeIndexes: [
          [
            {
              path: '/userId'
              order: 'ascending'
            }
            {
              path: '/status'
              order: 'ascending'
            }
            {
              path: '/updatedAt'
              order: 'descending'
            }
          ]
        ]
      }
    }
  }
}

// Messages container
resource messagesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'messages'
  properties: {
    resource: {
      id: 'messages'
      partitionKey: {
        paths: [
          '/projectId'
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/projectId/?'
          }
          {
            path: '/timestamp/?'
          }
          {
            path: '/role/?'
          }
        ]
        excludedPaths: [
          {
            path: '/content/?'
          }
          {
            path: '/toolCalls/*'
          }
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

// Step completions container with TTL
resource stepCompletionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'step_completions'
  properties: {
    resource: {
      id: 'step_completions'
      partitionKey: {
        paths: [
          '/toolName'
        ]
        kind: 'Hash'
      }
      defaultTtl: 15552000  // 180 days in seconds
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/toolName/?'
          }
          {
            path: '/city/?'
          }
          {
            path: '/completedAt/?'
          }
          {
            path: '/durationDays/?'
          }
        ]
        excludedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

@description('The name of the database')
output databaseName string = database.name
