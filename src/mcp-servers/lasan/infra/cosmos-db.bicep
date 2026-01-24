metadata description = 'Creates the LASAN CosmosDB database and containers for pickup requests.'

@description('Name of the existing CosmosDB account')
param cosmosDbAccountName string

@description('The Azure region for the resources')
param location string = resourceGroup().location

@description('Tags to apply to the resources')
param tags object = {}

// Reference the existing CosmosDB account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' existing = {
  name: cosmosDbAccountName
}

// LASAN Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosDbAccount
  name: 'lasan'
  tags: tags
  properties: {
    resource: {
      id: 'lasan'
    }
  }
}

// Pickups container
resource pickupsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'pickups'
  properties: {
    resource: {
      id: 'pickups'
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
            path: '/pickupId/?'
          }
          {
            path: '/status/?'
          }
          {
            path: '/address/?'
          }
          {
            path: '/pickupType/?'
          }
          {
            path: '/scheduledDate/?'
          }
          {
            path: '/createdAt/?'
          }
        ]
        excludedPaths: [
          {
            path: '/items/*'
          }
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

@description('The resource ID of the database')
output databaseId string = database.id
