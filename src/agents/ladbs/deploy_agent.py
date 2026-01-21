#!/usr/bin/env python3
"""
Deploy LADBS AI Agent Definition to Azure AI Foundry.

This script:
1. Loads the agent configuration from agent.yaml
2. Connects to Azure AI Foundry
3. Creates/updates the agent definition using PromptAgentDefinition
4. Supports idempotent operations (create new version if updated)
"""

import asyncio
import os
import sys
from pathlib import Path
import yaml
from azure.identity.aio import AzureCliCredential
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

# Configuration
# Use foundryProjectEndpoint from azd env, fallback to AZURE_AI_PROJECT_ENDPOINT for manual runs
AZURE_AI_PROJECT_ENDPOINT = os.getenv("foundryProjectEndpoint") or os.getenv("AZURE_AI_PROJECT_ENDPOINT")

# Paths
AGENT_DIR = Path(__file__).parent
AGENT_YAML = AGENT_DIR / "agent.yaml"
SYSTEM_PROMPT = AGENT_DIR / "system-prompt.md"


def load_yaml(file_path: Path) -> dict:
    """Load YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def load_text(file_path: Path) -> str:
    """Load text file."""
    with open(file_path, 'r') as f:
        return f.read()


async def deploy_agent():
    """Deploy the LADBS agent to Azure AI Foundry."""
    
    print("=" * 60)
    print("LADBS Agent Definition Deployment")
    print("=" * 60)
    
    # Validate environment
    if not AZURE_AI_PROJECT_ENDPOINT:
        print("ERROR: foundryProjectEndpoint environment variable not set")
        sys.exit(1)
    
    # Load agent configuration
    print("\n📄 Loading agent configuration...")
    agent_config = load_yaml(AGENT_YAML)
    system_prompt = load_text(SYSTEM_PROMPT)
    
    print(f"   Agent: {agent_config['name']}")
    print(f"   Model: {agent_config['model']['deployment']}")
    if 'tools' in agent_config:
        print(f"   Tools: {len(agent_config['tools'])} tool(s)")
    
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
            
            # Deploy Agent using PromptAgentDefinition
            print("\n🤖 Deploying agent definition...")
            
            # Create a persistent agent using the new API (version 2.0)
            # This will create a new version if the agent already exists (idempotent)
            created_agent = await project_client.agents.create_version(
                agent_name=agent_config['name'],
                definition=PromptAgentDefinition(
                    model=agent_config['model']['deployment'],
                    instructions=system_prompt,
                    temperature=agent_config.get('temperature', 0.7),
                    # Note: Tools are registered separately via deploy_tools.py
                )
            )
            
            print(f"   ✓ Agent deployed: {created_agent.name}")
            print(f"   ✓ Agent ID: {created_agent.id}")
            print(f"   ✓ Version: {created_agent.version}")
            
            # Success
            print("\n" + "=" * 60)
            print("✅ Agent Definition Deployed!")
            print("=" * 60)
            print(f"\nAgent Name: {created_agent.name}")
            print(f"Agent ID: {created_agent.id}")
            print(f"Version: {created_agent.version}")
            print()
            
    except Exception as e:
        print(f"   ✗ Failed to deploy agent: {e}")
        print(f"\n💡 Note: Azure AI Agent Service may require manual configuration.")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(deploy_agent())
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
