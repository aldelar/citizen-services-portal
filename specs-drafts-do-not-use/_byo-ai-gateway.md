# Bring Your Own AI Gateway - APIM Integration

**Status**: Planned  
**Date**: January 22, 2026  
**Author**: Technical Architecture Team

## Overview

This document outlines our approach to integrate Azure API Management (APIM) as a "third-party gateway" connection in Azure AI Foundry. While we're using our own APIM instance, we're configuring it as a ModelGateway connection rather than a native APIM connection to work around regional limitations in North Central US.

## Problem Statement

### Current Challenges

1. **Regional Limitation**: Azure AI Foundry's native AI Gateway feature is not available in North Central US region
2. **Direct APIM Integration**: Native APIM integration (category: "ApiManagement") may not be fully supported in North Central US
3. **Hosted Agents Requirement**: Hosted Agents feature (future requirement) is only available in North Central US
4. **Migration Complexity**: Moving to East US 2 or Sweden Central would require significant infrastructure changes

### Requirements

- ✅ Stay in North Central US region
- ✅ Expose AI models through APIM gateway (Azure OpenAI, etc.)
- ✅ Support Hosted Agents (North Central US only)
- ✅ Maintain enterprise-grade API management
- ✅ Enable centralized gateway control for AI model access
- ✅ Use Microsoft Entra ID for authentication

## Solution: APIM as Third-Party Gateway

### Approach

We will leverage Azure AI Foundry's **"Bring Your Own Gateway"** feature by configuring our existing APIM Standard tier instance as a **ModelGateway** (third-party) connection instead of using the native APIM integration.

**Use Case**: Expose AI models (Azure OpenAI, OpenAI, etc.) through APIM using ModelGateway connection. This is the documented, validated pattern from Microsoft Foundry samples.

**Key Insight**: By treating our APIM as a "third-party gateway," we gain:
- Regional flexibility (works in North Central US)
- Full control over gateway configuration and policies
- Centralized entry point for all AI model access
- Validation of the ModelGateway approach
- Foundation for multi-provider AI model routing

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│            Foundry Agent (North Central US)              │
│    Uses AI Models for reasoning (GPT-4.1, GPT-4.1-mini, etc.)  │
└──────────────────────────┬──────────────────────────────┘
                           │
                           │ ModelGateway Connection
                           │ (AuthType: AAD - Project Managed Identity)
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Azure APIM (Standard Tier)                  │
│                  North Central US                        │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │           AI Models API                        │    │
│  │           /openai                              │    │
│  │  - Chat completions                            │    │
│  │  - Model discovery                             │    │
│  │  - Embeddings                                  │    │
│  └──────────────────────┬─────────────────────────┘    │
└─────────────────────────┼────────────────────────────────┘
                          │
                          │ APIM Policies:
                          │ - Validate Foundry token
                          │ - APIM managed identity auth
                          │ - Route to Azure OpenAI
                          │
                          ▼
               ┌──────────────────────┐
               │   Azure OpenAI       │
               │   (AI Models)        │
               │   - gpt-4.1-mini     │
               │   - gpt-4.1          │
               │   - text-embedding   │
               │     -3-small         │
               └──────────────────────┘
```

### Authentication Flow

```
1. Agent needs AI model inference → Uses ModelGateway connection
2. Foundry routes request → APIM gateway with Project Managed Identity token
3. APIM validates token → Entra ID token validation policy
4. Token validation checks:
   - Valid Entra ID token from Foundry Project
   - Audience: https://cognitiveservices.azure.com (for Azure OpenAI)
   - Required claim: xms_mirid matches Foundry Project resource ID
