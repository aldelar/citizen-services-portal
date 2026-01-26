#!/usr/bin/env python3
"""Test script to verify semantic search works on all knowledge base indexes."""

import subprocess
import sys
import requests

# Configuration
SEARCH_ENDPOINT = "https://aldelar-csp-search.search.windows.net"
API_VERSION = "2025-11-01-Preview"

# Natural language test queries for each agency
# Format: (query, semantic_config, min_results, expected_keywords_in_results)
TEST_QUERIES = {
    "ladbs-kb": [
        ("How do I apply for a building permit?", "ladbs-semantic-config", 2, ["permit", "building"]),
        ("What are the steps for plan check?", "ladbs-semantic-config", 2, ["plan"]),
        ("How do I schedule an inspection?", "ladbs-semantic-config", 2, ["inspection"]),
    ],
    "ladwp-kb": [
        ("What are the requirements for solar panel interconnection?", "ladwp-semantic-config", 2, ["solar", "interconnection"]),
        ("How do I understand my electric bill?", "ladwp-semantic-config", 2, ["rate", "electric"]),
        ("What rebates are available for energy efficiency?", "ladwp-semantic-config", 2, ["rebate"]),
    ],
    "lasan-kb": [
        ("Where can I dispose of hazardous waste?", "lasan-semantic-config", 2, ["hazardous", "waste"]),
        ("How do I recycle electronics?", "lasan-semantic-config", 1, ["waste", "recycle"]),
        ("What are the trash pickup schedules?", "lasan-semantic-config", 1, ["trash", "pickup"]),
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


def test_semantic_search():
    """Test semantic search on all indexes."""
    print("=" * 60)
    print("Knowledge Base Semantic Search Test")
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
        
        for query_text, semantic_config, min_results, expected_keywords in queries:
            url = f"{SEARCH_ENDPOINT}/indexes/{index_name}/docs/search?api-version={API_VERSION}"
            body = {
                "search": query_text,
                "queryType": "semantic",
                "semanticConfiguration": semantic_config,
                "top": 5,
                "select": "title,chunk"
            }
            
            try:
                resp = requests.post(url, headers=headers, json=body, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                
                results = data.get("value", [])
                result_count = len(results)
                
                # Check if results contain expected keywords
                has_relevant_content = False
                if results:
                    combined_text = " ".join([
                        r.get("title", "") + " " + r.get("chunk", "")
                        for r in results
                    ]).lower()
                    has_relevant_content = any(
                        kw.lower() in combined_text for kw in expected_keywords
                    )
                
                if result_count >= min_results and has_relevant_content:
                    top_title = results[0].get("title", "N/A") if results else "N/A"
                    print(f"  ✓ \"{query_text[:40]}...\"")
                    print(f"      → {result_count} results (top: {top_title})")
                elif result_count >= min_results:
                    print(f"  ⚠ \"{query_text[:40]}...\"")
                    print(f"      → {result_count} results but relevance unclear")
                else:
                    print(f"  ✗ \"{query_text[:40]}...\"")
                    print(f"      → {result_count} results (expected >= {min_results})")
                    all_passed = False
                    
            except requests.RequestException as e:
                print(f"  ✗ \"{query_text[:40]}...\" → ERROR: {e}")
                all_passed = False
        
        print()
    
    print("=" * 60)
    if all_passed:
        print("✓ All semantic search tests PASSED")
        sys.exit(0)
    else:
        print("✗ Some semantic search tests FAILED")
        sys.exit(1)


if __name__ == "__main__":
    test_semantic_search()
