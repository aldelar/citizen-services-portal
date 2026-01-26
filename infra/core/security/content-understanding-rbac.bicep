metadata description = 'Assigns RBAC roles for Azure Content Understanding data plane operations'
metadata displayName = 'Content Understanding RBAC Assignments'

@description('The resource ID of the Content Understanding account')
param contentUnderstandingId string

@description('The principal ID of the user to grant access')
param userPrincipalId string = ''

@description('The principal ID of the AI Search service')
param searchPrincipalId string = ''

@description('The principal ID of the managed identity')
param identityPrincipalId string = ''

// Built-in Azure role definition IDs
// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roles = {
  // Cognitive Services User - data plane access (read/analyze)
  cognitiveServicesUser: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  
  // Cognitive Services Contributor - management + data plane access
  cognitiveServicesContributor: '25fbc0a9-bd7c-42a3-aa1a-3b75d497ee68'
}

// Reference to the Content Understanding account for scope
resource contentUnderstanding 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: last(split(contentUnderstandingId, '/'))
}

// Assign Cognitive Services Contributor role to user
resource userContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (userPrincipalId != '') {
  name: guid(contentUnderstandingId, userPrincipalId, roles.cognitiveServicesContributor)
  scope: contentUnderstanding
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.cognitiveServicesContributor)
    principalId: userPrincipalId
    principalType: 'User'
  }
}

// Assign Cognitive Services User role to AI Search service
resource searchUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (searchPrincipalId != '') {
  name: guid(contentUnderstandingId, searchPrincipalId, roles.cognitiveServicesUser)
  scope: contentUnderstanding
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.cognitiveServicesUser)
    principalId: searchPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Assign Cognitive Services User role to managed identity
resource identityUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (identityPrincipalId != '') {
  name: guid(contentUnderstandingId, identityPrincipalId, roles.cognitiveServicesUser)
  scope: contentUnderstanding
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.cognitiveServicesUser)
    principalId: identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}
