#!/usr/bin/env python3
"""
Test Easy Auth configuration for MCP Server.

This script tests whether the Easy Auth configuration on the Container App
correctly accepts tokens for the MCP server.

Usage:
    cd src/agents && uv run python test_easy_auth.py
"""

import sys

def main():
    from azure.identity import InteractiveBrowserCredential, AzureCliCredential
    import requests
    
    # Configuration
    APP_ID = "f62275c4-1c17-45dc-a662-85c49f3cbce1"
    MCP_URI = "https://aldelar-csp-mcp-ladbs.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io"
    
    print("=" * 60)
    print("MCP Server Easy Auth Test")
    print("=" * 60)
    print()
    print(f"App ID: {APP_ID}")
    print(f"MCP URI: {MCP_URI}")
    print()
    
    # Test 1: Without auth
    print("Test 1: Request without auth (should get 401)...")
    try:
        resp = requests.get(f"{MCP_URI}/mcp", timeout=10)
        if resp.status_code == 401:
            print(f"   ✅ Got 401 as expected - Easy Auth is enabled")
        else:
            print(f"   ⚠️ Got {resp.status_code} - Easy Auth may not be enabled")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    print()
    
    # Test 2: Get token
    print("Test 2: Getting token...")
    print(f"   Requesting token with scope: api://{APP_ID}/.default")
    
    token = None
    
    # Try AzureCliCredential first
    try:
        print("   Trying Azure CLI credential...")
        cred = AzureCliCredential()
        token = cred.get_token(f"api://{APP_ID}/.default").token
        print("   ✅ Token obtained via Azure CLI")
    except Exception as e:
        print(f"   ⚠️ Azure CLI failed: {str(e)[:80]}...")
        
        # Fall back to interactive browser
        try:
            print("   Trying Interactive Browser credential...")
            print("   (A browser window will open)")
            cred = InteractiveBrowserCredential()
            token = cred.get_token(f"api://{APP_ID}/.default").token
            print("   ✅ Token obtained via browser")
        except Exception as e2:
            print(f"   ❌ Browser auth failed: {e2}")
            return
    
    print(f"   Token length: {len(token)} chars")
    print()
    
    # Decode and show token claims
    print("Test 3: Token claims...")
    try:
        import base64
        import json
        parts = token.split(".")
        if len(parts) >= 2:
            # Add padding
            payload = parts[1]
            payload += "=" * (4 - len(payload) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload))
            print(f"   aud (audience): {claims.get('aud', 'N/A')}")
            print(f"   iss (issuer): {claims.get('iss', 'N/A')}")
            print(f"   sub (subject): {claims.get('sub', 'N/A')[:20]}...")
            print(f"   appid: {claims.get('appid', claims.get('azp', 'N/A'))}")
    except Exception as e:
        print(f"   ⚠️ Could not decode token: {e}")
    print()
    
    # Test 4: Call with token
    print("Test 4: Request with auth token...")
    try:
        resp = requests.get(
            f"{MCP_URI}/mcp", 
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        print(f"   HTTP Status: {resp.status_code}")
        
        if resp.status_code == 200:
            print("   ✅ SUCCESS! Easy Auth accepted the token")
            print(f"   Response: {resp.text[:200]}...")
        elif resp.status_code == 405:
            print("   ✅ SUCCESS! Easy Auth accepted the token (405 = Method Not Allowed is OK for GET)")
        elif resp.status_code == 406:
            print("   ✅ SUCCESS! Easy Auth accepted the token (406 = Not Acceptable is OK)")
        elif resp.status_code == 401:
            print("   ❌ FAILED! 401 Unauthorized - Token was rejected")
            print("   Possible causes:")
            print("      1. Token audience doesn't match allowedAudiences")
            print("      2. Token issuer doesn't match openIdIssuer")
            print("      3. Token is expired")
            print(f"   Response: {resp.text[:200]}")
        elif resp.status_code == 403:
            print("   ⚠️ 403 Forbidden - Token accepted but authorization failed")
            print(f"   Response: {resp.text[:200]}")
        else:
            print(f"   ⚠️ Unexpected status: {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
