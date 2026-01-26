metadata description = 'Creates the Reporting CosmosDB database and containers for step logs.'

@description('Name of the existing CosmosDB account')
param cosmosDbAccountName string

@description('Tags to apply to the resources')
param tags object = {}

// Reference the existing CosmosDB account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' existing = {
  name: cosmosDbAccountName
}

// Reporting Database
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-11-15' = {
  parent: cosmosDbAccount
  name: 'reporting'
  tags: tags
  properties: {
    resource: {
      id: 'reporting'
    }
  }
}

// Step logs container
resource stepLogsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-11-15' = {
  parent: database
  name: 'step_logs'
  properties: {
    resource: {
      id: 'step_logs'
      partitionKey: {
        paths: [
          '/toolName'
        ]
        kind: 'Hash'
      }
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

@description('The resource ID of the database')
output databaseId string = database.id
