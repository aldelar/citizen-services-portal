metadata description = 'Creates API Management API for AI model endpoints'

@description('Name of the API Management instance')
param apimName string

@description('API path prefix')
param apiPath string = 'ai/v1'

@description('API display name')
param displayName string = 'AI Models API'

@description('API description text')
param apiDescription string = 'API for accessing OpenAI models through AI Gateway'

@description('Foundry endpoint for backend')
param foundryEndpoint string = ''

// Reference existing APIM
resource apim 'Microsoft.ApiManagement/service@2023-05-01-preview' existing = {
  name: apimName
}

// AI Models API
resource aiModelsApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  parent: apim
  name: 'ai-models-api'
  properties: {
    displayName: displayName
    description: apiDescription
    path: apiPath
    protocols: ['https']
    subscriptionRequired: true
    type: 'http'
  }
}

// API Policy for AI models
resource aiModelsPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  parent: aiModelsApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: '<policies><inbound><base />${!empty(foundryEndpoint) ? '<set-backend-service base-url="${foundryEndpoint}" />' : ''}<rate-limit calls="100" renewal-period="60" /><cors><allowed-origins><origin>*</origin></allowed-origins><allowed-methods><method>POST</method><method>GET</method></allowed-methods><allowed-headers><header>*</header></allowed-headers></cors></inbound><backend><base /></backend><outbound><base /></outbound><on-error><base /></on-error></policies>'
  }
}

// GPT-5-Mini Operation
resource gpt5MiniOperation 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  parent: aiModelsApi
  name: 'gpt-5-mini-chat'
  properties: {
    displayName: 'Chat with GPT-5-Mini'
    method: 'POST'
    urlTemplate: '/chat/gpt-5-mini'
    description: 'Send chat completion request to GPT-5-Mini model'
    request: {
      description: 'Chat request'
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

// GPT-5.2 Operation
resource gpt52Operation 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  parent: aiModelsApi
  name: 'gpt-52-chat'
  properties: {
    displayName: 'Chat with GPT-5.2'
    method: 'POST'
    urlTemplate: '/chat/gpt-5.2'
    description: 'Send chat completion request to GPT-5.2 model'
    request: {
      description: 'Chat request'
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

// Text Embedding Operation  
resource textEmbeddingOperation 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  parent: aiModelsApi
  name: 'text-embedding-3-small'
  properties: {
    displayName: 'Generate Embeddings'
    method: 'POST'
    urlTemplate: '/embeddings/text-embedding-3-small'
    description: 'Generate text embeddings using text-embedding-3-small model'
    request: {
      description: 'Embedding request'
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

@description('AI Models API resource ID')
output apiId string = aiModelsApi.id

@description('AI Models API name')
output apiName string = aiModelsApi.name

@description('API path')
output apiPath string = apiPath
