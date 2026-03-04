#!/usr/bin/env python3
"""
CSP Agent Azure Deployment Test Script.

This script tests the CSP Agent deployed to Azure Container Apps.
It connects to the agent's Responses API endpoint and validates end-to-end functionality.

Usage:
    uv run python test_csp_agent_azure.py
    uv run python test_csp_agent_azure.py --query "How do I get a building permit?"
    uv run python test_csp_agent_azure.py --interactive
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Optional

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

# Configuration - Update these based on your deployment
FOUNDRY_PROJECT_ENDPOINT = os.environ.get(
    "FOUNDRY_PROJECT_ENDPOINT",
    "https://aldelar-csp-foundry.services.ai.azure.com/api/projects/aldelar-csp-foundry-project",
)
AGENT_NAME = os.environ.get("CSP_AGENT_NAME", "csp-agent")


def get_azure_token() -> str:
    """Get Azure access token for API calls."""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    return token.token


async def list_agents() -> list:
    """List all agents in the Foundry project."""
    import httpx
    
    token = get_azure_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    url = f"{FOUNDRY_PROJECT_ENDPOINT}/agents?api-version=2024-12-01-preview"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json().get("value", [])
        else:
            print(f"Error listing agents: {response.status_code}")
            print(response.text)
            return []


async def get_agent(agent_id: str) -> Optional[dict]:
    """Get details of a specific agent."""
    import httpx
    
    token = get_azure_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    url = f"{FOUNDRY_PROJECT_ENDPOINT}/agents/{agent_id}?api-version=2024-12-01-preview"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting agent: {response.status_code}")
            print(response.text)
            return None


async def create_thread() -> Optional[str]:
    """Create a new conversation thread."""
    import httpx
    
    token = get_azure_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    url = f"{FOUNDRY_PROJECT_ENDPOINT}/threads?api-version=2024-12-01-preview"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json={}, timeout=30)
        
        if response.status_code in (200, 201):
            return response.json().get("id")
        else:
            print(f"Error creating thread: {response.status_code}")
            print(response.text)
            return None


async def send_message(thread_id: str, agent_id: str, message: str) -> Optional[str]:
    """Send a message to the agent and get a response."""
    import httpx
    
    token = get_azure_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    # Add message to thread
    message_url = f"{FOUNDRY_PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version=2024-12-01-preview"
    message_body = {
        "role": "user",
        "content": message,
    }
    
    async with httpx.AsyncClient() as client:
        # Add message
        response = await client.post(
            message_url, headers=headers, json=message_body, timeout=30
        )
        if response.status_code not in (200, 201):
            print(f"Error adding message: {response.status_code}")
            print(response.text)
            return None
        
        # Run the agent
        run_url = f"{FOUNDRY_PROJECT_ENDPOINT}/threads/{thread_id}/runs?api-version=2024-12-01-preview"
        run_body = {"assistant_id": agent_id}
        
        response = await client.post(
            run_url, headers=headers, json=run_body, timeout=60
        )
        if response.status_code not in (200, 201):
            print(f"Error running agent: {response.status_code}")
            print(response.text)
            return None
        
        run_id = response.json().get("id")
        
        # Poll for completion
        run_status_url = f"{FOUNDRY_PROJECT_ENDPOINT}/threads/{thread_id}/runs/{run_id}?api-version=2024-12-01-preview"
        
        for _ in range(60):  # Max 60 seconds
            await asyncio.sleep(1)
            response = await client.get(run_status_url, headers=headers, timeout=30)
            if response.status_code == 200:
                status = response.json().get("status")
                if status == "completed":
                    break
                elif status in ("failed", "cancelled", "expired"):
                    print(f"Run failed with status: {status}")
                    return None
        
        # Get messages
        messages_url = f"{FOUNDRY_PROJECT_ENDPOINT}/threads/{thread_id}/messages?api-version=2024-12-01-preview"
        response = await client.get(messages_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            messages = response.json().get("data", [])
            # Find the latest assistant message
            for msg in messages:
                if msg.get("role") == "assistant":
                    content = msg.get("content", [])
                    if content and len(content) > 0:
                        return content[0].get("text", {}).get("value", "")
        
        return None


async def run_health_check():
    """Run a health check on the deployed agent."""
    print("=" * 60)
    print("CSP Agent Azure Deployment Test")
    print("=" * 60)
    
    print(f"\nFoundry Endpoint: {FOUNDRY_PROJECT_ENDPOINT}")
    
    # List agents
    print("\n1. Listing deployed agents...")
    agents = await list_agents()
    
    if not agents:
        print("   ⚠ No agents found in the project")
        print("\n   The CSP Agent may not be deployed yet.")
        print("   To deploy, run: azd deploy csp-agent")
        return False
    
    print(f"   Found {len(agents)} agent(s):")
    target_agent = None
    for agent in agents:
        agent_name = agent.get("name", "unnamed")
        agent_id = agent.get("id", "unknown")
        print(f"   - {agent_name} (ID: {agent_id})")
        if AGENT_NAME.lower() in agent_name.lower():
            target_agent = agent
    
    if not target_agent:
        print(f"\n   ⚠ CSP Agent '{AGENT_NAME}' not found")
        return False
    
    print(f"\n2. Testing CSP Agent: {target_agent.get('name')}")
    
    # Get agent details
    agent_id = target_agent.get("id")
    agent_details = await get_agent(agent_id)
    if agent_details:
        print(f"   Model: {agent_details.get('model', 'unknown')}")
        tools = agent_details.get("tools", [])
        print(f"   Tools: {len(tools)}")
    
    # Create thread and test conversation
    print("\n3. Creating conversation thread...")
    thread_id = await create_thread()
    if not thread_id:
        print("   ✗ Failed to create thread")
        return False
    print(f"   ✓ Thread created: {thread_id}")
    
    # Send test message
    print("\n4. Sending test query...")
    test_query = "What are the requirements for an electrical permit?"
    print(f"   Query: {test_query}")
    
    response = await send_message(thread_id, agent_id, test_query)
    if response:
        print(f"\n   Response:\n   {response[:500]}...")
        print("\n   ✓ Agent responded successfully!")
        return True
    else:
        print("   ✗ Failed to get response from agent")
        return False


async def run_interactive():
    """Run interactive session with deployed agent."""
    print("=" * 60)
    print("CSP Agent Azure - Interactive Mode")
    print("Type 'quit' or 'exit' to end the session")
    print("=" * 60)
    
    # Find the agent
    agents = await list_agents()
    target_agent = None
    for agent in agents:
        if AGENT_NAME.lower() in agent.get("name", "").lower():
            target_agent = agent
            break
    
    if not target_agent:
        print(f"Agent '{AGENT_NAME}' not found")
        return
    
    agent_id = target_agent.get("id")
    print(f"\nConnected to: {target_agent.get('name')}")
    
    # Create thread
    thread_id = await create_thread()
    if not thread_id:
        print("Failed to create conversation thread")
        return
    
    print("Ready! Ask me anything about LA city services.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            
            print("Agent: Thinking...")
            response = await send_message(thread_id, agent_id, user_input)
            if response:
                print(f"Agent: {response}\n")
            else:
                print("Agent: Sorry, I couldn't process that request.\n")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


async def run_single_query(query: str):
    """Run a single query against the deployed agent."""
    agents = await list_agents()
    target_agent = None
    for agent in agents:
        if AGENT_NAME.lower() in agent.get("name", "").lower():
            target_agent = agent
            break
    
    if not target_agent:
        print(f"Agent '{AGENT_NAME}' not found")
        return
    
    agent_id = target_agent.get("id")
    thread_id = await create_thread()
    
    if not thread_id:
        print("Failed to create thread")
        return
    
    print(f"Query: {query}\n")
    response = await send_message(thread_id, agent_id, query)
    if response:
        print(f"Response:\n{response}")
    else:
        print("Failed to get response")


def main():
    parser = argparse.ArgumentParser(
        description="Test CSP Agent deployed to Azure Container Apps"
    )
    parser.add_argument("--query", "-q", type=str, help="Run a single query")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List deployed agents"
    )

    args = parser.parse_args()

    try:
        import httpx
    except ImportError:
        print("Installing required package: httpx")
        os.system("uv pip install httpx --quiet")
        import httpx

    if args.list:
        agents = asyncio.run(list_agents())
        print("Deployed Agents:")
        for agent in agents:
            print(f"  - {agent.get('name')} (ID: {agent.get('id')})")
    elif args.query:
        asyncio.run(run_single_query(args.query))
    elif args.interactive:
        asyncio.run(run_interactive())
    else:
        success = asyncio.run(run_health_check())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