5. APIM authenticates to backend → Uses APIM's managed identity
6. APIM forwards request → Azure OpenAI backend
7. Azure OpenAI processes → Returns chat completion response
8. Response flows back through APIM → Agent receives AI model output
```

**Key Points**:
- **Foundry → APIM**: Project Managed Identity token (validated by APIM)
- **APIM → Azure OpenAI**: APIM's Managed Identity (separate auth context)
- **Security**: Two-layer validation (Foundry project authorization + APIM-to-OpenAI authentication)
- **Monitoring**: All requests logged in APIM for observability

## Implementation Details

### 1. Foundry ModelGateway Connection

**Resource Type**: `Microsoft.MachineLearningServices/workspaces/connections`

**Purpose**: Connect Foundry agents to AI models (Azure OpenAI, OpenAI, etc.) hosted behind APIM

**Configuration**:
```json
{
  "name": "apim-ai-models-gateway",
  "properties": {
    "category": "ModelGateway",
    "target": "https://{apim-name}.azure-api.net/openai",
    "authType": "AAD",
    "credentials": {},
    "metadata": {
      "deploymentInPath": "true",
      "inferenceAPIVersion": "2024-02-01",
      "models": [
        {
          "name": "gpt-4.1-mini",
          "properties": {
            "model": {
              "name": "gpt-4.1-mini",
              "version": "2025-04-14",
              "format": "OpenAI"
            }
          }
        },
        {
          "name": "gpt-4.1",
          "properties": {
            "model": {
              "name": "gpt-4.1",
              "version": "2025-04-14",
              "format": "OpenAI"
            }
          }
        },
        {
          "name": "text-embedding-3-small",
          "properties": {
            "model": {
              "name": "text-embedding-3-small",
              "version": "1",
              "format": "OpenAI"
            }
          }
        }
      ],
      "customHeaders": {
        "X-Client-App": "foundry-agents"
      }
    }
  }
}
```

**Key Fields**:
- `category`: `"ModelGateway"` - Treat as third-party gateway (not native APIM integration)
- `authType`: `"AAD"` - Use Azure Active Directory (Project Managed Identity)
- `credentials`: Empty object - Managed Identity handles authentication
- `deploymentInPath`: `"true"` - Azure OpenAI pattern: `/deployments/{model}/chat/completions`
- `inferenceAPIVersion`: API version for chat completions requests
- `models`: Static list of AI models available through APIM
- `format`: `"OpenAI"` - OpenAI-compatible chat completion API

### 2. APIM Policy Configuration

**Location**: Operation-level policy for chat completions endpoint (`/openai/deployments/{deploymentId}/chat/completions`)

```xml
<policies>
  <inbound>
    <choose>
      <when condition="@(context.Subscription == null)">
        <!-- Managed Identity Authentication from Foundry Project -->
        <validate-azure-ad-token 
          tenant-id="{{tenantId}}"
          header-name="Authorization"
          failed-validation-httpcode="401"
          failed-validation-error-message="Unauthorized. Valid Entra token required."
          output-token-variable-name="jwt">
          <audiences>
            <audience>https://cognitiveservices.azure.com</audience>
          </audiences>
          <required-claims>
            <claim name="xms_mirid" match="any">
              <value>{{foundryProjectResourceId}}</value>
            </claim>
          </required-claims>
        </validate-azure-ad-token>
        
        <!-- Use APIM's managed identity to call Azure OpenAI -->
        <authentication-managed-identity resource="https://cognitiveservices.azure.com" />
        <set-backend-service base-url="https://{{azureOpenAIEndpoint}}" />
      </when>
      <otherwise>
        <!-- Fallback: API Key authentication for testing -->
        <set-backend-service backend-id="azure-openai-backend" />
      </otherwise>
    </choose>
    
    <base />
  </inbound>
  
  <backend>
    <base />
  </backend>
  
  <outbound>
    <base />
  </outbound>
  
  <on-error>
    <base />
  </on-error>
</policies>
```

**Policy Components**:

1. **Token Validation** (`validate-azure-ad-token`):
   - Validates Entra ID token from Foundry Project Managed Identity
   - Checks audience: `https://cognitiveservices.azure.com`
   - Verifies `xms_mirid` claim contains Foundry Project resource ID
   - Ensures only authorized Foundry projects can access AI models
   
2. **Backend Authentication** (`authentication-managed-identity`):
   - APIM uses its own managed identity to call Azure OpenAI
   - Separates concerns: Foundry authorizes project, APIM authenticates to OpenAI
   - Enables RBAC on Azure OpenAI (grant access to APIM identity, not all Foundry projects)
   
3. **Backend Routing** (`set-backend-service`):
   - Routes to Azure OpenAI endpoint
   - APIM acts as authenticated gateway to AI models
   - Dynamic routing can support multiple AI backends

4. **Dual Authentication Support**:
   - **Primary**: Managed Identity from Foundry (production)
   - **Fallback**: APIM subscription key (testing/development)
   - Conditional logic based on `context.Subscription`

5. **Observability**:
   - All requests logged in APIM
   - Token claims available for monitoring
   - Integration with Application Insights

### 3. APIM API Configuration

**Purpose**: Expose Azure OpenAI models through APIM

