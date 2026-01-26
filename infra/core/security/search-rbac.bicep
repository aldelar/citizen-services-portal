metadata description = 'Assigns RBAC roles for Azure AI Search data plane operations'
metadata displayName = 'AI Search RBAC Assignments'

@description('The name of the AI Search service')
param searchServiceName string

@description('The principal ID of the user to grant access')
param userPrincipalId string = ''

@description('The principal ID of the managed identity (for MCP servers)')
param identityPrincipalId string = ''

// Built-in Azure role definition IDs for AI Search
// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roles = {
  // Search Index Data Reader - read access to search index data
  searchIndexDataReader: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  
  // Search Index Data Contributor - read/write access to search index data
  searchIndexDataContributor: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  
  // Search Service Contributor - manage search service but not data
  searchServiceContributor: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
}

// Reference to the search service for scope
resource searchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchServiceName
}

// Assign Search Index Data Contributor role to user (for development)
resource userSearchContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (userPrincipalId != '') {
  name: guid(searchService.id, userPrincipalId, roles.searchIndexDataContributor)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.searchIndexDataContributor)
    principalId: userPrincipalId
    principalType: 'User'
  }
}

// Assign Search Index Data Reader role to managed identity (for MCP servers)
resource identitySearchReaderRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (identityPrincipalId != '') {
  name: guid(searchService.id, identityPrincipalId, roles.searchIndexDataReader)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.searchIndexDataReader)
    principalId: identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}
