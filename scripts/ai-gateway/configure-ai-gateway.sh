#!/bin/bash
# Configure AI Gateway for Azure AI Foundry Project
# This script programmatically configures APIM as the AI Gateway for the Foundry project

set -e

# Get values from azd environment
FOUNDRY_ENDPOINT=$(azd env get-value foundryEndpoint)
FOUNDRY_PROJECT_NAME=$(azd env get-value foundryProjectName)
APIM_ID=$(azd env get-value apiManagementId)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo "🔧 Configuring AI Gateway for Foundry Project..."
echo "   Foundry Endpoint: $FOUNDRY_ENDPOINT"
echo "   Project: $FOUNDRY_PROJECT_NAME"
echo "   APIM ID: $APIM_ID"

# Get access token for Foundry data plane
echo ""
echo "🔑 Getting access token..."
TOKEN=$(az account get-access-token --resource https://ml.azure.com --query accessToken -o tsv)

# Configure AI Gateway via Foundry data plane API
# Note: This is based on the portal's API calls - may need adjustments
echo ""
echo "📡 Configuring AI Gateway..."

GATEWAY_CONFIG=$(cat <<EOF
{
  "apimResourceId": "$APIM_ID",
  "enabled": true
}
EOF
)

# Call the Foundry API to configure AI Gateway
# The exact endpoint may vary - this is based on typical patterns
API_URL="$FOUNDRY_ENDPOINT/api/projects/$FOUNDRY_PROJECT_NAME/aiGateway"

curl -X PUT "$API_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$GATEWAY_CONFIG" \
  -w "\nHTTP Status: %{http_code}\n" \
  -o /tmp/gateway-response.json

echo ""
echo "📄 Response:"
cat /tmp/gateway-response.json | python3 -m json.tool 2>/dev/null || cat /tmp/gateway-response.json

echo ""
echo "✅ AI Gateway configuration attempted"
echo "⚠️  If this failed, you may need to configure it manually via the portal:"
echo "   https://ai.azure.com → Your Project → Settings → AI Gateway"
