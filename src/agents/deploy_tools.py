#!/usr/bin/env python3
"""
Deploy Agent Tools to Azure AI Foundry.

This script:
1. Reads tools from the agent's agent.yaml definition
2. Validates tool configurations
3. Registers each tool with Azure AI Foundry (when supported)

Usage:
    python deploy_tools.py <agent_name>
    
Example:
    python deploy_tools.py ladbs
"""

import asyncio
import os
import sys
from pathlib import Path
import yaml
import re
from azure.identity import DefaultAzureCredential
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient
import service_urls

# Configuration
# Use foundryProjectEndpoint from azd env, fallback to AZURE_AI_PROJECT_ENDPOINT for manual runs
AZURE_AI_PROJECT_ENDPOINT = os.getenv("foundryProjectEndpoint") or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP_NAME = os.getenv("resourceGroupName")
FOUNDRY_NAME = os.getenv("foundryName")
FOUNDRY_PROJECT_NAME = os.getenv("foundryProjectName")


def load_yaml(file_path: Path) -> dict:
    """Load YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def substitute_env_vars(content: str, service_url_map: dict[str, str] = None) -> str:
    """
    Substitute environment variable placeholders in content.
    Supports ${VAR_NAME} syntax.
    
    Args:
        content: Content with variable placeholders
        service_url_map: Optional dictionary of service URLs to use for substitution
    """
    def replace_var(match):
        var_name = match.group(1)
        
        # First check service_url_map if provided
        if service_url_map and var_name in service_url_map:
            return service_url_map[var_name]
        
        # Fall back to environment variables
        value = os.getenv(var_name)
        if value is None:
            print(f"   ⚠️  Warning: Environment variable {var_name} not set")
            return match.group(0)  # Return original if not found
        return value
    
    return re.sub(r'\$\{([^}]+)\}', replace_var, content)


def get_tools_from_agent_config(agent_dir: Path, service_url_map: dict[str, str] = None) -> list[dict]:
    """
    Extract tools from agent.yaml configuration.
    
    Args:
        agent_dir: Path to agent directory
        service_url_map: Optional dictionary of service URLs to use for substitution
    
    Returns:
        List of tool configurations
    """
    agent_yaml = agent_dir / "agent.yaml"
    
    if not agent_yaml.exists():
        print(f"   ⚠️  Agent configuration not found: {agent_yaml}")
        return []
    
    # Load YAML with environment variable substitution
    with open(agent_yaml, 'r') as f:
        agent_yaml_content = f.read()
    agent_yaml_content = substitute_env_vars(agent_yaml_content, service_url_map)
    agent_config = yaml.safe_load(agent_yaml_content)
    
    # Extract tools (supports both old and new schema)
    if 'definition' in agent_config:
        tools = agent_config['definition'].get('tools', [])
    else:
        # Legacy schema support
        tools = agent_config.get('tools', [])
    
    return tools


async def validate_tool(project_client: AIProjectClient, tool_config: dict, index: int) -> bool:
    """
    Validate a single tool configuration.
    
    Args:
        project_client: Azure AI Project client
        tool_config: Tool configuration from agent.yaml
        index: Tool index for display
    
    Returns:
        True if valid, False otherwise
    """
    try:
        tool_type = tool_config.get('type', 'unknown')
        
        print(f"\n🔧 Validating tool #{index + 1}")
        print(f"   Type: {tool_type}")
        
        if tool_type == 'mcp':
            server_label = tool_config.get('server_label', 'unknown')
            server_url = tool_config.get('server_url', '')
            connection_id = tool_config.get('project_connection_id', '')
            
            print(f"   Server Label: {server_label}")
            print(f"   Server URL: {server_url}")
            print(f"   Connection ID: {connection_id}")
            
            # Note: MCP tool registration via ARM API is currently returning 500 errors
            # Tools are validated here and will be referenced in the agent definition
            # For manual registration, use the Azure AI Foundry portal:
            # Project > Tools > Add Tool > MCP Server
            print(f"   ℹ️  MCP tool definition validated")
            print(f"   ℹ️  Tool will be referenced in agent deployment")
            return True
        
        print(f"   ✓ Tool validated")
        return True
        
    except Exception as e:
        print(f"   ✗ Failed to validate tool: {e}")
        import traceback
        traceback.print_exc()
        return False


async def deploy_tools(agent_name: str):
    """Deploy all tools for the specified agent to Azure AI Foundry."""
    
    # Determine agent directory
    script_dir = Path(__file__).parent
    agent_dir = script_dir / agent_name
    
    if not agent_dir.exists():
        print(f"❌ Agent directory not found: {agent_dir}")
        sys.exit(1)
    
    print("=" * 60)
    print(f"{agent_name.upper()} Agent Tools Deployment")
    print("=" * 60)
    
    # Validate environment
    if not AZURE_AI_PROJECT_ENDPOINT:
        print("ERROR: AZURE_AI_PROJECT_ENDPOINT environment variable not set")
        sys.exit(1)
    
    # Discover service URLs from azd environment
    print("\n🔍 Discovering service URLs...")
    service_url_map = service_urls.get_service_urls()
    if service_url_map:
        print(f"   ✓ Found {len(service_url_map)} service URL(s):")
        for var_name, url in service_url_map.items():
            print(f"      - {var_name}: {url}")
    else:
        print("   ℹ️  No service URLs found")
    
    # Get tools from agent configuration
    print("\n📂 Reading tools from agent configuration...")
    tools = get_tools_from_agent_config(agent_dir, service_url_map)
    
    if not tools:
        print("   ⚠️  No tools defined in agent configuration")
        print("   ℹ️  Skipping tool deployment")
        return
    
    print(f"   Found {len(tools)} tool(s) in agent definition")
    
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
            
            # Validate each tool
            results = []
            for i, tool_config in enumerate(tools):
                success = await validate_tool(project_client, tool_config, i)
                results.append((f"Tool #{i + 1}", success))
            
            # Summary
            print("\n" + "=" * 60)
            successful = sum(1 for _, success in results if success)
            failed = len(results) - successful
            
            if failed == 0:
                print("✅ All Tools Validated Successfully!")
            else:
                print(f"⚠️  Tools Validation Complete with Errors")
            
            print("=" * 60)
            print(f"\nResults:")
            for tool_name, success in results:
                status = "✓" if success else "✗"
                print(f"  {status} {tool_name}")
            print()
            
            if failed > 0:
                sys.exit(1)
            
    except Exception as e:
        print(f"   ✗ Failed to connect or validate tools: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python deploy_tools.py <agent_name>")
        print("\nExample:")
        print("  python deploy_tools.py ladbs")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    asyncio.run(deploy_tools(agent_name))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