```bicep
resource azureOpenAIApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' = {
  name: 'azure-openai-gateway'
  parent: apimService
  properties: {
    displayName: 'Azure OpenAI Gateway'
    path: 'openai'
    protocols: ['https']
    subscriptionRequired: false  // Allow managed identity auth without subscription key
    type: 'http'
    serviceUrl: 'https://${azureOpenAIEndpoint}'
  }
}

// Chat completions operation
resource chatCompletionsOp 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  name: 'chat-completions'
  parent: azureOpenAIApi
  properties: {
    displayName: 'Create Chat Completion'
    method: 'POST'
    urlTemplate: '/deployments/{deploymentId}/chat/completions'
    templateParameters: [
      {
        name: 'deploymentId'
        type: 'string'
        required: true
        description: 'Model deployment ID (e.g., gpt-4.1-mini, gpt-4.1, text-embedding-3-small)'
      }
    ]
  }
}

// Embeddings operation
resource embeddingsOp 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  name: 'embeddings'
  parent: azureOpenAIApi
  properties: {
    displayName: 'Create Embeddings'
    method: 'POST'
    urlTemplate: '/deployments/{deploymentId}/embeddings'
    templateParameters: [
      {
        name: 'deploymentId'
        type: 'string'
        required: true
        description: 'Embedding model deployment ID'
      }
    ]
  }
}

// Model discovery operations (optional - for dynamic discovery)
resource listModelsOp 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  name: 'list-models'
  parent: azureOpenAIApi
  properties: {
    displayName: 'List Model Deployments'
    method: 'GET'
    urlTemplate: '/deployments'
  }
}

resource getModelOp 'Microsoft.ApiManagement/service/apis/operations@2023-05-01-preview' = {
  name: 'get-model'
  parent: azureOpenAIApi
  properties: {
    displayName: 'Get Model Deployment'
    method: 'GET'
    urlTemplate: '/deployments/{deploymentId}'
    templateParameters: [
      {
        name: 'deploymentId'
        type: 'string'
        required: true
      }
    ]
  }
}
```

### 4. Agent Configuration

**agent.yaml** (Example Agent):
```yaml
name: citizen-services-agent
model: apim-ai-models-gateway/gpt-4.1-mini  # Use AI model through APIM
instructions: |
  You are a helpful assistant for citizen services.
  Help users with inquiries and provide accurate information.

tools:
  # Tools defined with direct endpoints (not through ModelGateway)
  # MCP servers, REST APIs, functions, etc. can be configured here
  # These tools point directly to their respective endpoints
```

**Key Configuration**:
- **model**: Points to ModelGateway connection + specific model deployment
  - Format: `{connection-name}/{deployment-id}`
  - Example: `apim-ai-models-gateway/gpt-4.1-mini`
  - This routes AI reasoning through APIM to Azure OpenAI
  
- **tools**: Can include various tool types
  - Tools define their own endpoints directly
  - No need for gateway connections for non-AI-model tools
  - Examples: MCP servers, REST APIs, custom functions

**Environment Variables**:
```bash
# AI Model Connection
APIM_AI_CONNECTION_NAME="apim-ai-models-gateway"

# Azure OpenAI (backend)
AZURE_OPENAI_ENDPOINT="https://${AZURE_OPENAI_NAME}.openai.azure.com"

# APIM Gateway
APIM_GATEWAY_URL="${APIM_SERVICE_NAME}.azure-api.net"

# Foundry Project
FOUNDRY_PROJECT_CONNECTION_STRING="<project-connection-string>"
```

## Bicep Implementation

### Connection Module

**File**: `infra/core/gateway/foundry-modelgateway-connection.bicep`

```bicep
@description('Foundry Project resource ID')
param foundryProjectId string

@description('APIM gateway URL')
param apimGatewayUrl string

@description('Connection name')
param connectionName string

@description('MCP server models/tools list')
param mcpModels array = []

resource foundryProject 'Microsoft.MachineLearningServices/workspaces@2024-07-01-preview' existing = {
  name: split(foundryProjectId, '/')[8]
}

resource modelGatewayConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-07-01-preview' = {
  name: connectionName
  parent: foundryProject
  properties: {
    category: 'ModelGateway'
    target: apimGatewayUrl
    authType: 'AAD'
    credentials: {}
    metadata: {
      deploymentInPath: 'false'
      models: mcpModels
      customHeaders: {
        'X-MCP-Protocol': '1.0'
        'X-Client-App': 'foundry-agents'
      }
    }
  }
}

output connectionId string = modelGatewayConnection.id
output connectionName string = modelGatewayConnection.name
```

