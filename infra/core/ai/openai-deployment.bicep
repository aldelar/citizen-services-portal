metadata description = 'Deploys an Azure OpenAI model to an AI Foundry account'

@description('Name of the AI Foundry account')
param foundryName string

@description('Name of the deployment')
param deploymentName string

@description('OpenAI model name')
param modelName string

@description('Model version')
param modelVersion string = 'latest'

@description('Deployment SKU (Standard, GlobalStandard, etc.)')
param sku string = 'GlobalStandard'

@description('Deployment capacity in TPM (Tokens Per Minute)')
param capacity int = 1000000

// Reference the Foundry account
resource foundry 'Microsoft.CognitiveServices/accounts@2025-10-01-preview' existing = {
  name: foundryName
}

// OpenAI model deployment to NEW Foundry
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-10-01-preview' = {
  parent: foundry
  name: deploymentName
  sku: {
    capacity: capacity
    name: sku
  }
  properties: {
    model: {
      name: modelName
      format: 'OpenAI'
      version: modelVersion
    }
  }
}

@description('Deployment name')
output deploymentName string = modelDeployment.name

@description('Model name')
output modelName string = modelName

@description('Model version')
output modelVersion string = modelVersion
