#!/usr/bin/env python3
"""Test script to verify regular (keyword) search works on all knowledge base indexes."""

import subprocess
import sys
import requests

# Configuration
SEARCH_ENDPOINT = "https://aldelar-csp-search.search.windows.net"
API_VERSION = "2025-11-01-Preview"

# Test queries for each agency
TEST_QUERIES = {
    "ladbs-kb": [
        ("building permit", 2),
        ("electrical inspection", 2),
        ("plan check", 2),
    ],
    "ladwp-kb": [
        ("solar panel", 2),
        ("interconnection", 2),
        ("electric rates", 2),
    ],
    "lasan-kb": [
        ("hazardous waste", 2),
        ("recycling", 2),
        ("trash pickup", 2),
    ],
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


def test_regular_search():
    """Test regular keyword search on all indexes."""
    print("=" * 60)
    print("Knowledge Base Regular Search Test")
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
    
    for index_name, queries in TEST_QUERIES.items():
        agency = index_name.replace("-kb", "").upper()
        print(f"Testing {agency} index ({index_name})...")
        
        for query_text, min_results in queries:
            url = f"{SEARCH_ENDPOINT}/indexes/{index_name}/docs/search?api-version={API_VERSION}"
            body = {
                "search": query_text,
                "queryType": "simple",
                "top": 5,
                "select": "title,chunk"
            }
            
            try:
                resp = requests.post(url, headers=headers, json=body, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                
                results = data.get("value", [])
                result_count = len(results)
                
                if result_count >= min_results:
                    top_title = results[0].get("title", "N/A") if results else "N/A"
                    print(f"  ✓ \"{query_text}\" → {result_count} results (top: {top_title})")
                else:
                    print(f"  ✗ \"{query_text}\" → {result_count} results (expected >= {min_results})")
                    all_passed = False
                    
            except requests.RequestException as e:
                print(f"  ✗ \"{query_text}\" → ERROR: {e}")
                all_passed = False
        
        print()
    
    print("=" * 60)
    if all_passed:
        print("✓ All regular search tests PASSED")
        sys.exit(0)
    else:
        print("✗ Some regular search tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    test_regular_search()
