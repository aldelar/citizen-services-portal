metadata description = 'Creates ACR connection and RBAC for Azure AI Foundry Project hosted agents.'

targetScope = 'resourceGroup'

@description('AI Foundry account name')
param foundryName string

@description('AI Foundry project name')
param projectName string

@description('Container Registry name')
param containerRegistryName string

@description('Connection name for the ACR')
param connectionName string = 'acr-connection'

// Reference the Foundry account and project
resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryName

  resource project 'projects' existing = {
    name: projectName
  }
}

// Reference the Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

// Role IDs
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'        // AcrPull
var azureAiUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'   // Azure AI User

// Grant the Foundry Project identity AcrPull role on the ACR
// This allows the capability host to pull agent container images
resource projectAcrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, foundry::project.id, acrPullRoleId)
  scope: containerRegistry
  properties: {
    principalId: foundry::project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

// Grant the Foundry Project identity Azure AI User role on the Foundry Account
// This allows the agent to use the AI models deployed on the account
resource projectAzureAiUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, foundry::project.id, azureAiUserRoleId)
  scope: foundry
  properties: {
    principalId: foundry::project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiUserRoleId)
  }
}

// Create the ACR connection on the Foundry project
// This tells the capability host where to pull container images from
resource acrConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: foundry::project
  name: connectionName
  properties: {
    category: 'ContainerRegistry'
    target: containerRegistry.properties.loginServer
    authType: 'ManagedIdentity'
    isSharedToAll: true
    credentials: {
      clientId: foundry::project.identity.principalId
      resourceId: containerRegistry.id
    }
    metadata: {
      ResourceId: containerRegistry.id
    }
  }
  dependsOn: [
    projectAcrPullRole  // Ensure RBAC is set before connection
    projectAzureAiUserRole
  ]
}

// Outputs
output connectionName string = acrConnection.name
output connectionId string = acrConnection.id
output projectPrincipalId string = foundry::project.identity.principalId
