metadata description = 'Assigns RBAC roles for Azure Cosmos DB data plane operations using SQL Role Definitions'
metadata displayName = 'Cosmos DB RBAC Assignments'

@description('The name of the Cosmos DB account')
param cosmosDbAccountName string

@description('The principal ID of the user to grant access')
param userPrincipalId string = ''

@description('The principal ID of the managed identity (for MCP servers)')
param identityPrincipalId string = ''

// Built-in Cosmos DB SQL Role Definition IDs
// These are Cosmos DB's own RBAC system, not Azure RBAC
// See: https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-setup-rbac
var cosmosRoles = {
  // Cosmos DB Built-in Data Reader - read access to data plane
  dataReader: '00000000-0000-0000-0000-000000000001'
  
  // Cosmos DB Built-in Data Contributor - read/write access to data plane
  dataContributor: '00000000-0000-0000-0000-000000000002'
}

// Reference to the Cosmos DB account
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-11-15' existing = {
  name: cosmosDbAccountName
}

// Assign Data Contributor role to user (for development)
resource userCosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = if (userPrincipalId != '') {
  parent: cosmosDbAccount
  name: guid(cosmosDbAccount.id, userPrincipalId, cosmosRoles.dataContributor)
  properties: {
    roleDefinitionId: '${cosmosDbAccount.id}/sqlRoleDefinitions/${cosmosRoles.dataContributor}'
    principalId: userPrincipalId
    scope: cosmosDbAccount.id
  }
}

// Assign Data Contributor role to managed identity (for MCP servers - need read/write)
resource identityCosmosRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2023-11-15' = if (identityPrincipalId != '') {
  parent: cosmosDbAccount
  name: guid(cosmosDbAccount.id, identityPrincipalId, cosmosRoles.dataContributor)
  properties: {
    roleDefinitionId: '${cosmosDbAccount.id}/sqlRoleDefinitions/${cosmosRoles.dataContributor}'
    principalId: identityPrincipalId
    scope: cosmosDbAccount.id
  }
}
