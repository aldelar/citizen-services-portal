metadata description = 'Deploys the LADBS MCP server to Azure Container Apps.'

@description('The Azure region for the container app')
param location string = resourceGroup().location

@description('Tags to apply to the container app')
param tags object = {}

@description('Name of the Container App')
param containerAppName string = 'aldelar-csp-mcp-ladbs'

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
param containerMinReplicas int = 0

@description('Maximum number of replicas')
@minValue(1)
@maxValue(30)
param containerMaxReplicas int = 5

@description('Container port')
param targetPort int = 8000

@description('Enable external ingress')
param external bool = true

@description('Managed identity resource ID')
param identityId string = ''

@description('Application Insights connection string')
@secure()
param applicationInsightsConnectionString string = ''

@description('LADBS API endpoint (optional)')
param ladbsApiEndpoint string = ''

@description('LADBS API key (optional)')
@secure()
param ladbsApiKey string = ''

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'mcp-ladbs' })
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
        !empty(ladbsApiKey) ? [
          {
            name: 'ladbs-api-key'
            value: ladbsApiKey
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
                name: 'MCP_SERVER_HOST'
                value: '0.0.0.0'
              }
              {
                name: 'MCP_SERVER_PORT'
                value: string(targetPort)
              }
            ],
            !empty(applicationInsightsConnectionString) ? [
              {
                name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
                secretRef: 'appinsights-connection-string'
              }
            ] : [],
            !empty(ladbsApiEndpoint) ? [
              {
                name: 'LADBS_API_ENDPOINT'
                value: ladbsApiEndpoint
              }
            ] : [],
            !empty(ladbsApiKey) ? [
              {
                name: 'LADBS_API_KEY'
                secretRef: 'ladbs-api-key'
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
            name: 'cpu-scaling'
            custom: {
              type: 'cpu'
              metadata: {
                type: 'Utilization'
                value: '70'
              }
            }
          }
        ]
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
