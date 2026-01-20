metadata description = 'Creates a user-assigned managed identity for service-to-service authentication.'

@description('The Azure region for the identity')
param location string = resourceGroup().location

@description('Tags to apply to the identity')
param tags object = {}

@description('Name of the managed identity')
param identityName string

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: tags
}

@description('The resource ID of the managed identity')
output identityId string = managedIdentity.id

@description('The name of the managed identity')
output identityName string = managedIdentity.name

@description('The principal ID of the managed identity')
output principalId string = managedIdentity.properties.principalId

@description('The client ID of the managed identity')
output clientId string = managedIdentity.properties.clientId
