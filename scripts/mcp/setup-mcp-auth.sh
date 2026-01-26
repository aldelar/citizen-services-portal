#!/bin/bash
set -e

# Setup MCP Server Authentication with App Registration
# This script creates an App Registration for the MCP server and configures access

echo "🔐 Setting up MCP Server Authentication..."

# Get required values
MCP_FQDN=$(azd env get-value mcpLadbsFqdn)
FOUNDRY_PROJECT_PRINCIPAL_ID=$(az resource show \
  --ids $(azd env get-value foundryProjectEndpoint | sed 's|https://||' | sed 's|.services.ai.azure.com.*||')/projects/$(azd env get-value foundryProjectName) \
  --query identity.principalId -o tsv 2>/dev/null || echo "")

if [ -z "$FOUNDRY_PROJECT_PRINCIPAL_ID" ]; then
  # Alternative way to get the principal ID
  SUBSCRIPTION_ID=$(azd env get-value AZURE_SUBSCRIPTION_ID)
  RESOURCE_GROUP=$(azd env get-value resourceGroupName)
  FOUNDRY_NAME=$(azd env get-value foundryName)
  PROJECT_NAME=$(azd env get-value foundryProjectName)
  
  FOUNDRY_PROJECT_PRINCIPAL_ID=$(az rest \
    --method get \
    --uri "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${FOUNDRY_NAME}/projects/${PROJECT_NAME}?api-version=2025-10-01-preview" \
    --query identity.principalId -o tsv)
fi

echo "📋 MCP Server FQDN: $MCP_FQDN"
echo "🔑 Foundry Project Principal ID: $FOUNDRY_PROJECT_PRINCIPAL_ID"

# Check if App Registration already exists
APP_REG_NAME="mcp-ladbs-server"
APP_ID=$(az ad app list --display-name "$APP_REG_NAME" --query "[0].appId" -o tsv)

if [ -z "$APP_ID" ]; then
  echo "📝 Creating App Registration: $APP_REG_NAME"
  
  # Create App Registration without identifier URI first
  APP_ID=$(az ad app create \
    --display-name "$APP_REG_NAME" \
    --sign-in-audience AzureADMyOrg \
    --query appId -o tsv)
  
  echo "✅ Created App Registration with App ID: $APP_ID"
  
  # Now update with proper identifier URI using the App ID
  az ad app update --id "$APP_ID" --identifier-uris "api://$APP_ID"
  echo "✅ Set identifier URI: api://$APP_ID"
else
  echo "✅ App Registration already exists with App ID: $APP_ID"
fi

# Get the Service Principal (create if doesn't exist)
SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv)

if [ -z "$SP_ID" ]; then
  echo "📝 Creating Service Principal..."
  SP_ID=$(az ad sp create --id "$APP_ID" --query id -o tsv)
  echo "✅ Created Service Principal: $SP_ID"
else
  echo "✅ Service Principal already exists: $SP_ID"
fi

# Configure App Roles for service-to-service authentication
echo "📝 Configuring App Roles for managed identities..."

# Get the object ID of the app
APP_OBJECT_ID=$(az ad app show --id "$APP_ID" --query id -o tsv)

# Check if App Roles already exist
EXISTING_ROLES=$(az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID" \
  --query "appRoles" -o json 2>/dev/null)

APP_ROLE_COUNT=$(echo "$EXISTING_ROLES" | jq '. | length' 2>/dev/null || echo "0")

if [ "$APP_ROLE_COUNT" == "0" ]; then
  # No roles exist, create new one for service-to-service
  APP_ROLE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
  
  az rest --method PATCH \
    --uri "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID" \
    --headers "Content-Type=application/json" \
    --body "{
      \"appRoles\": [{
        \"allowedMemberTypes\": [\"Application\"],
        \"description\": \"Allow managed identities to access MCP server tools\",
        \"displayName\": \"MCP.Access\",
        \"id\": \"$APP_ROLE_ID\",
        \"isEnabled\": true,
        \"value\": \"MCP.Access\"
      }]
    }"
  
  echo "✅ App Role configured: MCP.Access"
else
  APP_ROLE_ID=$(echo "$EXISTING_ROLES" | jq -r '.[0].id')
  echo "✅ App Role already configured (ID: $APP_ROLE_ID)"
fi

# Grant the Foundry Project identity access to the app
echo "📝 Granting Foundry Project identity access to App Role..."

# Check if role assignment already exists
EXISTING_ASSIGNMENT=$(az rest \
  --method get \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignedTo" \
  --query "value[?principalId=='$FOUNDRY_PROJECT_PRINCIPAL_ID']" -o tsv 2>/dev/null || echo "")

if [ -z "$EXISTING_ASSIGNMENT" ]; then
  # Assign the Foundry Project managed identity to the App Role
  az rest --method POST \
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignedTo" \
    --headers "Content-Type=application/json" \
    --body "{
      \"principalId\": \"$FOUNDRY_PROJECT_PRINCIPAL_ID\",
      \"resourceId\": \"$SP_ID\",
      \"appRoleId\": \"$APP_ROLE_ID\"
    }"
  
  echo "✅ Granted Foundry Project identity access to MCP server"
else
  echo "✅ Foundry Project identity already has access"
fi

# Save values to azd environment
azd env set MCP_LADBS_APP_ID "$APP_ID"
azd env set MCP_LADBS_APP_CLIENT_ID "$APP_ID"
azd env set MCP_LADBS_TENANT_ID "$(az account show --query tenantId -o tsv)"

echo ""
echo "✅ Authentication setup complete!"
echo ""
echo "📋 Configuration Summary:"
echo "   App Registration: $APP_REG_NAME"
echo "   App ID (Client ID): $APP_ID"
echo "   Scope URI: api://$APP_ID/MCP.Access"
echo "   Audience: api://$APP_ID"
echo ""
echo "🔄 Next steps:"
echo "   1. Run: azd provision"
echo "   2. Update MCP connection in Portal with:"
echo "      - Authentication: Microsoft Entra - Project Managed Identity"
echo "      - Audience: api://$APP_ID"
echo ""
