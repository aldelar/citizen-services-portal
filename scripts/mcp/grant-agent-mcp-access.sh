#!/bin/bash
set -e

# Grant a published agent access to the MCP server
# Usage: ./grant-agent-mcp-access.sh <agent-name>

AGENT_NAME=${1:-"ladbs-assistant"}

echo "🔐 Granting Agent Access to MCP Server"
echo "======================================="
echo ""

# Get configuration
APP_ID=$(azd env get-value MCP_LADBS_APP_CLIENT_ID)
SUBSCRIPTION_ID=$(azd env get-value AZURE_SUBSCRIPTION_ID)
RESOURCE_GROUP=$(azd env get-value resourceGroupName)
FOUNDRY_NAME=$(azd env get-value foundryName)
PROJECT_NAME=$(azd env get-value foundryProjectName)

echo "📋 Configuration:"
echo "   Agent Name: $AGENT_NAME"
echo "   MCP App ID: $APP_ID"
echo ""

# Get the agent deployment details
echo "🔍 Looking for agent deployment..."
AGENT_DEPLOYMENT=$(az rest \
  --method GET \
  --uri "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${FOUNDRY_NAME}/projects/${PROJECT_NAME}/agents?api-version=2025-10-01-preview" \
  --query "value[?name=='${AGENT_NAME}'] | [0]" -o json 2>/dev/null || echo "{}")

if [ "$AGENT_DEPLOYMENT" == "{}" ] || [ -z "$AGENT_DEPLOYMENT" ]; then
  echo "❌ Agent '$AGENT_NAME' not found or not published."
  echo ""
  echo "To publish the agent:"
  echo "   cd src/agents && export foundryProjectEndpoint=\$(azd env get-value foundryProjectEndpoint) && \\"
  echo "   export AZURE_SUBSCRIPTION_ID=\$(azd env get-value AZURE_SUBSCRIPTION_ID) && \\"
  echo "   export resourceGroupName=\$(azd env get-value resourceGroupName) && \\"
  echo "   export foundryName=\$(azd env get-value foundryName) && \\"
  echo "   export foundryProjectName=\$(azd env get-value foundryProjectName) && \\"
  echo "   export SERVICE_MCP_LADBS_URI=\$(azd env get-value mcpLadbsUri) && \\"
  echo "   export MCP_LADBS_SCOPE_URI=\$(azd env get-value mcpLadbsScopeUri) && \\"
  echo "   uv run deploy.py ladbs"
  exit 1
fi

# Check if agent has managed identity
AGENT_PRINCIPAL_ID=$(echo "$AGENT_DEPLOYMENT" | jq -r '.identity.principalId // empty')

if [ -z "$AGENT_PRINCIPAL_ID" ]; then
  echo "❌ Agent does not have a managed identity."
  echo "   The agent might not be fully published yet or needs system-assigned identity."
  exit 1
fi

echo "✅ Found agent with principal ID: $AGENT_PRINCIPAL_ID"
echo ""

# Get the Service Principal for the MCP app
SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv)

# Get the App Role ID
APP_OBJECT_ID=$(az ad app show --id "$APP_ID" --query id -o tsv)
APP_ROLE_ID=$(az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID" \
  --query "appRoles[0].id" -o tsv)

echo "📝 Checking existing role assignments..."
EXISTING_ASSIGNMENT=$(az rest \
  --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignedTo" \
  --query "value[?principalId=='$AGENT_PRINCIPAL_ID']" -o json)

if [ "$EXISTING_ASSIGNMENT" != "[]" ]; then
  echo "✅ Agent already has access to MCP server"
else
  echo "📝 Granting agent access..."
  az rest --method POST \
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignedTo" \
    --headers "Content-Type=application/json" \
    --body "{
      \"principalId\": \"$AGENT_PRINCIPAL_ID\",
      \"resourceId\": \"$SP_ID\",
      \"appRoleId\": \"$APP_ROLE_ID\"
    }" > /dev/null
  
  echo "✅ Granted agent access to MCP server!"
fi

echo ""
echo "✅ Configuration Complete!"
echo ""
echo "📋 Agent Details:"
echo "   Name: $AGENT_NAME"
echo "   Principal ID: $AGENT_PRINCIPAL_ID"
echo "   Has MCP Access: Yes"
echo ""
echo "🧪 To test the agent:"
echo "   1. Go to Azure AI Foundry Portal: https://ai.azure.com"
echo "   2. Navigate to your project: $PROJECT_NAME"
echo "   3. Go to Agents → Find '$AGENT_NAME'"
echo "   4. Test with: 'Submit a permit for 123 Main St, kitchen remodel, \$25,000'"
echo ""
