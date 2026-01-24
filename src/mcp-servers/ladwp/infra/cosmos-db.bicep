metadata description = 'Creates the LADWP CosmosDB database and containers for interconnections, rebates, and TOU enrollments.'

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

// LADWP Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosDbAccount
  name: 'ladwp'
  tags: tags
  properties: {
    resource: {
      id: 'ladwp'
    }
  }
}

// Interconnections container
resource interconnectionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'interconnections'
  properties: {
    resource: {
      id: 'interconnections'
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
            path: '/applicationId/?'
          }
          {
            path: '/status/?'
          }
          {
            path: '/address/?'
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
            path: '/equipment/*'
          }
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

// Rebates container
resource rebatesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'rebates'
  properties: {
    resource: {
      id: 'rebates'
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
            path: '/applicationId/?'
          }
          {
            path: '/accountNumber/?'
          }
          {
            path: '/status/?'
          }
          {
            path: '/equipmentType/?'
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
            path: '/*'
          }
        ]
      }
    }
  }
}

// TOU Enrollments container
resource touEnrollmentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'tou_enrollments'
  properties: {
    resource: {
      id: 'tou_enrollments'
      partitionKey: {
        paths: [
          '/accountNumber'
        ]
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/accountNumber/?'
          }
          {
            path: '/userId/?'
          }
          {
            path: '/confirmationNumber/?'
          }
          {
            path: '/status/?'
          }
          {
            path: '/ratePlan/?'
          }
          {
            path: '/effectiveDate/?'
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
