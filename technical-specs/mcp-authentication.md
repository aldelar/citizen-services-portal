# MCP Server Authentication

## Current Status: DISABLED

Authentication for the LADBS MCP Server is currently **disabled**. The MCP server is accessible without authentication.

> ⚠️ **Security Note**: In production, authentication should be enabled to protect MCP endpoints.

---

## Authentication Attempts (January 2026)

### Approach: Microsoft Entra + Container Apps Easy Auth

We attempted to configure Microsoft Entra authentication using an App Registration and Azure Container Apps Easy Auth to secure the MCP server with Foundry Project managed identity.

### What Was Configured

1. **App Registration**: `mcp-ladbs-server`
   - App ID: `f62275c4-1c17-45dc-a662-85c49f3cbce1`
   - Identifier URI: `api://f62275c4-1c17-45dc-a662-85c49f3cbce1`
   - App Role: `MCP.Access` (for service-to-service auth)

2. **Container Apps Easy Auth**:
   - Enabled with `Return401` for unauthenticated requests
   - OpenID Issuer: `https://login.microsoftonline.com/{tenantId}/v2.0`
   - Client ID: `f62275c4-1c17-45dc-a662-85c49f3cbce1`
   - Allowed Audiences: `api://f62275c4-1c17-45dc-a662-85c49f3cbce1`, `f62275c4-1c17-45dc-a662-85c49f3cbce1`

3. **Foundry Project Identity**:
   - System-assigned managed identity on Foundry Project
   - App Role assignment granted to the identity

4. **Agent Configuration**:
   - Authentication type: `entra_agent_identity`
   - Scope: `api://f62275c4-1c17-45dc-a662-85c49f3cbce1/.default`

### Error Encountered

When the agent attempted to call the MCP server with authentication enabled:

```
Error encountered while enumerating tools from remote server: 
https://aldelar-csp-mcp-ladbs.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io:443/mcp. 
Details: Response status code does not indicate success: 403 (Forbidden).
```

### Analysis

- **401 (Unauthorized)** would mean the token was rejected → Easy Auth configuration issue
- **403 (Forbidden)** means the token was **accepted** but authorization failed

The 403 error indicates:
1. Easy Auth validated the token successfully
2. The identity in the token was not authorized to access the resource
3. This could be an App Role assignment issue or a permission configuration problem

### Possible Root Causes

1. **App Role not properly assigned** to the Foundry Project managed identity
2. **Foundry Project identity** may not be the identity used by the agent at runtime
3. **Published/deployed agents** may use a different identity than the Project identity
4. **Container Apps Easy Auth** may require additional authorization configuration

### Scripts Created

The following scripts were created during this effort:

- `scripts/setup-mcp-auth.sh` - Creates App Registration and assigns roles
- `scripts/fix-mcp-auth.sh` - Fixes Easy Auth configuration
- `scripts/test-mcp-auth.sh` - Tests authentication flow
- `src/agents/test_easy_auth.py` - Python test for Easy Auth

### Bicep Configuration

Authentication can be re-enabled in `infra/main.bicep`:

```bicep
module mcpLadbs './app/mcp-ladbs.bicep' = {
  // ...
  params: {
    // ...
    enableAuthentication: true  // Set to true to enable
    appClientId: 'f62275c4-1c17-45dc-a662-85c49f3cbce1'
  }
}
```

---

## Future Work

To properly secure the MCP server, investigate:

1. **Which identity does the Foundry agent actually use?**
   - Development vs. published agent identities
   - Check token claims in Container App logs

2. **Alternative authentication methods**:
   - API Key authentication
   - Azure API Management with subscription keys
   - VNet integration with private endpoints

3. **Container Apps Easy Auth authorization**:
   - Review `defaultAuthorizationPolicy.allowedApplications` configuration
   - Verify App Role assignment via Microsoft Graph API

---

## References

- [Azure Container Apps Easy Auth](https://learn.microsoft.com/en-us/azure/container-apps/authentication)
- [Microsoft Entra App Registrations](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)
- [Foundry Agent Identity](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/develop/create-hub-project-sdk)
