metadata description = 'Deploys the Citizen Services Portal Web Application to Azure Container Apps.'

@description('The Azure region for the container app')
param location string = resourceGroup().location

@description('Tags to apply to the container app')
param tags object = {}

@description('Name of the Container App')
param containerAppName string = 'aldelar-csp-webapp'

@description('Name of the Container Apps Environment')
param containerAppsEnvironmentName string

@description('Name of the Container Registry')
param containerRegistryName string

@description('Container image to deploy')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('CPU cores for the container')
param containerCpuCoreCount string = '0.5'

@description('Memory for the container')
param containerMemory string = '1Gi'

@description('Minimum number of replicas')
@minValue(0)
@maxValue(30)
param containerMinReplicas int = 1

@description('Maximum number of replicas')
@minValue(1)
@maxValue(30)
param containerMaxReplicas int = 3

@description('Container port')
param targetPort int = 8080

@description('Enable external ingress')
param external bool = true

@description('Managed identity resource ID')
param identityId string = ''

@description('Managed identity client ID for DefaultAzureCredential')
param identityClientId string = ''

@description('Application Insights connection string')
@secure()
param applicationInsightsConnectionString string = ''

@description('CosmosDB endpoint URL')
param cosmosEndpoint string = ''

@description('CosmosDB database name')
param cosmosDatabase string = 'csp'

@description('CSP Agent endpoint URL')
param cspAgentUrl string = ''

@description('LADBS MCP Server URL')
param mcpLadbsUrl string = ''

@description('LADWP MCP Server URL')
param mcpLadwpUrl string = ''

@description('LASAN MCP Server URL')
param mcpLasanUrl string = ''

@description('CSP MCP Server URL for plan lifecycle and analytics')
param mcpCspUrl string = ''

@description('Microsoft Entra tenant ID for authentication')
param tenantId string = tenant().tenantId

@description('Enable Microsoft Entra authentication (Easy Auth)')
param enableAuthentication bool = false

@description('App Registration Client ID for Easy Auth')
param appClientId string = ''

@description('App Registration Client Secret for Easy Auth')
@secure()
param appClientSecret string = ''

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'csp-web-app' })
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
        ] : [],
        enableAuthentication && !empty(appClientSecret) ? [
          {
            name: 'microsoft-provider-authentication-secret'
            value: appClientSecret
          }
        ] : []
      )
    }
    template: {
      containers: [
        {
          name: 'webapp'
          image: containerImage
          resources: {
            cpu: json(containerCpuCoreCount)
            memory: containerMemory
          }
          env: concat(
            [
              // NiceGUI settings
              {
                name: 'NICEGUI_PORT'
                value: string(targetPort)
              }
              {
                name: 'NICEGUI_HOST'
                value: '0.0.0.0'
              }
              // Authentication - disable mock auth in Azure
              {
                name: 'USE_MOCK_AUTH'
                value: enableAuthentication ? 'false' : 'true'
              }
            ],
            // Application Insights
            !empty(applicationInsightsConnectionString) ? [
              {
                name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
                secretRef: 'appinsights-connection-string'
              }
            ] : [],
            // CosmosDB
            !empty(cosmosEndpoint) ? [
              {
                name: 'COSMOS_ENDPOINT'
                value: cosmosEndpoint
              }
              {
                name: 'COSMOS_DATABASE'
                value: cosmosDatabase
              }
            ] : [],
            // CSP Agent
            !empty(cspAgentUrl) ? [
              {
                name: 'CSP_AGENT_URL'
                value: cspAgentUrl
              }
            ] : [],
            // MCP Server URLs
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
            ] : [],
            // Managed Identity for Azure SDK authentication
            !empty(identityClientId) ? [
              {
                name: 'AZURE_CLIENT_ID'
                value: identityClientId
              }
            ] : []
          )
        }
      ]
      scale: {
        minReplicas: containerMinReplicas
        maxReplicas: containerMaxReplicas
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// Easy Auth configuration for Microsoft Entra ID authentication
// This enables automatic user authentication before reaching the web app
resource containerAppAuthConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = if (enableAuthentication && !empty(appClientId)) {
  name: 'current'
  parent: containerApp
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          openIdIssuer: '${environment().authentication.loginEndpoint}${tenantId}/v2.0'
          clientId: appClientId
          clientSecretSettingName: 'microsoft-provider-authentication-secret'
        }
        validation: {
          allowedAudiences: [
            'api://${appClientId}'
            appClientId
          ]
        }
      }
    }
  }
}

@description('The resource ID of the Container App')
output id string = containerApp.id

@description('The name of the Container App')
output name string = containerApp.name

@description('The FQDN of the Container App')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('The URI of the Container App')
output uri string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
