metadata description = 'Assigns RBAC roles for Azure Storage Account data plane operations'
metadata displayName = 'Storage Account RBAC Assignments'

@description('The name of the storage account')
param storageAccountName string

@description('The principal ID of the user to grant contributor access')
param userPrincipalId string = ''

@description('The principal ID of the AI Search service (for blob data reader)')
param searchPrincipalId string = ''

@description('The principal ID of the managed identity (for blob data reader)')
param identityPrincipalId string = ''

// Built-in Azure role definition IDs
// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roles = {
  // Storage Blob Data Contributor - read, write, and delete access to blob data
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  
  // Storage Blob Data Reader - read access to blob data
  storageBlobDataReader: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
}

// Reference to the storage account for scope
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

// Assign Storage Blob Data Contributor role to user
resource userBlobContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (userPrincipalId != '') {
  name: guid(storageAccount.id, userPrincipalId, roles.storageBlobDataContributor)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataContributor)
    principalId: userPrincipalId
    principalType: 'User'
  }
}

// Assign Storage Blob Data Reader role to AI Search service
resource searchBlobReaderRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (searchPrincipalId != '') {
  name: guid(storageAccount.id, searchPrincipalId, roles.storageBlobDataReader)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataReader)
    principalId: searchPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Assign Storage Blob Data Reader role to managed identity
resource identityBlobReaderRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (identityPrincipalId != '') {
  name: guid(storageAccount.id, identityPrincipalId, roles.storageBlobDataReader)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataReader)
    principalId: identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}
