## Microsoft Entra Authentication Setup

The LADBS MCP Server has been configured with **Microsoft Entra authentication** to secure access using Agent Identity.

### What Was Configured

- ✅ Azure Container Apps Easy Auth enabled on the MCP server
- ✅ JWT token validation configured for Microsoft Entra
- ✅ Scope URI exported: `mcpLadbsScopeUri` (get via `azd env get-value mcpLadbsScopeUri`)
- ✅ Agent configuration updated to use `entra_agent_identity` authentication

### Manual Configuration Required

To complete the authentication setup in the Foundry Portal:

1. Navigate to [Azure AI Foundry Portal](https://ai.azure.com)
2. Go to your project → **Tools** → **MCP Connections**
3. Find and edit the `mcp-ladbs` connection
4. Update authentication settings:
   - **Authentication Method**: Select "Microsoft Entra - Agent Identity"
   - **Scope URI**: Run `azd env get-value mcpLadbsScopeUri` and paste the value (format: `https://<app-name>.azurecontainerapps.io`)
5. Save the configuration

### How It Works

- **Development**: Agents use the Foundry Project's managed identity (shared identity)
- **Production**: Published agents get unique identities automatically
- **Authentication Flow**: Agent → Requests token from Entra → Container Apps validates token → MCP server processes request

### Troubleshooting

If the agent cannot access the MCP server:
- Verify the scope URI matches: `azd env get-value mcpLadbsScopeUri`
- Check the authentication is set to "Agent Identity" (not "Unauthenticated")
- Ensure the agent is using the latest configuration
- Check Container App logs: `az containerapp logs show --name aldelar-csp-mcp-ladbs --resource-group csp --follow`
