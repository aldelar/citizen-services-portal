metadata description = 'Creates Log Analytics workspace and Application Insights for monitoring and observability.'

@description('The Azure region for the resources')
param location string = resourceGroup().location

@description('Tags to apply to all resources')
param tags object = {}

@description('Name of the Log Analytics workspace')
param logAnalyticsName string

@description('Name of the Application Insights instance')
param applicationInsightsName string

@description('Log Analytics workspace SKU')
@allowed([
  'PerGB2018'
  'CapacityReservation'
])
param logAnalyticsSku string = 'PerGB2018'

@description('Data retention in days')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: logAnalyticsSku
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

@description('The resource ID of the Log Analytics workspace')
output logAnalyticsWorkspaceId string = logAnalytics.id

@description('The name of the Log Analytics workspace')
output logAnalyticsWorkspaceName string = logAnalytics.name

@description('The resource ID of Application Insights')
output applicationInsightsId string = applicationInsights.id

@description('The name of Application Insights')
output applicationInsightsName string = applicationInsights.name

@description('Application Insights instrumentation key')
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey

@description('Application Insights connection string')
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString
