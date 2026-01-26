#!/bin/bash
# Run all knowledge base tests
#
# This script runs all test scripts to verify the knowledge base is working correctly:
# 1. Document counts - verifies indexes have expected number of chunks
# 2. Regular search - verifies keyword search works
# 3. Semantic search - verifies semantic/natural language search works

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================"
echo "Running Knowledge Base Tests"
echo "========================================"
echo ""

# Check if Python environment is active
if ! python3 -c "import requests" 2>/dev/null; then
    echo "ERROR: 'requests' package not found. Please activate the Python environment:"
    echo "  cd scripts && source .venv/bin/activate"
    exit 1
fi

echo "Test 1/3: Document Counts"
echo "----------------------------------------"
python3 "${SCRIPT_DIR}/test-document-counts.py"
echo ""

echo "Test 2/3: Regular Search"
echo "----------------------------------------"
python3 "${SCRIPT_DIR}/test-regular-search.py"
echo ""

echo "Test 3/3: Semantic Search"
echo "----------------------------------------"
python3 "${SCRIPT_DIR}/test-semantic-search.py"
echo ""

echo "========================================"
echo "All Knowledge Base Tests Complete!"
echo "========================================"
