metadata description = 'Creates API Management API for MCP server endpoints'

@description('Name of the API Management instance')
param apimName string

@description('API path prefix')
param apiPath string = 'mcp/v1'

@description('API display name')
param displayName string = 'MCP Services API'

@description('API description text')
param apiDescription string = 'API for accessing MCP servers providing government service tools'

@description('LADBS MCP Server URI')
param ladbsMcpUri string

// Reference existing APIM
resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' existing = {
  name: apimName
}

// MCP Services API
resource mcpServicesApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'mcp-services-api'
  properties: {
    displayName: displayName
    description: apiDescription
    path: apiPath
    protocols: ['https']
    subscriptionRequired: true
    type: 'http'
  }
}

// API Policy for MCP services
resource mcpServicesPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  parent: mcpServicesApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '<policies><inbound><base /><rate-limit calls="100" renewal-period="60" /><cors allow-credentials="true"><allowed-origins><origin>*</origin></allowed-origins><allowed-methods><method>POST</method><method>GET</method></allowed-methods><allowed-headers><header>*</header></allowed-headers></cors></inbound><backend><retry condition="@(context.Response.StatusCode >= 500)" count="3" interval="1" /><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>'
  }
}

// LADBS Operation
resource ladbsOperation 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  parent: mcpServicesApi
  name: 'mcp-ladbs'
  properties: {
    displayName: 'LADBS MCP Server'
    method: 'POST'
    urlTemplate: '/ladbs'
    description: 'Forward requests to LADBS MCP Server for building permits, inspections, and violations'
    request: {
      description: 'MCP request'
      headers: []
      representations: [
        {
          contentType: 'application/json'
        }
      ]
    }
    responses: [
      {
        statusCode: 200
        description: 'Success'
        representations: [
          {
            contentType: 'application/json'
          }
        ]
      }
    ]
  }
}

// LADBS Operation Policy - route to Container App
resource ladbsOperationPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2023-05-01-preview' = {
  parent: ladbsOperation
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '<policies><inbound><base /><set-backend-service base-url="${ladbsMcpUri}" /><rewrite-uri template="/mcp" /></inbound><backend><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>'
  }
}

@description('MCP Services API resource ID')
output apiId string = mcpServicesApi.id

@description('MCP Services API name')
output apiName string = mcpServicesApi.name

@description('API path')
output apiPath string = apiPath
