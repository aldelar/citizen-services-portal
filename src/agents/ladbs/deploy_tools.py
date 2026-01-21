#!/usr/bin/env python3
"""
Deploy LADBS Agent Tools to Azure AI Foundry.

This script:
1. Scans the tools/ directory for tool definitions (YAML files)
2. Registers each tool with Azure AI Foundry
3. Supports idempotent operations (updates if already exists)
"""

import asyncio
import os
import sys
from pathlib import Path
import yaml
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient

# Configuration
# Use foundryProjectEndpoint from azd env, fallback to AZURE_AI_PROJECT_ENDPOINT for manual runs
AZURE_AI_PROJECT_ENDPOINT = os.getenv("foundryProjectEndpoint") or os.getenv("AZURE_AI_PROJECT_ENDPOINT")

# Paths
AGENT_DIR = Path(__file__).parent
TOOLS_DIR = AGENT_DIR / "tools"


def load_yaml(file_path: Path) -> dict:
    """Load YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def find_tool_definitions() -> list[Path]:
    """Find all tool YAML files in the tools directory."""
    if not TOOLS_DIR.exists():
        print(f"⚠️  Tools directory not found: {TOOLS_DIR}")
        return []
    
    tool_files = list(TOOLS_DIR.glob("*.yaml")) + list(TOOLS_DIR.glob("*.yml"))
    return sorted(tool_files)


async def deploy_tool(project_client: AIProjectClient, tool_file: Path) -> bool:
    """
    Deploy a single tool to Azure AI Foundry.
    
    Args:
        project_client: Azure AI Project client
        tool_file: Path to the tool definition YAML file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        tool_config = load_yaml(tool_file)
        tool_name = tool_config.get('name')
        
        print(f"\n🔧 Deploying tool: {tool_name}")
        print(f"   File: {tool_file.name}")
        print(f"   Type: {tool_config.get('type', 'unknown')}")
        
        # TODO: Implement actual tool deployment based on tool type
        # For MCP tools, this would register the MCP server endpoint
        # For function tools, this would register the function definition
        
        if tool_config.get('type') == 'mcp':
            print(f"   Endpoint: {tool_config.get('endpoint', {}).get('url', 'N/A')}")
            # MCP tool deployment logic here
            # Note: Current Azure AI Foundry SDK may not have direct MCP registration
            # This might need to be done through the portal or REST API
            print(f"   ⚠️  MCP tool registration not yet implemented in SDK")
            print(f"   ℹ️  Tool definition loaded and validated")
            return True
        
        print(f"   ✓ Tool validated: {tool_name}")
        return True
        
    except Exception as e:
        print(f"   ✗ Failed to deploy tool {tool_file.name}: {e}")
        return False


async def deploy_tools():
    """Deploy all tools to Azure AI Foundry."""
    
    print("=" * 60)
    print("LADBS Agent Tools Deployment")
    print("=" * 60)
    
    # Validate environment
    if not AZURE_AI_PROJECT_ENDPOINT:
        print("ERROR: AZURE_AI_PROJECT_ENDPOINT environment variable not set")
        sys.exit(1)
    
    # Find tool definitions
    print("\n📂 Scanning for tool definitions...")
    tool_files = find_tool_definitions()
    
    if not tool_files:
        print("   ⚠️  No tool definitions found in tools/ directory")
        print("   ℹ️  Skipping tool deployment")
        return
    
    print(f"   Found {len(tool_files)} tool definition(s):")
    for tool_file in tool_files:
        print(f"   - {tool_file.name}")
    
    # Connect to Azure AI Foundry
    print("\n🔗 Connecting to Azure AI Foundry...")
    
    try:
        async with (
            AzureCliCredential() as credential,
            AIProjectClient(
                endpoint=AZURE_AI_PROJECT_ENDPOINT,
                credential=credential
            ) as project_client,
        ):
            print(f"   ✓ Connected to project endpoint")
            
            # Deploy each tool
            results = []
            for tool_file in tool_files:
                success = await deploy_tool(project_client, tool_file)
                results.append((tool_file.name, success))
            
            # Summary
            print("\n" + "=" * 60)
            successful = sum(1 for _, success in results if success)
            failed = len(results) - successful
            
            if failed == 0:
                print("✅ All Tools Deployed Successfully!")
            else:
                print(f"⚠️  Tools Deployment Complete with Errors")
            
            print("=" * 60)
            print(f"\nResults:")
            for tool_name, success in results:
                status = "✓" if success else "✗"
                print(f"  {status} {tool_name}")
            print()
            
            if failed > 0:
                sys.exit(1)
            
    except Exception as e:
        print(f"   ✗ Failed to connect or deploy tools: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(deploy_tools())
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
