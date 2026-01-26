"""
Configure AI Gateway for Azure AI Foundry Project

This script uses the Azure AI Foundry data plane API to programmatically
configure APIM as the AI Gateway for the Foundry project.
"""

import os
import sys
import requests
from azure.identity import AzureCliCredential

def get_env_value(key: str) -> str:
    """Get value from azd environment."""
    import subprocess
    result = subprocess.run(
        ['azd', 'env', 'get-value', key],
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return ""

def configure_ai_gateway():
    """Configure AI Gateway for the Foundry project."""
    print("🔧 Configuring AI Gateway for Foundry Project...")
    
    # Get configuration from environment
    foundry_endpoint = get_env_value("foundryEndpoint")
    project_name = get_env_value("foundryProjectName")
    apim_id = get_env_value("apiManagementId")
    
    if not all([foundry_endpoint, project_name, apim_id]):
        print("❌ Missing required environment variables")
        print(f"   foundryEndpoint: {foundry_endpoint}")
        print(f"   foundryProjectName: {project_name}")
        print(f"   apiManagementId: {apim_id}")
        sys.exit(1)
    
    print(f"   Foundry Endpoint: {foundry_endpoint}")
    print(f"   Project: {project_name}")
    print(f"   APIM ID: {apim_id}")
    
    # Get access token using Azure CLI credential
    print("\n🔑 Getting access token...")
    credential = AzureCliCredential()
    
    # Try different scopes that might work
    # The API error message told us it expects: https://ai.azure.com
    scopes_to_try = [
        "https://ai.azure.com/.default",
        "https://ml.azure.com/.default",
        "https://cognitiveservices.azure.com/.default",
        f"{foundry_endpoint}/.default"
    ]
    
    token = None
    for scope in scopes_to_try:
        try:
            token_obj = credential.get_token(scope)
            token = token_obj.token
            print(f"   ✓ Got token with scope: {scope}")
            break
        except Exception as e:
            print(f"   ⚠️  Failed to get token with scope {scope}: {e}")
            continue
    
    if not token:
        print("❌ Could not obtain access token")
        sys.exit(1)
    
    # Try different API endpoints that might work
    # Based on the Foundry services endpoint pattern
    foundry_services_endpoint = foundry_endpoint.replace('.cognitiveservices.azure.com', '.services.ai.azure.com')
    
    # API versions to try - start with the one used in our Bicep files
    api_versions = ["2025-10-01-preview", "2024-10-01", "2024-12-01-preview", "2024-09-01-preview"]
    
    api_endpoints = []
    for api_version in api_versions:
        api_endpoints.extend([
            f"{foundry_services_endpoint}/api/projects/{project_name}/settings/aiGateway?api-version={api_version}",
            f"{foundry_services_endpoint}/api/projects/{project_name}/aiGateway?api-version={api_version}",
        ])
    
    # Also try without services endpoint
    for api_version in api_versions:
        api_endpoints.append(f"{foundry_endpoint}/api/projects/{project_name}/aiGateway?api-version={api_version}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    gateway_config = {
        "apimResourceId": apim_id,
        "enabled": True
    }
    
    print("\n📡 Attempting to configure AI Gateway...")
    
    for endpoint in api_endpoints:
        print(f"\n   Trying: {endpoint}")
        try:
            response = requests.put(
                endpoint,
                headers=headers,
                json=gateway_config,
                timeout=30
            )
            
            print(f"   HTTP Status: {response.status_code}")
            
            if response.status_code in [200, 201, 204]:
                print("   ✅ Successfully configured AI Gateway!")
                if response.text:
                    print(f"   Response: {response.text}")
                return True
            else:
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    print("\n⚠️  All attempts failed.")
    print("\n💡 Manual configuration required:")
    print("   1. Go to https://ai.azure.com")
    print("   2. Navigate to your project → Settings → AI Gateway")
    print("   3. Select your APIM instance")
    print("   4. Save the configuration")
    
    return False

if __name__ == "__main__":
    configure_ai_gateway()
