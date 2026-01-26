#!/usr/bin/env python3
"""Test script to verify document counts in all knowledge base indexes."""

import subprocess
import sys
import requests

# Configuration
SEARCH_ENDPOINT = "https://aldelar-csp-search.search.windows.net"
API_VERSION = "2025-11-01-Preview"

EXPECTED_COUNTS = {
    "ladbs-kb": {"source_files": 15, "min_chunks": 50},
    "ladwp-kb": {"source_files": 9, "min_chunks": 100},
    "lasan-kb": {"source_files": 6, "min_chunks": 10},
}


def get_query_key() -> str:
    """Get the search query key."""
    result = subprocess.run(
        [
            "az", "search", "query-key", "list",
            "--service-name", "aldelar-csp-search",
            "--resource-group", "csp",
            "--query", "[0].key",
            "-o", "tsv"
        ],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def test_document_counts():
    """Test document counts in all indexes."""
    print("=" * 60)
    print("Knowledge Base Document Count Test")
    print("=" * 60)
    print()
    
    try:
        query_key = get_query_key()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to get query key: {e}")
        print("Make sure you're logged in with 'az login'")
        sys.exit(1)
    
    headers = {"api-key": query_key, "Content-Type": "application/json"}
    all_passed = True
    
    for index_name, expected in EXPECTED_COUNTS.items():
        agency = index_name.replace("-kb", "").upper()
        print(f"Testing {agency} index ({index_name})...")
        
        url = f"{SEARCH_ENDPOINT}/indexes/{index_name}/docs/search?api-version={API_VERSION}"
        body = {"search": "*", "count": True, "top": 0}
        
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            chunk_count = data.get("@odata.count", 0)
            min_expected = expected["min_chunks"]
            
            if chunk_count >= min_expected:
                print(f"  ✓ {chunk_count} document chunks (expected >= {min_expected})")
            else:
                print(f"  ✗ {chunk_count} document chunks (expected >= {min_expected})")
                all_passed = False
                
        except requests.RequestException as e:
            print(f"  ✗ ERROR: {e}")
            all_passed = False
        
        print()
    
    print("=" * 60)
    if all_passed:
        print("✓ All document count tests PASSED")
        sys.exit(0)
    else:
        print("✗ Some document count tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    test_document_counts()