### APIM Policy Module

**File**: `infra/core/gateway/apim-mcp-policy.bicep`

```bicep
@description('APIM service name')
param apimServiceName string

@description('MCP API name')
param mcpApiName string

@description('Tenant ID')
param tenantId string

@description('MCP Container App client ID')
param mcpClientId string

@description('Foundry Project resource ID')
param foundryProjectResourceId string

@description('MCP server FQDN')
param mcpServerFqdn string

resource apimService 'Microsoft.ApiManagement/service@2023-05-01-preview' existing = {
  name: apimServiceName
}

resource mcpApi 'Microsoft.ApiManagement/service/apis@2023-05-01-preview' existing = {
  name: mcpApiName
  parent: apimService
}

resource mcpPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-05-01-preview' = {
  name: 'policy'
  parent: mcpApi
  properties: {
    format: 'xml'
    value: '''
      <policies>
        <inbound>
          <choose>
            <when condition="@(context.Subscription == null)">
              <validate-azure-ad-token 
                tenant-id="${tenantId}"
                header-name="Authorization"
                failed-validation-httpcode="401"
                failed-validation-error-message="Unauthorized. Valid Entra token required."
                output-token-variable-name="jwt">
                <audiences>
                  <audience>api://${mcpClientId}</audience>
                </audiences>
                <required-claims>
                  <claim name="xms_mirid" match="any">
                    <value>${foundryProjectResourceId}</value>
                  </claim>
                </required-claims>
              </validate-azure-ad-token>
              <set-backend-service base-url="https://${mcpServerFqdn}" />
            </when>
            <otherwise>
              <set-backend-service backend-id="mcp-backend" />
            </otherwise>
          </choose>
          <base />
        </inbound>
        <backend>
          <base />
        </backend>
        <outbound>
          <base />
        </outbound>
        <on-error>
          <base />
        </on-error>
      </policies>
    '''
  }
}
```

## Benefits

### ✅ Regional Flexibility
- **Stays in North Central US**: No infrastructure migration required
- **Hosted Agents Ready**: Compatible with future Hosted Agents feature (NCU only)
- **Gateway Availability**: ModelGateway works regardless of native AI Gateway regional rollout
- **Future-Proof**: Ready for regional expansion when native features arrive

### ✅ Enterprise Control
- **Centralized AI Management**: All AI model traffic through APIM
- **Policy Enforcement**: Rate limiting, caching, monitoring, security policies
- **Audit Trail**: Complete request/response logging in APIM for AI models
- **Cost Optimization**: Single gateway for multiple AI backends (Azure OpenAI, OpenAI, etc.)
- **Flexible Routing**: Support for multiple AI providers through single gateway

### ✅ Security
- **Zero Trust**: Every request validated via Entra ID
- **Managed Identity**: No secrets in configuration
- **Least Privilege**: Project identity scoped to specific resources
- **Claim Validation**: Ensures requests from authorized Foundry projects only
- **Separation of Concerns**: Foundry authorization + APIM-to-OpenAI authentication

### ✅ Scalability
- **Production-Ready**: APIM Standard tier handles enterprise scale
- **Multiple AI Backends**: Can route to Azure OpenAI, OpenAI, other providers
- **Load Balancing**: APIM provides built-in load balancing
- **Caching**: APIM can cache AI model responses for performance
- **Auto-scaling**: APIM scales with demand

### ✅ Developer Experience
- **Standard Foundry Patterns**: Uses documented ModelGateway connection
- **Familiar Tools**: Standard agent.yaml configuration
- **Easy Testing**: APIM test console for debugging AI API calls
- **Clear Separation**: Gateway logic separate from application logic
- **Monitoring**: APIM analytics and Application Insights integration
- **Multi-Model Support**: Easy to add new models through configuration

## Validation Approach

### Phase 1: APIM + MCP Setup
1. ✅ Deploy APIM with MCP API definition
2. ✅ Configure APIM policies for token validation
3. ✅ Test APIM → MCP flow with test tokens
4. ✅ Verify token claims and audience validation

### Phase 2: Foundry Connection
1. Create ModelGateway connection via Bicep
2. Configure static model list (MCP servers)
3. Deploy connection to Foundry Project
4. Validate connection appears in Foundry portal

