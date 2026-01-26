"""
Configure AI Gateway for Azure AI Foundry Project using ARM Management API

This attempts to configure APIM as the AI Gateway via the management plane.
"""

import os
import sys
import requests
import subprocess
from azure.identity import AzureCliCredential

def get_env_value(key: str) -> str:
    """Get value from azd environment."""
    result = subprocess.run(
        ['azd', 'env', 'get-value', key],
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return ""

def configure_ai_gateway_arm():
    """Configure AI Gateway using ARM management API."""
    print("🔧 Configuring AI Gateway via ARM Management API...")
    
    # Get configuration
    subscription_id = subprocess.run(['az', 'account', 'show', '--query', 'id', '-o', 'tsv'],
                                    capture_output=True, text=True).stdout.strip()
    resource_group = get_env_value("resourceGroupName") or "csp"
    foundry_name = get_env_value("foundryName")
    project_name = get_env_value("foundryProjectName")
    apim_id = get_env_value("apiManagementId")
    
    print(f"   Subscription: {subscription_id}")
    print(f"   Resource Group: {resource_group}")
    print(f"   Foundry: {foundry_name}")
    print(f"   Project: {project_name}")
    print(f"   APIM ID: {apim_id}")
    
    # Get management token
    print("\n🔑 Getting ARM management token...")
    credential = AzureCliCredential()
    token = credential.get_token("https://management.azure.com/.default").token
    print("   ✓ Got token")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try PATCH/PUT on the project resource with gateway configuration
    api_version = "2025-10-01-preview"
    
    project_url = (
        f"https://management.azure.com/subscriptions/{subscription_id}"
        f"/resourceGroups/{resource_group}"
        f"/providers/Microsoft.CognitiveServices/accounts/{foundry_name}"
        f"/projects/{project_name}"
        f"?api-version={api_version}"
    )
    
    # Try adding gateway configuration to project properties
    project_config = {
        "properties": {
            "aiGateway": {
                "apimResourceId": apim_id,
                "enabled": True
            }
        }
    }
    
    print(f"\n📡 Attempting PATCH to project resource...")
    print(f"   URL: {project_url}")
    
    try:
        response = requests.patch(
            project_url,
            headers=headers,
            json=project_config,
            timeout=30
        )
        
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
        if response.status_code in [200, 201, 202]:
            print("\n   ✅ Successfully configured AI Gateway!")
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n⚠️  ARM API approach failed.")
    print("\n💡 The AI Gateway configuration is likely a portal-only feature at this time.")
    print("   Manual configuration required via https://ai.azure.com")
    
    return False

if __name__ == "__main__":
    configure_ai_gateway_arm()
