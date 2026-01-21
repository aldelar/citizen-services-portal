metadata description = 'Deploys an Azure OpenAI model to an AI Foundry workspace'

@description('Name of the AI Foundry workspace')
param foundryName string

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

// Reference the Foundry workspace
resource workspace 'Microsoft.MachineLearningServices/workspaces@2024-10-01-preview' existing = {
  name: foundryName
}

// OpenAI model deployment
resource modelDeployment 'Microsoft.MachineLearningServices/workspaces/onlineEndpoints@2024-10-01-preview' = {
  parent: workspace
  name: deploymentName
  properties: {
    authMode: 'Key'
    properties: {
      modelId: modelName
      modelVersion: modelVersion
    }
  }
}

@description('Deployment name')
output deploymentName string = modelDeployment.name

@description('Model name')
output modelName string = modelName

@description('Model version')
output modelVersion string = modelVersion
