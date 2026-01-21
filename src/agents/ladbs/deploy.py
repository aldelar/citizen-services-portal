#!/usr/bin/env python3
"""
Deploy LADBS AI Agent to Azure AI Foundry.

This script uses the Azure AI Foundry SDK to:
1. Connect to the Foundry project
2. Register the MCP-LADBS tool
3. Deploy the LADBS assistant agent
"""

import os
import sys
from pathlib import Path
import yaml
import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Agent, AgentTool, ConnectionProperties

# Configuration
RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "csp")
PROJECT_NAME = os.getenv("FOUNDRY_PROJECT_NAME", "citizen-services-portal")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")

# Paths
AGENT_DIR = Path(__file__).parent
AGENT_YAML = AGENT_DIR / "agent.yaml"
SYSTEM_PROMPT = AGENT_DIR / "system-prompt.md"
MCP_TOOL_YAML = AGENT_DIR / "tools" / "mcp-ladbs.yaml"


def load_yaml(file_path: Path) -> dict:
    """Load YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def load_text(file_path: Path) -> str:
    """Load text file."""
    with open(file_path, 'r') as f:
        return f.read()


def deploy_agent():
    """Deploy the LADBS agent to Azure AI Foundry."""
    
    print("=" * 60)
    print("LADBS Agent Deployment")
    print("=" * 60)
    
    # Validate environment
    if not SUBSCRIPTION_ID:
        print("ERROR: AZURE_SUBSCRIPTION_ID environment variable not set")
        sys.exit(1)
    
    # Load agent configuration
    print("\n📄 Loading agent configuration...")
    agent_config = load_yaml(AGENT_YAML)
    system_prompt = load_text(SYSTEM_PROMPT)
    mcp_tool_config = load_yaml(MCP_TOOL_YAML)
    
    print(f"   Agent: {agent_config['name']}")
    print(f"   Model: {agent_config['model']['deployment']}")
    print(f"   Tools: {len(agent_config['tools'])} tool(s)")
    
    # Connect to Azure AI Foundry
    print("\n🔗 Connecting to Azure AI Foundry...")
    credential = DefaultAzureCredential()
    
    try:
        # Create project client
        project_client = AIProjectClient(
            credential=credential,
            subscription_id=SUBSCRIPTION_ID,
            resource_group_name=RESOURCE_GROUP,
            project_name=PROJECT_NAME
        )
        print(f"   ✓ Connected to project: {PROJECT_NAME}")
        
    except Exception as e:
        print(f"   ✗ Failed to connect: {e}")
        sys.exit(1)
    
    # Register MCP Tool
    print("\n🔧 Registering MCP tool...")
    try:
        # Create MCP connection/tool
        mcp_tool = AgentTool(
            type="mcp",
            mcp={
                "name": mcp_tool_config['name'],
                "description": mcp_tool_config['description'],
                "endpoint": {
                    "url": mcp_tool_config['endpoint']['url'],
                    "authentication": mcp_tool_config['endpoint']['authentication']
                },
                "tools": mcp_tool_config['tools']
            }
        )
        print(f"   ✓ MCP tool configured: {mcp_tool_config['name']}")
        
    except Exception as e:
        print(f"   ✗ Failed to configure MCP tool: {e}")
        print(f"   ⚠️  Continuing with agent deployment...")
    
    # Deploy Agent
    print("\n🤖 Deploying agent...")
    try:
        agent = Agent(
            name=agent_config['name'],
            description=agent_config['description'],
            instructions=system_prompt,
            model=agent_config['model']['deployment'],
            tools=[mcp_tool] if 'mcp_tool' in locals() else [],
            temperature=agent_config.get('temperature', 0.7),
            max_tokens=agent_config.get('max_tokens', 2000)
        )
        
        # Create or update agent
        deployed_agent = project_client.agents.create_or_update(agent)
        
        print(f"   ✓ Agent deployed: {deployed_agent.id}")
        print(f"   ✓ Name: {deployed_agent.name}")
        print(f"   ✓ Model: {deployed_agent.model}")
        
    except Exception as e:
        print(f"   ✗ Failed to deploy agent: {e}")
        print(f"\n💡 Note: Azure AI Agent Service may require manual configuration.")
        print(f"   Please deploy the agent manually in Azure AI Foundry Portal:")
        print(f"   1. Navigate to project '{PROJECT_NAME}'")
        print(f"   2. Go to Agents > Create Agent")
        print(f"   3. Use configuration from {AGENT_YAML}")
        sys.exit(1)
    
    # Success
    print("\n" + "=" * 60)
    print("✅ LADBS Agent Deployment Complete!")
    print("=" * 60)
    print(f"\nAgent ID: {deployed_agent.id}")
    print(f"\nTest the agent in Azure AI Foundry Portal:")
    print(f"https://ai.azure.com/build/projects/{PROJECT_NAME}/agents")
    print()


if __name__ == "__main__":
    try:
        deploy_agent()
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
