metadata description = 'Deploys the LADWP MCP server to Azure Container Apps.'

@description('The Azure region for the container app')
param location string = resourceGroup().location

@description('Tags to apply to the container app')
param tags object = {}

@description('Name of the Container App')
param containerAppName string = 'aldelar-csp-mcp-ladwp'

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

@description('LADWP API endpoint (optional)')
param ladwpApiEndpoint string = ''

@description('LADWP API key (optional)')
@secure()
param ladwpApiKey string = ''

@description('Name of the CosmosDB account')
param cosmosDbAccountName string = ''

@description('CosmosDB endpoint URL')
param cosmosEndpoint string = ''

@description('Microsoft Entra tenant ID for authentication')
param tenantId string = tenant().tenantId

@description('Enable Microsoft Entra authentication')
param enableAuthentication bool = true

@description('App Registration Client ID for authentication')
param appClientId string = ''

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

// Deploy LADWP CosmosDB database
module cosmosDb '../../../src/mcp-servers/ladwp/infra/cosmos-db.bicep' = if (!empty(cosmosDbAccountName)) {
  name: 'ladwp-cosmos-db-deployment'
  params: {
    cosmosDbAccountName: cosmosDbAccountName
    location: location
    tags: tags
  }
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'mcp-ladwp' })
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
      // Microsoft Entra authentication for agent identity access
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
        !empty(ladwpApiKey) ? [
          {
            name: 'ladwp-api-key'
            value: ladwpApiKey
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
            !empty(ladwpApiEndpoint) ? [
              {
                name: 'LADWP_API_ENDPOINT'
                value: ladwpApiEndpoint
              }
            ] : [],
            !empty(ladwpApiKey) ? [
              {
                name: 'LADWP_API_KEY'
                secretRef: 'ladwp-api-key'
              }
            ] : [],
            !empty(cosmosEndpoint) ? [
              {
                name: 'COSMOS_ENDPOINT'
                value: cosmosEndpoint
              }
              {
                name: 'COSMOS_DATABASE'
                value: 'ladwp'
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

// Microsoft Entra authentication configuration
// This enables Azure Container Apps Easy Auth to validate JWT tokens from Microsoft Entra
// For Foundry Project identity authentication, the token audience will be api://<AppId>
resource containerAppAuthConfig 'Microsoft.App/containerApps/authConfigs@2023-05-01' = if (enableAuthentication) {
  name: 'current'
  parent: containerApp
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'Return401'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          // openIdIssuer uses the environment's authentication endpoint for multi-cloud support
          openIdIssuer: '${environment().authentication.loginEndpoint}${tenantId}/v2.0'
          // clientId must be the App Registration's Application (client) ID
          clientId: appClientId
        }
        validation: {
          // allowedAudiences must match what the Foundry agent identity requests
          // Foundry requests tokens with scope "api://<appId>/.default" which results in audience "api://<appId>"
          allowedAudiences: [
            'api://${appClientId}'
            appClientId  // Also allow the raw App ID as audience (some token issuers use this)
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
