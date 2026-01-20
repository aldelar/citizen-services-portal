metadata description = 'Creates an Azure Container App.'

@description('The Azure region for the container app')
param location string = resourceGroup().location

@description('Tags to apply to the container app')
param tags object = {}

@description('Name of the Container App')
param name string

@description('Name of the Container Apps Environment')
param containerAppsEnvironmentName string

@description('Container image to deploy')
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Name of the Container Registry (required for custom images)')
param containerRegistryName string

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
param containerMaxReplicas int = 10

@description('Container port')
param targetPort int = 80

@description('Enable external ingress')
param external bool = true

@description('Environment variables')
param environmentVariables array = []

@description('Managed identity resource ID')
param identityId string = ''

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: containerAppsEnvironmentName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: containerRegistryName
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: location
  tags: tags
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
      secrets: [
        {
          name: 'registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
      ]
    }
    template: {
      containers: [
        {
          name: name
          image: containerImage
          resources: {
            cpu: json(containerCpuCoreCount)
            memory: containerMemory
          }
          env: environmentVariables
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