### Phase 3: Agent Integration
1. Update agent.yaml to use APIM connection
2. Test agent → APIM → MCP flow
3. Verify Managed Identity authentication
4. Validate end-to-end MCP tool invocation

### Phase 4: Production Validation
1. Load testing through APIM gateway
2. Monitoring and observability setup
3. Security audit of token validation
4. Documentation and runbooks

## Comparison: Native vs Third-Party Gateway

| Aspect | Native AI Gateway | Native APIM | BYO Gateway via APIM (Our Approach) |
|--------|------------------|-------------|--------------------------------------|
| **Region Support** | ❌ Not in NCU | ⚠️ Limited in NCU | ✅ Available everywhere |
| **Hosted Agents** | ❌ Would need migration | ⚠️ Unknown | ✅ NCU compatible |
| **AI Model Routing** | 🟢 Native feature | 🟢 Full APIM control | 🟢 ModelGateway connection |
| **Control** | 🟡 Foundry-managed | 🟢 Full APIM control | 🟢 Full APIM control |
| **Complexity** | 🟢 Low (if available) | 🟡 Medium | 🟡 Medium |
| **Documentation** | ❌ Not public | 🟡 Partial | 🟢 Full Foundry samples |
| **Use Case** | 🟡 Preview feature | 🟡 Regional rollout | 🟢 Standard gateway pattern |
| **Cost** | 🟢 Included | 🟢 Existing APIM | 🟢 Existing APIM |
| **Monitoring** | 🟡 Basic | 🟢 Enterprise APIM | 🟢 Enterprise APIM |
| **Multi-Provider** | 🟡 Limited | 🟢 Full support | 🟢 Full support |
| **Policy Flexibility** | 🟡 Limited | 🟢 Full control | 🟢 Full control |

## Known Limitations

### Current Constraints
1. **Manual Connection Creation**: No UI support yet for ModelGateway, must use Bicep/ARM templates or Azure CLI
2. **Static Model List**: AI models must be pre-defined in connection metadata (can also use dynamic discovery)
3. **Token Scope**: Must match target audience exactly (`https://cognitiveservices.azure.com` for Azure OpenAI)
4. **APIM Tier**: Standard v2 or Premium required for managed identity policies (Basic tier insufficient)
5. **API Versioning**: Must keep `inferenceAPIVersion` in sync with Azure OpenAI API versions

### Workarounds
1. **CLI Deployment**: Use `az deployment group create` or Bicep for connection provisioning
2. **Dynamic Discovery**: Configure APIM to expose `/deployments` and `/deployments/{id}` endpoints
3. **Token Configuration**: Document required scopes clearly in agent configuration and APIM policies
4. **APIM Upgrade**: Already on Standard tier (no action needed)
5. **Version Management**: Use APIM policy to dynamically set API version based on request headers

### Not Currently Supported
1. ❌ UI-based ModelGateway connection creation (CLI/Bicep only)
2. ❌ Real-time model deployment updates (requires connection metadata update)
3. ❌ Token caching at APIM level (each request validates token)
4. ❌ Automatic failover between multiple Azure OpenAI instances

## Future Enhancements

### Short Term
- [ ] Add dynamic model discovery for Azure OpenAI deployments
- [ ] Implement model-specific rate limiting policies in APIM
- [ ] Enable APIM response caching for AI model responses (reduce costs)
- [ ] Add multiple AI providers (OpenAI, Anthropic) through single gateway
- [ ] Implement request/response transformation policies for different model formats
- [ ] Add embeddings endpoint support
- [ ] Token usage tracking and quota management per project

### Medium Term
- [ ] Implement token caching to reduce authentication overhead
- [ ] Add per-project rate limiting (based on `xms_mirid` claim)
- [ ] Integrate comprehensive observability (APIM + App Insights + Foundry telemetry)
- [ ] Load balancing across multiple Azure OpenAI instances
- [ ] Support additional AI model providers (Anthropic, Gemini, Mistral, etc.)
- [ ] Implement circuit breaker patterns for backend failures
- [ ] Cost allocation and chargeback per project/team

### Long Term
- [ ] Multi-region APIM deployment with Azure Front Door
- [ ] Gateway federation across multiple APIM instances
- [ ] Advanced routing based on agent context (team, project, environment)
- [ ] Intelligent model selection based on cost/performance metrics
- [ ] Automated model discovery and registration from multiple providers
- [ ] A/B testing framework for model comparisons
- [ ] Fine-tuned model integration and versioning

