#!/bin/bash
set -e

echo "🔧 Fixing MCP Server Authentication Configuration..."
echo "=================================================="
echo ""

# Get configuration from azd environment
APP_ID=$(azd env get-value MCP_LADBS_APP_CLIENT_ID)
SUBSCRIPTION_ID=$(azd env get-value AZURE_SUBSCRIPTION_ID)
RESOURCE_GROUP=$(azd env get-value resourceGroupName)
TENANT_ID=$(az account show --query tenantId -o tsv)

if [ -z "$APP_ID" ]; then
  echo "❌ ERROR: MCP_LADBS_APP_CLIENT_ID not set. Run setup-mcp-auth.sh first."
  exit 1
fi

echo "📋 Configuration:"
echo "   App ID: $APP_ID"
echo "   Tenant ID: $TENANT_ID"
echo "   Resource Group: $RESOURCE_GROUP"
echo ""

# Construct the correct auth config payload
# Note: audiences should NOT have extra quotes around them
AUTH_CONFIG_PAYLOAD=$(cat <<EOF
{
  "properties": {
    "platform": {
      "enabled": true
    },
    "globalValidation": {
      "unauthenticatedClientAction": "Return401"
    },
    "identityProviders": {
      "azureActiveDirectory": {
        "enabled": true,
        "registration": {
          "openIdIssuer": "https://login.microsoftonline.com/${TENANT_ID}/v2.0",
          "clientId": "${APP_ID}"
        },
        "validation": {
          "allowedAudiences": [
            "api://${APP_ID}",
            "${APP_ID}"
          ]
        }
      }
    }
  }
}
EOF
)

echo "🔄 Updating Easy Auth configuration..."
echo "   Setting allowedAudiences to:"
echo "      - api://${APP_ID}"
echo "      - ${APP_ID}"
echo ""

# Update the auth config directly via ARM REST API
az rest --method PUT \
  --uri "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/containerApps/aldelar-csp-mcp-ladbs/authConfigs/current?api-version=2023-05-01" \
  --headers "Content-Type=application/json" \
  --body "$AUTH_CONFIG_PAYLOAD" \
  -o json > /dev/null

echo "✅ Auth configuration updated successfully!"
echo ""

# Verify the update
echo "🔍 Verifying configuration..."
CURRENT_CONFIG=$(az rest --method GET \
  --uri "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/containerApps/aldelar-csp-mcp-ladbs/authConfigs/current?api-version=2023-05-01" \
  --query "properties.identityProviders.azureActiveDirectory.validation.allowedAudiences" -o json)

echo "   Current allowedAudiences: $CURRENT_CONFIG"
echo ""

# Check for the quote issue
if echo "$CURRENT_CONFIG" | grep -q "'api://"; then
  echo "⚠️  WARNING: Still seeing extra quotes. This may be a display issue."
else
  echo "✅ Configuration looks correct!"
fi

echo ""
echo "📋 Next Steps:"
echo "   1. Re-deploy the agent: cd src/agents && uv run deploy.py ladbs"
echo "   2. Test in Foundry Portal"
echo ""
