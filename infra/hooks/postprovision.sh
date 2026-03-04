#!/bin/bash
# ---------------------------------------------------------------------------
# postprovision.sh – Post-provision configuration for AI Gateway + CosmosDB
#
# AI Gateway linking to Foundry is currently PORTAL-ONLY (no ARM/CLI API).
# This script outputs the manual steps required after provision.
# ---------------------------------------------------------------------------
set -euo pipefail

FOUNDRY_NAME="${foundryName:-unknown}"
PROJECT_NAME="${foundryProjectName:-unknown}"
GATEWAY_NAME="${aiGatewayName:-unknown}"

echo "=============================================="
echo "  AI Gateway Manual Configuration Required"
echo "=============================================="
echo ""
echo "The AI Gateway APIM '${GATEWAY_NAME}' (BasicV2) is deployed."
echo "Link it to Foundry via the portal (no ARM/CLI API available):"
echo ""
echo "  1. Go to https://ai.azure.com"
echo "  2. Enable 'New Foundry' toggle"
echo "  3. Operate > Admin console > AI Gateway tab"
echo "  4. Click 'Add AI Gateway'"
echo "  5. Select Foundry resource: ${FOUNDRY_NAME}"
echo "  6. Choose 'Use existing' > select: ${GATEWAY_NAME}"
echo "  7. Name the gateway and click 'Add'"
echo "  8. After status shows 'Enabled', click the gateway name"
echo "  9. Add project '${PROJECT_NAME}' to the gateway"
echo ""
echo "=============================================="
