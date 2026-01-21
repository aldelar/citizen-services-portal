metadata description = 'Assigns RBAC roles for Azure AI Foundry data plane operations'
metadata displayName = 'Foundry RBAC Assignments'

@description('The resource ID of the Foundry account')
param foundryId string

@description('The principal ID of the user or service principal to grant access')
param principalId string

@description('The type of principal (User, Group, or ServicePrincipal)')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
])
param principalType string = 'User'

// Built-in Azure role definition IDs
// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roles = {
  // Cognitive Services User - full data plane access including agents
  // Data Actions: Microsoft.CognitiveServices/*
  cognitiveServicesUser: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  
  // Azure AI Developer - access to view and work with AI resources
  azureAIDeveloper: '64702f94-c441-49e6-a78b-ef80e0188fee'
}

// Reference to the Foundry account for scope
resource resourceInfo 'Microsoft.CognitiveServices/accounts@2025-10-01-preview' existing = {
  name: last(split(foundryId, '/'))
}

// Assign Cognitive Services User role
resource cognitiveServicesUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryId, principalId, roles.cognitiveServicesUser)
  scope: resourceInfo
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.cognitiveServicesUser)
    principalId: principalId
    principalType: principalType
  }
}

// Assign Azure AI Developer role
resource azureAIDeveloperRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryId, principalId, roles.azureAIDeveloper)
  scope: resourceInfo
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.azureAIDeveloper)
    principalId: principalId
    principalType: principalType
  }
}

@description('Role assignment ID for Cognitive Services User')
output cognitiveServicesUserRoleAssignmentId string = cognitiveServicesUserRoleAssignment.id

@description('Role assignment ID for Azure AI Developer')
output azureAIDeveloperRoleAssignmentId string = azureAIDeveloperRoleAssignment.id
