metadata description = 'Deploys the CSP Agent to Azure Container Apps.'

@description('The Azure region for the container app')
param location string = resourceGroup().location

@description('Tags to apply to the container app')
param tags object = {}

@description('Name of the Container App')
param containerAppName string = 'aldelar-csp-agent'

@description('Name of the Container Apps Environment')
param containerAppsEnvironmentName string

@description('Name of the Container Registry')
param containerRegistryName string

@description('Container image to deploy')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('CPU cores for the container')
param containerCpuCoreCount string = '1.0'

@description('Memory for the container')
param containerMemory string = '2Gi'

@description('Minimum number of replicas')
@minValue(0)
@maxValue(30)
param containerMinReplicas int = 1

@description('Maximum number of replicas')
@minValue(1)
@maxValue(30)
param containerMaxReplicas int = 3

@description('Container port')
param targetPort int = 8088

@description('Enable external ingress')
param external bool = true

@description('Managed identity resource ID')
param identityId string = ''

@description('Managed identity client ID for DefaultAzureCredential')
param identityClientId string = ''

@description('Application Insights connection string')
@secure()
param applicationInsightsConnectionString string = ''

@description('Azure OpenAI endpoint')
param azureOpenAiEndpoint string = ''

@description('Azure OpenAI chat deployment name')
param azureOpenAiChatDeploymentName string = 'gpt-4.1'

@description('MCP LADBS URL')
param mcpLadbsUrl string = ''

@description('MCP LADWP URL')
param mcpLadwpUrl string = ''

@description('MCP LASAN URL')
param mcpLasanUrl string = ''

@description('MCP CSP URL for plan lifecycle and analytics')
param mcpCspUrl string = ''

@description('Azure AI Foundry project resource ID')
param agentProjectResourceId string = ''

@description('Azure AI Foundry project endpoint URL')
param agentProjectEndpoint string = ''

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'csp-agent' })
  identity: !empty(identityId) ? {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  } : {
    type: 'None'
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: external
        targetPort: targetPort
        transport: 'auto'
        allowInsecure: false
      }
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: concat(
        [
          {
            name: 'registry-password'
            value: containerRegistry.listCredentials().passwords[0].value
          }
        ],
        !empty(applicationInsightsConnectionString) ? [
          {
            name: 'appinsights-connection-string'
            value: applicationInsightsConnectionString
          }
        ] : []
      )
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: containerImage
          resources: {
            cpu: json(containerCpuCoreCount)
            memory: containerMemory
          }
          env: concat(
            [
              {
                name: 'AZURE_OPENAI_ENDPOINT'
                value: azureOpenAiEndpoint
              }
              {
                name: 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'
                value: azureOpenAiChatDeploymentName
              }
              {
                name: 'AGENT_PROJECT_RESOURCE_ID'
                value: agentProjectResourceId
              }
              {
                name: 'AZURE_AI_PROJECT_ENDPOINT'
                value: agentProjectEndpoint
              }
              {
                name: 'ENABLE_INSTRUMENTATION'
                value: 'true'
              }
              {
                name: 'ENABLE_SENSITIVE_DATA'
                value: 'true'
              }
              {
                name: 'OTEL_SERVICE_NAME'
                value: 'csp-agent'
              }
            ],
            !empty(applicationInsightsConnectionString) ? [
              {
                name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
                secretRef: 'appinsights-connection-string'
              }
            ] : [],
            !empty(identityClientId) ? [
              {
                name: 'AZURE_CLIENT_ID'
                value: identityClientId
              }
            ] : [],
            !empty(mcpLadbsUrl) ? [
              {
                name: 'MCP_LADBS_URL'
                value: mcpLadbsUrl
              }
            ] : [],
            !empty(mcpLadwpUrl) ? [
              {
                name: 'MCP_LADWP_URL'
                value: mcpLadwpUrl
              }
            ] : [],
            !empty(mcpLasanUrl) ? [
              {
                name: 'MCP_LASAN_URL'
                value: mcpLasanUrl
              }
            ] : [],
            !empty(mcpCspUrl) ? [
              {
                name: 'MCP_CSP_URL'
                value: mcpCspUrl
              }
            ] : []
          )
        }
      ]
      scale: {
        minReplicas: containerMinReplicas
        maxReplicas: containerMaxReplicas
      }
    }
  }
}

@description('The resource ID of the container app')
output id string = containerApp.id

@description('The name of the container app')
output name string = containerApp.name

@description('The FQDN of the container app')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('The URI of the container app')
output uri string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
