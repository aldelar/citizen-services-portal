#!/bin/bash
set -e

echo "🧪 Testing MCP Server Authentication Step-by-Step"
echo "=================================================="
echo ""

# Get configuration
APP_ID=$(azd env get-value MCP_LADBS_APP_CLIENT_ID)
MCP_URI=$(azd env get-value mcpLadbsUri)
TENANT_ID=$(az account show --query tenantId -o tsv)
SUBSCRIPTION_ID=$(azd env get-value AZURE_SUBSCRIPTION_ID)
RESOURCE_GROUP=$(azd env get-value resourceGroupName)
FOUNDRY_NAME=$(azd env get-value foundryName)
PROJECT_NAME=$(azd env get-value foundryProjectName)

echo "📋 Configuration:"
echo "   App ID: $APP_ID"
echo "   MCP URI: $MCP_URI"
echo "   Tenant ID: $TENANT_ID"
echo ""

# Step 1: Check Easy Auth configuration
echo "Step 1: Verify Easy Auth Configuration"
echo "---------------------------------------"
az rest --method GET \
  --uri "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.App/containerApps/aldelar-csp-mcp-ladbs/authConfigs/current?api-version=2023-05-01" \
  --query "{enabled:properties.platform.enabled, clientId:properties.identityProviders.azureActiveDirectory.registration.clientId, audiences:properties.identityProviders.azureActiveDirectory.validation.allowedAudiences}" \
  -o json
echo ""

# Step 2: Get Foundry Project Principal ID
echo "Step 2: Get Foundry Project Managed Identity"
echo "---------------------------------------------"
FOUNDRY_PROJECT_PRINCIPAL_ID=$(az rest \
  --method get \
  --uri "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/accounts/${FOUNDRY_NAME}/projects/${PROJECT_NAME}?api-version=2025-10-01-preview" \
  --query identity.principalId -o tsv)
echo "   Principal ID: $FOUNDRY_PROJECT_PRINCIPAL_ID"
echo ""

# Step 3: Check App Role Assignment
echo "Step 3: Verify App Role Assignment"
echo "-----------------------------------"
SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv)
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignedTo" \
  --query "value[?principalId=='$FOUNDRY_PROJECT_PRINCIPAL_ID'].{Principal:principalDisplayName, Role:appRoleId}" \
  -o table
echo ""

# Step 4: Get a token for the Foundry Project identity
echo "Step 4: Request Token (simulating Foundry Project identity)"
echo "------------------------------------------------------------"
echo "⚠️  Note: We'll use your user identity to get a token for testing"
echo "   (The actual Foundry Project MI token can only be obtained by the service)"
echo ""

# Get token using az account get-access-token with the app ID as resource
echo "   Requesting token with audience: api://$APP_ID"
TOKEN=$(az account get-access-token --resource "api://$APP_ID" --query accessToken -o tsv 2>&1 || echo "FAILED")

if [ "$TOKEN" == "FAILED" ] || [ -z "$TOKEN" ]; then
  echo "   ❌ Failed to get token with audience api://$APP_ID"
  echo ""
  echo "   Trying alternative: Get token for Azure management"
  TOKEN=$(az account get-access-token --resource "https://management.azure.com" --query accessToken -o tsv)
  echo "   ⚠️  Got management token (this won't work for MCP, but let's see what Easy Auth says)"
else
  echo "   ✅ Got token!"
fi
echo ""

# Step 5: Decode the token to see claims
echo "Step 5: Inspect Token Claims"
echo "-----------------------------"
PAYLOAD=$(echo "$TOKEN" | cut -d. -f2)
# Add padding if needed
case $((${#PAYLOAD} % 4)) in
  2) PAYLOAD="${PAYLOAD}==" ;;
  3) PAYLOAD="${PAYLOAD}=" ;;
esac
echo "$PAYLOAD" | base64 -d 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Could not decode token"
echo ""

# Step 6: Test the MCP endpoint without auth
echo "Step 6: Test MCP Endpoint Without Auth (expect 401)"
echo "----------------------------------------------------"
curl -s -o /dev/null -w "   HTTP Status: %{http_code}\n" "${MCP_URI}/mcp"
echo ""

# Step 7: Test the MCP endpoint with token
echo "Step 7: Test MCP Endpoint With Token"
echo "-------------------------------------"
RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "${MCP_URI}/mcp")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

echo "   HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "406" ]; then
  echo "   ✅ Authentication successful!"
  echo "   Response preview: ${BODY:0:200}"
elif [ "$HTTP_CODE" == "401" ]; then
  echo "   ❌ Still getting 401 Unauthorized"
  echo "   Response: $BODY"
  echo ""
  echo "   Possible issues:"
  echo "   1. Token audience doesn't match Easy Auth allowedAudiences"
  echo "   2. Token issuer not trusted"
  echo "   3. Token expired or invalid"
elif [ "$HTTP_CODE" == "403" ]; then
  echo "   ⚠️  Got 403 Forbidden (auth worked, but authorization failed)"
  echo "   This means Easy Auth accepted the token but app-level authz failed"
else
  echo "   ⚠️  Unexpected status code"
  echo "   Response: $BODY"
fi
echo ""

# Step 8: Summary
echo "Summary"
echo "-------"
echo "To fix authentication issues:"
echo ""
echo "1. Verify Easy Auth audiences match: api://$APP_ID"
echo "2. Verify Foundry Project has App Role assignment"
echo "3. In Portal MCP connection, use:"
echo "   - Authentication: Microsoft Entra - Project Managed Identity"
echo "   - Audience: api://$APP_ID"
echo ""
echo "For debugging, check Container App logs:"
echo "   az containerapp logs show --name aldelar-csp-mcp-ladbs --resource-group ${RESOURCE_GROUP} --follow --tail 50"
echo ""
