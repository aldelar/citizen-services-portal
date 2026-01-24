metadata description = 'Creates the LADBS CosmosDB database and containers for permits and inspections.'

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

// LADBS Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosDbAccount
  name: 'ladbs'
  tags: tags
  properties: {
    resource: {
      id: 'ladbs'
    }
  }
}

// Permits container
resource permitsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'permits'
  properties: {
    resource: {
      id: 'permits'
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
            path: '/permitNumber/?'
          }
          {
            path: '/status/?'
          }
          {
            path: '/address/?'
          }
          {
            path: '/permitType/?'
          }
          {
            path: '/submittedAt/?'
          }
          {
            path: '/createdAt/?'
          }
        ]
        excludedPaths: [
          {
            path: '/applicant/*'
          }
          {
            path: '/documents/*'
          }
          {
            path: '/fees/*'
          }
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

// Inspections container
resource inspectionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'inspections'
  properties: {
    resource: {
      id: 'inspections'
      partitionKey: {
        paths: [
          '/permitNumber'
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/permitNumber/?'
          }
          {
            path: '/userId/?'
          }
          {
            path: '/inspectionId/?'
          }
          {
            path: '/status/?'
          }
          {
            path: '/address/?'
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
