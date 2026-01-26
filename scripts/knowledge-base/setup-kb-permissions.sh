#!/bin/bash
# Setup RBAC permissions for Knowledge Base ingestion pipeline
#
# This script configures the necessary permissions for Azure AI Search to:
# - Read documents from blob storage using managed identity
# - Use AI Foundry for embeddings via managed identity  
# - Use Content Understanding for document processing via managed identity
#
# IMPORTANT: Resource Region Configuration
# - Most resources (Search, Storage, Foundry) are in North Central US
# - Content Understanding (aldelar-csp-cu-westus) is in West US because the
#   Content Understanding API is only available in westus, swedencentral, australiaeast
#
# Prerequisites:
# - Azure CLI installed and logged in
# - azd environment variables available (run from project root after azd up)

set -e

echo "=========================================="
echo "Knowledge Base Permissions Setup"
echo "=========================================="

# Load environment variables from azd
# Only load simple key=value pairs without spaces or special characters
if [ -f ".azure/dev/.env" ]; then
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        # Skip lines with spaces in value (complex values)
        [[ "$value" =~ [[:space:]] ]] && continue
        # Remove quotes from value
        value="${value%\"}"
        value="${value#\"}"
        # Export if key is valid
        if [[ "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
            export "$key=$value"
        fi
    done < ".azure/dev/.env"
fi

# Configuration - these should match your deployment
RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-csp}"
SEARCH_SERVICE_NAME="${AZURE_SEARCH_SERVICE:-aldelar-csp-search}"
STORAGE_ACCOUNT_NAME="${AZURE_STORAGE_ACCOUNT:-aldelarcspstorage}"
FOUNDRY_ACCOUNT_NAME="${AZURE_AI_FOUNDRY:-aldelar-csp-foundry}"
# Note: Content Understanding is deployed in West US (separate from other resources in North Central US)
# because the Content Understanding API is only available in specific regions (westus, swedencentral, australiaeast)
CONTENT_UNDERSTANDING_NAME="${AZURE_CONTENT_UNDERSTANDING:-aldelar-csp-cu-westus}"
USER_ASSIGNED_IDENTITY_NAME="${AZURE_IDENTITY_NAME:-aldelar-csp-identity}"

echo ""
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Search Service: $SEARCH_SERVICE_NAME"
echo "  Storage Account: $STORAGE_ACCOUNT_NAME"
echo "  AI Foundry: $FOUNDRY_ACCOUNT_NAME"
echo "  Content Understanding: $CONTENT_UNDERSTANDING_NAME"
echo "  User-Assigned Identity: $USER_ASSIGNED_IDENTITY_NAME"
echo ""

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "Subscription ID: $SUBSCRIPTION_ID"

# Step 1: Get the Search service's system-assigned managed identity principal ID
echo ""
echo "Step 1: Getting Search service identity..."
SEARCH_IDENTITY=$(az search service show \
    --name "$SEARCH_SERVICE_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "identity.principalId" -o tsv)

if [ -z "$SEARCH_IDENTITY" ] || [ "$SEARCH_IDENTITY" == "null" ]; then
    echo "ERROR: Search service does not have a system-assigned managed identity enabled."
    echo "Please enable it in the Azure portal or via Bicep before running this script."
    exit 1
fi
echo "  Search Service Principal ID: $SEARCH_IDENTITY"

# Step 2: Get the user-assigned managed identity resource ID
echo ""
echo "Step 2: Getting user-assigned identity..."
USER_IDENTITY_ID=$(az identity show \
    --name "$USER_ASSIGNED_IDENTITY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "id" -o tsv 2>/dev/null || echo "")

if [ -z "$USER_IDENTITY_ID" ]; then
    echo "WARNING: User-assigned identity not found. Will proceed with system-assigned only."
else
    echo "  User-Assigned Identity ID: $USER_IDENTITY_ID"
    
    # Step 2b: Associate user-assigned identity with Search service
    echo ""
    echo "Step 2b: Associating user-assigned identity with Search service..."
    
    # Check if already associated
    CURRENT_IDENTITY_TYPE=$(az search service show \
        --name "$SEARCH_SERVICE_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "identity.type" -o tsv)
    
    if [[ "$CURRENT_IDENTITY_TYPE" != *"UserAssigned"* ]]; then
        echo "  Adding user-assigned identity to Search service..."
        az rest --method patch \
            --url "https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Search/searchServices/$SEARCH_SERVICE_NAME?api-version=2025-05-01" \
            --body "{\"identity\":{\"type\":\"SystemAssigned,UserAssigned\",\"userAssignedIdentities\":{\"$USER_IDENTITY_ID\":{}}}}" \
            --headers "Content-Type=application/json" > /dev/null
        echo "  ✓ User-assigned identity associated with Search service"
    else
        echo "  ✓ User-assigned identity already associated"
    fi
fi

# Step 3: Assign Storage Blob Data Reader to Search service on Storage Account
echo ""
echo "Step 3: Assigning Storage Blob Data Reader role..."
STORAGE_SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"

# Check if role already assigned
EXISTING_ROLE=$(az role assignment list \
    --assignee "$SEARCH_IDENTITY" \
    --role "Storage Blob Data Reader" \
    --scope "$STORAGE_SCOPE" \
    --query "[0].id" -o tsv 2>/dev/null || echo "")

if [ -z "$EXISTING_ROLE" ]; then
    az role assignment create \
        --assignee "$SEARCH_IDENTITY" \
        --role "Storage Blob Data Reader" \
        --scope "$STORAGE_SCOPE" > /dev/null
    echo "  ✓ Storage Blob Data Reader assigned to Search service on Storage Account"
else
    echo "  ✓ Storage Blob Data Reader already assigned"
fi

# Step 4: Assign Cognitive Services User to Search service on AI Foundry
echo ""
echo "Step 4: Assigning Cognitive Services User role on AI Foundry..."
FOUNDRY_SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$FOUNDRY_ACCOUNT_NAME"

EXISTING_ROLE=$(az role assignment list \
    --assignee "$SEARCH_IDENTITY" \
    --role "Cognitive Services User" \
    --scope "$FOUNDRY_SCOPE" \
    --query "[0].id" -o tsv 2>/dev/null || echo "")

if [ -z "$EXISTING_ROLE" ]; then
    az role assignment create \
        --assignee "$SEARCH_IDENTITY" \
        --role "Cognitive Services User" \
        --scope "$FOUNDRY_SCOPE" > /dev/null
    echo "  ✓ Cognitive Services User assigned to Search service on AI Foundry"
else
    echo "  ✓ Cognitive Services User already assigned on AI Foundry"
fi

# Step 5: Assign Cognitive Services User to Search service on Content Understanding
echo ""
echo "Step 5: Assigning Cognitive Services User role on Content Understanding..."
CU_SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.CognitiveServices/accounts/$CONTENT_UNDERSTANDING_NAME"

EXISTING_ROLE=$(az role assignment list \
    --assignee "$SEARCH_IDENTITY" \
    --role "Cognitive Services User" \
    --scope "$CU_SCOPE" \
    --query "[0].id" -o tsv 2>/dev/null || echo "")

if [ -z "$EXISTING_ROLE" ]; then
    az role assignment create \
        --assignee "$SEARCH_IDENTITY" \
        --role "Cognitive Services User" \
        --scope "$CU_SCOPE" > /dev/null
    echo "  ✓ Cognitive Services User assigned to Search service on Content Understanding"
else
    echo "  ✓ Cognitive Services User already assigned on Content Understanding"
fi

echo ""
echo "=========================================="
echo "Permission setup complete!"
echo "=========================================="
echo ""
echo "Summary of RBAC assignments for Search service ($SEARCH_IDENTITY):"
echo "  - Storage Blob Data Reader on $STORAGE_ACCOUNT_NAME"
echo "  - Cognitive Services User on $FOUNDRY_ACCOUNT_NAME"
echo "  - Cognitive Services User on $CONTENT_UNDERSTANDING_NAME"
echo ""
echo "Next steps:"
echo "  1. Run: python scripts/knowledge-base/upload-kb-documents.py"
echo "  2. Run: python scripts/knowledge-base/setup-knowledge-base.py"
echo "  3. Run: bash scripts/knowledge-base/run-kb-indexers.sh"
echo ""
echo "To run tests after indexing:"
echo "  bash scripts/knowledge-base/run-all-tests.sh"
echo ""
