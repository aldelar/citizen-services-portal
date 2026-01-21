#!/usr/bin/env python3
"""
Deploy AI Agent Definition to Azure AI Foundry.

This script:
1. Loads the agent configuration from agent.yaml
2. Connects to Azure AI Foundry
3. Creates/updates the agent definition using PromptAgentDefinition
4. Supports idempotent operations (create new version if updated)

Usage:
    python deploy_agent.py <agent_name>
    
Example:
    python deploy_agent.py ladbs
"""

import asyncio
import os
import sys
from pathlib import Path
import yaml
import requests
from azure.identity.aio import AzureCliCredential
from azure.identity import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

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


def load_text(file_path: Path) -> str:
    """Load text file."""
    with open(file_path, 'r') as f:
        return f.read()


def substitute_env_vars(content: str) -> str:
    """
    Substitute environment variable placeholders in content.
    Supports ${VAR_NAME} syntax.
    """
    import re
    
    def replace_var(match):
        var_name = match.group(1)
        value = os.getenv(var_name)
        if value is None:
            print(f"   ⚠️  Warning: Environment variable {var_name} not set")
            return match.group(0)  # Return original if not found
        return value
    
    return re.sub(r'\$\{([^}]+)\}', replace_var, content)


def publish_agent(agent_name: str, agent_version: str = None) -> bool:
    """
    Publish agent as a managed deployment in Azure AI Foundry.
    
    This creates a managed deployment that makes the agent available for production use.
    Uses Azure Resource Manager API to create/update an agent deployment.
    
    Args:
        agent_name: Name of the agent to publish
        agent_version: Specific version to publish (required for deployment)
    
    Returns:
        True if successful, False otherwise
    """
    print("\n📦 Publishing agent deployment...")
    if agent_version:
        print(f"   Publishing version: {agent_version}")
    
    # Validate required environment variables
    if not all([AZURE_SUBSCRIPTION_ID, RESOURCE_GROUP_NAME, FOUNDRY_NAME, FOUNDRY_PROJECT_NAME]):
        print("   ⚠️  Missing required environment variables for publishing")
        print("   ℹ️  Agent created but not published")
        return False
    
    if not agent_version:
        print("   ⚠️  Agent version is required for publishing")
        print("   ℹ️  Agent created but not published")
        return False
    
    try:
        # Get ARM token (management plane)
        ARM_SCOPE = "https://management.azure.com/.default"
        credential = DefaultAzureCredential()
        token = credential.get_token(ARM_SCOPE).token
        
        api_version = "2025-10-01-preview"
        application_name = agent_name
        deployment_name = agent_name+"_production"
        
        # Step 1: Create/Update the Application (references agent by name only)
        app_url = (
            f"https://management.azure.com/subscriptions/{AZURE_SUBSCRIPTION_ID}"
            f"/resourceGroups/{RESOURCE_GROUP_NAME}"
            f"/providers/Microsoft.CognitiveServices/accounts/{FOUNDRY_NAME}"
            f"/projects/{FOUNDRY_PROJECT_NAME}"
            f"/applications/{application_name}"
            f"?api-version={api_version}"
        )
        
        app_payload = {
            "properties": {
                "displayName": agent_name.replace("-", " ").title(),
                "agents": [{"agentName": agent_name}]
            }
        }
        
        print(f"   Creating/updating application...")
        app_response = requests.put(
            app_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=app_payload,
            timeout=90
        )
        app_response.raise_for_status()
        print(f"   ✓ Application ready")
        
        # Step 2: Create/Update the Deployment (references specific agent version)
        
        deployment_payload = {
            "properties": {
                "displayName": f"{agent_name.replace('-', ' ').title()} v{agent_version}",
                "deploymentType": "Managed",
                "protocols": [
                    {
                        "protocol": "responses",
                        "version": "1.0"
                    }
                ],
                "agents": [
                    {
                        "agentName": agent_name,
                        "agentVersion": str(agent_version)
                    }
                ]
            }
        }
        
        # Construct ARM URL for agent deployment
        deployment_url = (
            f"https://management.azure.com/subscriptions/{AZURE_SUBSCRIPTION_ID}"
            f"/resourceGroups/{RESOURCE_GROUP_NAME}"
            f"/providers/Microsoft.CognitiveServices/accounts/{FOUNDRY_NAME}"
            f"/projects/{FOUNDRY_PROJECT_NAME}"
            f"/applications/{application_name}"
            f"/agentdeployments/{deployment_name}"
            f"?api-version={api_version}"
        )
        
        print(f"   Deploying agent version {agent_version}...")
        
        # Make PUT request to create/update deployment
        response = requests.put(
            deployment_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=deployment_payload,
            timeout=90
        )
        
        response.raise_for_status()
        deployment = response.json()
        
        print(f"   ✓ Agent deployment published")
        print(f"   ✓ Deployment: {deployment_name}")
        
        # Verify the version in the response
        if 'properties' in deployment and 'agents' in deployment['properties']:
            deployed_agents = deployment['properties']['agents']
            if deployed_agents:
                deployed_version = deployed_agents[0].get('agentVersion', 'unknown')
                print(f"   ✓ Agent version deployed: {deployed_version}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Failed to publish agent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        print(f"   ℹ️  Agent created but not published")
        return False
    except Exception as e:
        print(f"   ✗ Unexpected error publishing agent: {e}")
        print(f"   ℹ️  Agent created but not published")
        return False


async def create_agent(agent_config: dict, system_prompt: str):
    """
    Create or update agent in Azure AI Foundry.
    
    Args:
        agent_config: Agent configuration from agent.yaml
        system_prompt: Agent instructions from system-prompt.md
    
    Returns:
        Created agent object with name, id, and version
    """
    print("\n🤖 Creating agent definition...")
    print(f"   Using endpoint: {AZURE_AI_PROJECT_ENDPOINT}")
    
    async with (
        AzureCliCredential() as credential,
        AIProjectClient(
            endpoint=AZURE_AI_PROJECT_ENDPOINT,
            credential=credential
        ) as project_client,
    ):
        # Create a persistent agent using the new API (version 2.0)
        # This will create a new version if the agent already exists (idempotent)
        
        # Extract model from definition (supports both old and new schema)
        if 'definition' in agent_config:
            model = agent_config['definition']['model']
            temperature = agent_config['definition'].get('temperature', 0.7)
        else:
            # Legacy schema support
            model = agent_config['model']['deployment']
            temperature = agent_config.get('temperature', 0.7)
        
        created_agent = await project_client.agents.create_version(
            agent_name=agent_config['name'],
            definition=PromptAgentDefinition(
                model=model,
                instructions=system_prompt,
                temperature=temperature,
                # Note: Tools are registered separately via deploy_tools.py
            )
        )
        
        print(f"   ✓ Agent created: {created_agent.name}")
        print(f"   ✓ Agent ID: {created_agent.id}")
        print(f"   ✓ Version: {created_agent.version}")
        
        return created_agent


async def deploy_agent(agent_name: str):
    """
    Deploy agent to Azure AI Foundry.
    
    This orchestrates the full deployment:
    1. Load configuration
    2. Create/update agent
    3. Publish agent as application
    
    Args:
        agent_name: Name of the agent to deploy
    """
    # Determine agent directory
    script_dir = Path(__file__).parent
    agent_dir = script_dir / agent_name
    
    if not agent_dir.exists():
        print(f"❌ Agent directory not found: {agent_dir}")
        sys.exit(1)
    
    # Paths
    agent_yaml = agent_dir / "agent.yaml"
    system_prompt_file = agent_dir / "system-prompt.md"
    
    if not agent_yaml.exists():
        print(f"❌ Agent configuration not found: {agent_yaml}")
        sys.exit(1)
    
    if not system_prompt_file.exists():
        print(f"❌ System prompt not found: {system_prompt_file}")
        sys.exit(1)
    
    print("=" * 60)
    print(f"{agent_name.upper()} Agent Definition Deployment")
    print("=" * 60)
    
    # Validate environment
    if not AZURE_AI_PROJECT_ENDPOINT:
        print("ERROR: foundryProjectEndpoint environment variable not set")
        sys.exit(1)
    
    # Load agent configuration
    print("\n📄 Loading agent configuration...")
    
    # Load YAML with environment variable substitution
    with open(agent_yaml, 'r') as f:
        agent_yaml_content = f.read()
    agent_yaml_content = substitute_env_vars(agent_yaml_content)
    agent_config = yaml.safe_load(agent_yaml_content)
    
    system_prompt = load_text(system_prompt_file)
    
    # Extract model and tools info (supports both old and new schema)
    if 'definition' in agent_config:
        model = agent_config['definition']['model']
        tools = agent_config['definition'].get('tools', [])
    else:
        # Legacy schema support
        model = agent_config['model']['deployment']
        tools = agent_config.get('tools', [])
    
    print(f"   Agent: {agent_config['name']}")
    print(f"   Model: {model}")
    if tools:
        print(f"   Tools: {len(tools)} tool(s)")
    
    # Connect to Azure AI Foundry
    print("\n🔗 Connecting to Azure AI Foundry...")
    print(f"   ✓ Connected to project endpoint")
    
    try:
        # Step 1: Create agent
        created_agent = await create_agent(agent_config, system_prompt)
        
        # Step 2: Publish agent as an application
        publish_success = publish_agent(
            agent_name=created_agent.name,
            agent_version=str(created_agent.version)
        )
        
        # Success
        print("\n" + "=" * 60)
        if publish_success:
            print("✅ Agent Created and Published!")
        else:
            print("✅ Agent Created (Publishing Skipped)")
        print("=" * 60)
        print(f"\nAgent Name: {created_agent.name}")
        print(f"Agent ID: {created_agent.id}")
        print(f"Version: {created_agent.version}")
        if publish_success:
            print(f"Status: Published")
        print()
        
    except Exception as e:
        print(f"   ✗ Failed to deploy agent: {e}")
        print(f"\n💡 Note: Azure AI Agent Service may require manual configuration.")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python deploy_agent.py <agent_name>")
        print("\nExample:")
        print("  python deploy_agent.py ladbs")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    asyncio.run(deploy_agent(agent_name))


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
