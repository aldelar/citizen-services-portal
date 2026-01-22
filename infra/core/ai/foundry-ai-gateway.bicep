metadata description = 'Configures AI Gateway integration between Foundry Project and APIM'

@description('The resource ID of the Foundry Project')
param foundryProjectId string

@description('The resource ID of the API Management instance')
param apimResourceId string

@description('Enable AI Gateway')
param enabled bool = true

// This is a deployment script that uses the Azure SDK to configure AI Gateway
// Since there's no direct Bicep resource type for this configuration yet
resource configureAiGateway 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'configure-ai-gateway'
  location: resourceGroup().location
  kind: 'AzureCLI'
  properties: {
    azCliVersion: '2.59.0'
    timeout: 'PT10M'
    retentionInterval: 'PT1H'
    environmentVariables: [
      {
        name: 'FOUNDRY_PROJECT_ID'
        value: foundryProjectId
      }
      {
        name: 'APIM_RESOURCE_ID'
        value: apimResourceId
      }
      {
        name: 'ENABLED'
        value: string(enabled)
      }
    ]
    scriptContent: '''
      #!/bin/bash
      set -e
      
      echo "Configuring AI Gateway..."
      echo "Project: $FOUNDRY_PROJECT_ID"
      echo "APIM: $APIM_RESOURCE_ID"
      
      # Use az rest to PATCH the project resource with AI Gateway configuration
      az rest --method PATCH \
        --url "${FOUNDRY_PROJECT_ID}?api-version=2025-10-01-preview" \
        --body "{\"properties\":{\"aiGateway\":{\"apimResourceId\":\"${APIM_RESOURCE_ID}\",\"enabled\":${ENABLED}}}}"
      
      echo "AI Gateway configured successfully"
    '''
    cleanupPreference: 'OnSuccess'
  }
}

@description('The deployment script resource ID')
output deploymentScriptId string = configureAiGateway.id
