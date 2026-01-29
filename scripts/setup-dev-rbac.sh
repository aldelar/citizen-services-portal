#!/bin/bash
#
# Setup CosmosDB RBAC roles for local development
#
# This script grants the current user (or specified principal) the necessary
# CosmosDB data plane permissions for local development.
#
# Usage:
#   ./setup-dev-rbac.sh                    # Uses current signed-in user
#   ./setup-dev-rbac.sh <principal-id>     # Uses specified principal ID
#
# Note: These are CosmosDB data plane roles, not ARM RBAC roles.
# They use built-in role definition IDs specific to CosmosDB.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🔐 CosmosDB RBAC Setup for Local Development${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root for azd commands
cd "$PROJECT_ROOT"

# Get principal ID (from argument or current user)
if [ -n "$1" ]; then
    PRINCIPAL_ID="$1"
    echo -e "${YELLOW}Using provided principal ID: ${PRINCIPAL_ID}${NC}"
else
    echo "Getting current user's principal ID..."
    PRINCIPAL_ID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null)
    if [ -z "$PRINCIPAL_ID" ]; then
        echo -e "${RED}❌ Error: Could not get current user's principal ID.${NC}"
        echo "   Make sure you're logged in with: az login"
        exit 1
    fi
    echo -e "${GREEN}✅ Found principal ID: ${PRINCIPAL_ID}${NC}"
fi

# Get CosmosDB account name from azd environment
echo ""
echo "Getting CosmosDB account from azd environment..."
COSMOS_ACCOUNT=$(azd env get-value cosmosDbAccountName 2>/dev/null)
if [ -z "$COSMOS_ACCOUNT" ]; then
    echo -e "${RED}❌ Error: Could not get cosmosDbAccountName from azd environment.${NC}"
    echo "   Make sure you've run 'azd provision' first."
    exit 1
fi
echo -e "${GREEN}✅ CosmosDB Account: ${COSMOS_ACCOUNT}${NC}"

# Get resource group from azd environment
RESOURCE_GROUP=$(azd env get-value resourceGroupName 2>/dev/null)
if [ -z "$RESOURCE_GROUP" ]; then
    echo -e "${RED}❌ Error: Could not get resourceGroupName from azd environment.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Resource Group: ${RESOURCE_GROUP}${NC}"

# CosmosDB built-in role definition IDs
# See: https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-setup-rbac
COSMOS_DATA_READER="00000000-0000-0000-0000-000000000001"
COSMOS_DATA_CONTRIBUTOR="00000000-0000-0000-0000-000000000002"

# Database scope (all databases in the account)
SCOPE="/dbs/csp"

echo ""
echo -e "${BLUE}Assigning CosmosDB data plane roles...${NC}"
echo ""

# Function to assign role with error handling
assign_role() {
    local role_id="$1"
    local role_name="$2"
    
    echo "  Assigning ${role_name}..."
    
    # Check if role assignment already exists
    existing=$(az cosmosdb sql role assignment list \
        --account-name "$COSMOS_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --query "[?principalId=='${PRINCIPAL_ID}' && roleDefinitionId contains '${role_id}']" \
        -o tsv 2>/dev/null || echo "")
    
    if [ -n "$existing" ]; then
        echo -e "  ${YELLOW}⏭️  ${role_name} already assigned${NC}"
        return 0
    fi
    
    # Create the role assignment
    az cosmosdb sql role assignment create \
        --account-name "$COSMOS_ACCOUNT" \
        --resource-group "$RESOURCE_GROUP" \
        --scope "$SCOPE" \
        --principal-id "$PRINCIPAL_ID" \
        --role-definition-id "$role_id" \
        --output none 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ ${role_name} assigned${NC}"
    else
        echo -e "  ${RED}❌ Failed to assign ${role_name}${NC}"
        return 1
    fi
}

# Assign both roles
assign_role "$COSMOS_DATA_CONTRIBUTOR" "Cosmos DB Built-in Data Contributor"
assign_role "$COSMOS_DATA_READER" "Cosmos DB Built-in Data Reader"

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}✅ CosmosDB RBAC setup complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "${YELLOW}⚠️  Note: RBAC role propagation can take up to 10 minutes.${NC}"
echo "   If you get 'Forbidden' errors, wait a bit and try again."
echo ""
