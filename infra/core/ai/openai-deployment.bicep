metadata description = 'Deploys an Azure OpenAI model to an AI Foundry Hub'

@description('Name of the AI Foundry Hub')
param hubName string

@description('Name of the deployment')
param deploymentName string

@description('OpenAI model name and version')
param modelName string

@description('Model version')
param modelVersion string

@description('Deployment SKU (Standard, GlobalStandard, etc.)')
param sku string = 'GlobalStandard'

@description('Deployment capacity in TPM (Tokens Per Minute)')
param capacity int = 1000000

// OpenAI model deployment
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-04-01-preview' = {
  name: '${hubName}/${deploymentName}'
  sku: {
    name: sku
    capacity: capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.Default'
  }
}

@description('Deployment name')
output deploymentName string = modelDeployment.name

@description('Model name')
output modelName string = modelName

@description('Model version')
output modelVersion string = modelVersion
