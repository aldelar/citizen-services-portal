#!/usr/bin/env python3
"""
CSP Agent Responses API Test Script.

This script tests the CSP Agent using the Responses API protocol,
aligned with the unified local ↔ Azure API contract spec.

Usage:
    uv run python test_csp_agent_responses.py
    uv run python test_csp_agent_responses.py --query "How do I get a building permit?"
    uv run python test_csp_agent_responses.py --interactive
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

# Configuration
AGENT_ENDPOINT = os.environ.get(
    "CSP_AGENT_URL",
    "http://localhost:8088",
)
API_VERSION = "2025-11-15-preview"
USE_AUTH = os.environ.get("CSP_AGENT_USE_AUTH", "false").lower() == "true"


def get_azure_token() -> str:
    """Get Azure access token for AI Foundry."""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://ai.azure.com/.default")
    return token.token


async def send_message(
    message: str,
    history: Optional[list[dict]] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Send a message using Responses API and get response.
    
    Returns:
        Tuple of (response_text, conversation_id)
    """
    import httpx
    
    headers = {
        "Content-Type": "application/json",
    }
    if USE_AUTH:
        token = get_azure_token()
        headers["Authorization"] = f"Bearer {token}"
    
    # Build request payload
    payload = {
        "input": message,
        "stream": False,
    }
    
    if history:
        lines = ["Conversation so far:"]
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not role or not content:
                continue
            label = "User" if role == "user" else "Assistant"
            lines.append(f"{label}: {content}")
        lines.append("\nRespond to the latest user message using the context above.")
        payload["input"] = "\n".join(lines)
    
    # Build URL with api-version
    url = f"{AGENT_ENDPOINT}/responses?api-version={API_VERSION}"
    
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, headers=headers, json=payload)
        
        if response.status_code not in (200, 201):
            print(f"Error: {response.status_code}")
            print(response.text)
            return None, None
        
        data = response.json()
        
        # Extract conversation ID
        conv_id = None
        if "conversation" in data:
            conv = data["conversation"]
            if isinstance(conv, dict):
                conv_id = conv.get("id")
            elif isinstance(conv, str):
                conv_id = conv
        
        # Extract response text from output
        text = None
        if "output" in data and isinstance(data["output"], list):
            for item in data["output"]:
                if isinstance(item, dict) and "content" in item:
                    content = item["content"]
                    if isinstance(content, list):
                        for c in content:
                            if isinstance(c, dict) and "text" in c:
                                text = c["text"]
                                break
                    if text:
                        break
        
        return text, conv_id


async def run_health_check():
    """Run a health check on the agent using Responses API."""
    print("=" * 60)
    print("CSP Agent Responses API Test")
    print("=" * 60)
    
    print(f"\nAgent Endpoint: {AGENT_ENDPOINT}")
    print(f"API Version: {API_VERSION}")
    
    # Test 1: Send initial message (no conversation ID)
    print("\n1. Sending initial message (no conversation context)...")
    test_query = "What are the requirements for an electrical permit?"
    print(f"   Query: {test_query}")
    
    response, conv_id = await send_message(test_query)
    
    if response:
        print(f"\n   Response:\n   {response[:500]}...")
        print("\n   ✓ Agent responded successfully!")
        
        # Test 2: Send follow-up with explicit history
        print("\n2. Sending follow-up message with explicit history...")
        follow_up = "What documents do I need?"
        print(f"   Query: {follow_up}")
        
        history = [
            {"role": "user", "content": test_query},
            {"role": "assistant", "content": response},
            {"role": "user", "content": follow_up},
        ]
        response2, _ = await send_message(follow_up, history)
        
        if response2:
            print(f"\n   Response:\n   {response2[:500]}...")
            print("\n   ✓ History-based follow-up completed!")
            return True
        else:
            print("   ✗ Failed to get follow-up response")
            return False
    else:
        print("   ✗ Failed to get response from agent")
        return False


async def run_interactive():
    """Run interactive session with the agent."""
    print("=" * 60)
    print("CSP Agent Responses API - Interactive Mode")
    print("Type 'quit' or 'exit' to end the session")
    print("=" * 60)
    
    print("\nReady! Ask me anything about LA city services.\n")
    
    history: list[dict] = []
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break
            
            print("Agent: Thinking...")
            history.append({"role": "user", "content": user_input})
            response, _ = await send_message(user_input, history)
            
            if response:
                print(f"Agent: {response}\n")
                history.append({"role": "assistant", "content": response})
            else:
                print("Agent: Sorry, I couldn't process that request.\n")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


async def run_single_query(query: str):
    """Run a single query against the agent."""
    print(f"Query: {query}\n")
    response, conv_id = await send_message(query)
    if response:
        print(f"Response:\n{response}")
    else:
        print("Failed to get response")


def main():
    parser = argparse.ArgumentParser(
        description="Test CSP Agent with Responses API"
    )
    parser.add_argument("--query", "-q", type=str, help="Run a single query")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )

    args = parser.parse_args()

    try:
        import httpx
    except ImportError:
        print("Installing required package: httpx")
        os.system("uv pip install httpx --quiet")
        import httpx

    if args.query:
        asyncio.run(run_single_query(args.query))
    elif args.interactive:
        asyncio.run(run_interactive())
    else:
        success = asyncio.run(run_health_check())
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
