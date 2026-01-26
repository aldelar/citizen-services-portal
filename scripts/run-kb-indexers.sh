#!/bin/bash
# Run all knowledge base indexers via REST API

SEARCH_SERVICE="aldelar-csp-search"
SEARCH_ENDPOINT="https://${SEARCH_SERVICE}.search.windows.net"
API_VERSION="2025-11-01-Preview"

echo "Running knowledge base indexers..."

# Get access token for Azure Search
TOKEN=$(az account get-access-token --resource https://search.azure.com --query accessToken -o tsv)

if [ -z "$TOKEN" ]; then
    echo "ERROR: Failed to get access token. Make sure you're logged in with 'az login'"
    exit 1
fi

for AGENCY in ladbs ladwp lasan; do
    INDEXER_NAME="${AGENCY}-indexer"
    echo "Running ${INDEXER_NAME}..."
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        "${SEARCH_ENDPOINT}/indexers/${INDEXER_NAME}/run?api-version=${API_VERSION}" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -H "Content-Length: 0")
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | head -n -1)
    
    if [ "$HTTP_CODE" == "202" ] || [ "$HTTP_CODE" == "204" ]; then
        echo "  ✓ ${INDEXER_NAME} started successfully"
    else
        echo "  ✗ ${INDEXER_NAME} failed with status ${HTTP_CODE}"
        echo "    Response: ${BODY}"
    fi
done

echo ""
echo "Indexers are running. Check status with:"
echo "  curl -H \"Authorization: Bearer \$TOKEN\" \"${SEARCH_ENDPOINT}/indexers/<indexer-name>/status?api-version=${API_VERSION}\""