## References

### Official Documentation
- [Foundry Samples - APIM Integration](https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/01-connections/apim-and-modelgateway-integration-guide.md)
- [APIM Setup Guide for Agents](https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/01-connections/apim/apim-setup-guide-for-agents.md)
- [APIM Connection Objects](https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/01-connections/apim/APIM-Connection-Objects.md)
- [ModelGateway Setup Guide](https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/01-connections/model-gateway/modelgateway-setup-guide-for-agents.md)
- [ModelGateway Connection Objects](https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/01-connections/model-gateway/ModelGateway-Connection-Objects.md)

### Azure Documentation
- [Azure API Management GenAI Gateway Capabilities](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities)
- [Azure AI Foundry API in APIM](https://learn.microsoft.com/en-us/azure/api-management/azure-ai-foundry-api)
- [Managed Identity Authentication](https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)

### Internal Documentation
- [APIM Infrastructure](../infra/core/gateway/api-management.bicep)
- [Azure OpenAI Deployment](../infra/core/ai/openai-deployment.bicep)
- [Foundry Project Setup](../infra/core/ai/foundry-project.bicep)

## Next Steps

### Phase 1: Design and Planning
1. **Review and Approval**: Team review of ModelGateway approach for AI models
2. **Architecture Validation**: Confirm APIM Standard tier supports required policies
3. **RBAC Planning**: Define Azure OpenAI RBAC assignments for APIM managed identity
4. **Model Selection**: Identify which AI models to expose (gpt-4.1-mini, gpt-4.1, text-embedding-3-small)

### Phase 2: Infrastructure Implementation
1. **Bicep Modules**: 
   - Create ModelGateway connection module for AI models
   - Configure APIM API for Azure OpenAI
   - Set up APIM policies for token validation and managed identity auth
   - Configure APIM managed identity with Cognitive Services permissions
2. **RBAC Configuration**:
   - Grant APIM managed identity "Cognitive Services OpenAI User" role on Azure OpenAI
   - Verify Foundry Project managed identity can access APIM
3. **Testing**:
   - Validate APIM → Azure OpenAI flow with managed identity
   - Test model discovery (static list initially)
   - Verify chat completions endpoint
   - Test token validation policies

### Phase 3: Agent Integration
1. **Connection Deployment**: Deploy ModelGateway connection via `azd provision`
2. **Agent Configuration**:
   - Update agent.yaml to use ModelGateway connection
   - Configure model: `apim-ai-models-gateway/gpt-4.1-mini`
   - Set environment variables
3. **End-to-End Testing**:
   - Test agent reasoning with AI models through APIM
   - Validate authentication flow
   - Verify response quality and latency

### Phase 4: Production Deployment
1. **Production Rollout**: Full deployment via `azd up`
2. **Monitoring Setup**: 
   - Configure APIM analytics dashboards
   - Set up Application Insights integration
   - Enable Foundry telemetry
   - Create alerts for failures, latency, token issues
3. **Security Audit**: 
   - Validate token flows end-to-end
   - Review claim validation logic
   - Test audience checks and RBAC
   - Penetration testing
4. **Documentation**: 
   - Update README with ModelGateway setup
   - Create operations guide for troubleshooting
   - Document monitoring and alerting
   - Team training materials

### Phase 5: Optimization
1. **Performance Tuning**: 
   - Implement response caching policies
   - Optimize connection pooling
   - Tune timeout values
   - Load testing and optimization
2. **Cost Optimization**: 
   - Analyze APIM usage patterns
   - Implement rate limiting
   - Review Azure OpenAI token consumption
   - Set up cost alerts
3. **Observability**: 
   - Build comprehensive dashboards
   - Define SLOs and SLIs
   - Implement distributed tracing
4. **Future Expansion**: 
   - Plan for additional AI providers
   - Design multi-region strategy
   - Evaluate dynamic model discovery

---

**Status**: Ready for Implementation  
**Risk Level**: Low-Medium  
**Estimated Effort**: 3-4 days development + 2 days testing  
**Dependencies**: 
- Existing APIM Standard tier instance
- Azure OpenAI deployment
- Foundry Project with managed identity
- RBAC permissions on Azure OpenAI

**Value Proposition**: Enables AI model access in North Central US without regional migration, maintains Hosted Agents compatibility, provides enterprise-grade API management for all AI traffic.
