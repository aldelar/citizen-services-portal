metadata description = 'Creates a connection on an Azure AI Foundry Project.'

targetScope = 'resourceGroup'

@description('AI Foundry account name')
param foundryName string

@description('AI Foundry project name')
param projectName string

// Connection configuration type definition
type ConnectionConfig = {
  @description('Name of the connection')
  name: string
  
  @description('Category of the connection (e.g., ContainerRegistry, AzureStorageAccount, CognitiveSearch)')
  category: string
  
  @description('Target endpoint or URL for the connection')
  target: string
  
  @description('Authentication type')
  authType: 'AAD' | 'AccessKey' | 'AccountKey' | 'ApiKey' | 'CustomKeys' | 'ManagedIdentity' | 'None' | 'OAuth2' | 'PAT' | 'SAS' | 'ServicePrincipal' | 'UsernamePassword'
  
  @description('Whether the connection is shared to all users (optional, defaults to true)')
  isSharedToAll: bool?
  
  @description('Credentials for non-ApiKey authentication types (optional)')
  credentials: object?
  
  @description('Additional metadata for the connection (optional)')
  metadata: object?
}

@description('Connection configuration')
param connectionConfig ConnectionConfig

@secure()
@description('API key for ApiKey based connections (optional)')
param apiKey string = ''


// Get reference to the Foundry account and project
resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryName

  resource project 'projects' existing = {
    name: projectName
  }
}

// Create the connection
resource connection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: foundry::project
  name: connectionConfig.name
  properties: {
    category: connectionConfig.category
    target: connectionConfig.target
    authType: connectionConfig.authType
    isSharedToAll: connectionConfig.?isSharedToAll ?? true
    credentials: connectionConfig.authType == 'ApiKey' ? {
      key: apiKey
    } : connectionConfig.?credentials
    metadata: connectionConfig.?metadata
  }
}

// Outputs
output connectionName string = connection.name
output connectionId string = connection.id
