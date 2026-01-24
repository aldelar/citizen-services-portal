# AI Gateway Configuration for Azure AI Foundry

## Overview

The AI Gateway integration between Azure API Management (APIM) and Azure AI Foundry provides centralized access control, rate limiting, and monitoring for AI models and MCP servers.

Documentation:
- [Bring your own AI gateway to Azure AI Agent Service (preview)](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/ai-gateway?view=foundry)
- [Bring Your Own AI Gateway to Foundry (Preview)](https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/01-connections/apim-and-modelgateway-integration-guide.md)

## Current Limitation

**APIM as AI Gateway configuration cannot be fully automated via Bicep/ARM** in Azure AI Foundry (as of January 2026). The configuration must be done either:
1. Manually through the Azure AI Foundry Portal (recommended for now)
2. Via undocumented data plane APIs (experimental)

## Option 1: Manual Configuration (Recommended)

This is the officially supported method:

### Steps

1. **Navigate to Azure AI Foundry Portal**
   ```
   https://ai.azure.com
   ```

2. **Go to your project settings**
   - Select your project: `aldelar-csp-foundry-project`
   - Click **Settings** → **AI Gateway**

3. **Select your APIM instance**
   ```
   Resource ID: $(azd env get-value apiManagementId)
   
   Or select from dropdown:
   /subscriptions/96f801df-f40d-4570-807d-7cdc6afe3e54/resourceGroups/csp/providers/Microsoft.ApiManagement/service/aldelar-csp-apim
   ```

4. **Save the configuration**

### Verification

After configuration:
- Go to your project → **Models**
- Model endpoints should now route through APIM
- Check APIM metrics to verify traffic

## Option 2: Automated via Data Plane API (Experimental)

⚠️ **Warning**: This uses undocumented APIs that may change

### Prerequisites

```bash
pip install azure-identity requests
```

### Script

A Python script is provided at `scripts/configure_ai_gateway.py` that attempts to configure the AI Gateway programmatically.

**Usage:**
```bash
cd scripts
python3 configure_ai_gateway.py
```

**What it does:**
1. Gets Foundry and APIM details from azd environment
2. Obtains an access token for the Foundry data plane
3. Attempts to call various API endpoints to configure the gateway
4. Falls back to manual instructions if unsuccessful

### Known Challenges

- The exact data plane API endpoint is not publicly documented
- Token scope requirements may vary
- API may require specific permissions beyond what Azure CLI provides

## Option 3: Browser DevTools Method (Manual but Faster)

1. Open Azure AI Foundry Portal in browser
2. Open browser Developer Tools (F12) → Network tab
3. Navigate to Settings → AI Gateway
4. Select your APIM instance and click Save
5. In Network tab, find the PUT/POST request
6. Copy the request as cURL or examine the payload
7. Use this for automation in CI/CD

**Typical request format:**
```bash
curl -X PUT \
  'https://aldelar-csp-foundry.services.ai.azure.com/api/projects/aldelar-csp-foundry-project/aiGateway' \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"apimResourceId": "/subscriptions/.../Microsoft.ApiManagement/service/aldelar-csp-apim", "enabled": true}'
```

## What AI Gateway Provides

Once configured, APIM acts as the AI Gateway and provides:

### For AI Models
- **Centralized access** to all AI models (gpt-4.1, gpt-4.1-mini, etc.)
- **Rate limiting** and quota management
- **Usage tracking** and cost allocation
- **Security policies** (authentication, authorization)

### For MCP Servers
- **Unified endpoint** for all MCP tools
- **Request/response logging**
- **Circuit breaker** patterns
- **Load balancing** across MCP server instances

## Architecture with AI Gateway

```
Agent → Foundry Agent Service → APIM (AI Gateway) → {
    - OpenAI Models (via Foundry)
    - MCP Servers (via Container Apps)
}
```

**Without AI Gateway:**
```
Agent → Foundry Agent Service → Direct to Models/MCP Servers
```

## Benefits

| Feature | Without Gateway | With Gateway |
|---------|----------------|--------------|
| Centralized Control | ❌ | ✅ |
| Rate Limiting | Model-level only | Unified across all services |
| Monitoring | Separate per service | Unified dashboard |
| Cost Tracking | Per-service | Cross-service analytics |
| Security Policies | Per-service config | Centralized policies |

## Next Steps

After configuring AI Gateway:

1. **Update Agent Definitions** to use APIM endpoints:
   ```yaml
   # In agent.yaml
   tools:
     - type: mcp
       server_url: ${APIM_GATEWAY_URL}/mcp/v1/mcp-ladbs
   ```

2. **Configure APIM Policies** for rate limiting, authentication

3. **Set up Monitoring** in APIM for usage analytics

4. **Test Agent Connectivity** through the gateway

## Troubleshooting

### Gateway not showing models
- Verify APIM is in same region as Foundry
- Check APIM managed identity has Cognitive Services User role on Foundry

### MCP server tools not accessible
- Verify APIM can reach Container Apps
- Check APIM policies aren't blocking requests
- Verify authentication is properly configured

### Performance issues
- Enable caching in APIM policies
- Check APIM tier (Standard supports higher throughput than Developer)
- Monitor APIM capacity metrics

## References

- [Azure API Management Documentation](https://learn.microsoft.com/en-us/azure/api-management/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)
- [AI Gateway Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/architecture/ai-gateway)
