metadata description = 'Creates blob containers for agency knowledge base documents.'

@description('Name of the storage account')
param storageAccountName string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageAccountName
}

resource blobServices 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' existing = {
  parent: storageAccount
  name: 'default'
}

resource ladbsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'ladbs-docs'
  properties: {
    publicAccess: 'None'
  }
}

resource ladwpContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'ladwp-docs'
  properties: {
    publicAccess: 'None'
  }
}

resource lasanContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobServices
  name: 'lasan-docs'
  properties: {
    publicAccess: 'None'
  }
}

output containerNames array = [
  ladbsContainer.name
  ladwpContainer.name
  lasanContainer.name
]
