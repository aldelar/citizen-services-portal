metadata description = 'Assigns RBAC roles for accessing MCP servers hosted on Azure Container Apps'
metadata displayName = 'MCP Server RBAC Assignments'

@description('The resource ID of the Container App hosting the MCP server')
param containerAppId string

@description('The principal IDs of agents or managed identities to grant access')
param principalIds array

@description('The type of principals (User, Group, or ServicePrincipal)')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param principalType string = 'ServicePrincipal'

// Built-in Azure role definition IDs
// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roles = {
  // Reader - allows reading resource configuration and status
  // Required for agent identities to discover and invoke MCP servers
  reader: 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
}

// Reference to the Container App for scope
resource containerApp 'Microsoft.App/containerApps@2023-05-01' existing = {
  name: last(split(containerAppId, '/'))
}

// Assign Reader role to each principal
resource readerRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for principalId in principalIds: {
  name: guid(containerAppId, principalId, roles.reader)
  scope: containerApp
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.reader)
    principalId: principalId
    principalType: principalType
  }
}]

@description('Role assignment IDs for Reader')
output readerRoleAssignmentIds array = [for i in range(0, length(principalIds)): readerRoleAssignments[i].id]
