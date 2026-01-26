#!/bin/bash
# Run all knowledge base indexers

SEARCH_SERVICE="aldelar-csp-search"
RESOURCE_GROUP="csp"

echo "Running knowledge base indexers..."

for AGENCY in ladbs ladwp lasan; do
    echo "Running ${AGENCY}-indexer..."
    az search indexer run \
        --name "${AGENCY}-indexer" \
        --service-name "$SEARCH_SERVICE" \
        --resource-group "$RESOURCE_GROUP"
done

echo "Done. Check indexer status with:"
echo "  az search indexer status --name <indexer-name> --service-name $SEARCH_SERVICE --resource-group $RESOURCE_GROUP"
