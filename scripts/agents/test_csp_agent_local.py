#!/usr/bin/env python3
"""
CSP Agent Local Test Script.

This script tests the CSP Agent locally by connecting to deployed MCP servers
and using Azure OpenAI for inference. It simulates what the deployed container app agent does
but runs entirely on your local machine.

Usage:
    uv run python test_csp_agent_local.py
    uv run python test_csp_agent_local.py --query "How do I get an electrical permit?"
    uv run python test_csp_agent_local.py --interactive
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import AzureOpenAI

load_dotenv()

# Configuration
MCP_SERVERS = {
    "LADBS": os.environ.get(
        "MCP_LADBS_URL",
        "https://aldelar-csp-mcp-ladbs.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp",
    ),
    "LADWP": os.environ.get(
        "MCP_LADWP_URL",
        "https://aldelar-csp-mcp-ladwp.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp",
    ),
    "LASAN": os.environ.get(
        "MCP_LASAN_URL",
        "https://aldelar-csp-mcp-lasan.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp",
    ),
    "CSP": os.environ.get(
        "MCP_CSP_URL",
        "https://aldelar-csp-mcp-csp.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp",
    ),
}

AZURE_OPENAI_ENDPOINT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT",
    "https://aldelar-csp-foundry.cognitiveservices.azure.com/",
)
DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4.1")

# System prompt
SYSTEM_PROMPT = """You are the Citizen Services Portal Agent (CSP Agent), an AI assistant for 
City of Los Angeles government services. You help citizens navigate services across LADBS 
(Building & Safety), LADWP (Water & Power), LASAN (Sanitation), and other departments.

When you need information, use the appropriate tools. Tool names are prefixed with the agency name 
(e.g., LADBS_queryKB, LADWP_queryKB, LASAN_queryKB).

## Your Capabilities:
- Answer questions about permits, inspections, utility services, waste disposal
- Help citizens understand requirements and processes
- Create multi-step plans for complex projects (like solar installations)
- Guide citizens through forms and applications

## Key Guidelines:
1. Always use tools to get accurate, up-to-date information
2. Be helpful, concise, and guide citizens step by step
3. When a task requires user action (phone call, in-person visit), clearly explain what they need to do
4. For multi-agency projects, coordinate information from all relevant departments
"""


async def discover_tools(server_name: str, server_url: str) -> list:
    """Discover tools from an MCP server."""
    tools = []
    try:
        async with streamablehttp_client(server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    openai_tool = {
                        "type": "function",
                        "function": {
                            "name": f"{server_name}_{tool.name}",
                            "description": f"[{server_name}] {tool.description}",
                            "parameters": tool.inputSchema
                            if hasattr(tool, "inputSchema")
                            else {},
                        },
                    }
                    tools.append(
                        {
                            "openai_tool": openai_tool,
                            "server_name": server_name,
                            "server_url": server_url,
                            "mcp_tool_name": tool.name,
                        }
                    )
    except Exception as e:
        print(f"  ⚠ {server_name}: Failed to connect - {e}", file=sys.stderr)
    return tools


async def call_mcp_tool(server_url: str, tool_name: str, arguments: dict) -> str:
    """Call an MCP tool and return the result."""
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else ""


def create_openai_client() -> AzureOpenAI:
    """Create Azure OpenAI client with default credentials."""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")

    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=token.token,
        api_version="2024-10-21",
    )
    return client


async def chat_with_agent(
    client: AzureOpenAI,
    all_tools: list,
    tool_lookup: dict,
    messages: list,
    user_message: str,
    verbose: bool = False,
) -> str:
    """Send a message to the agent and get a response."""
    messages.append({"role": "user", "content": user_message})

    openai_tools = [t["openai_tool"] for t in all_tools]

    max_iterations = 10
    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            tool_choice="auto" if openai_tools else None,
        )

        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                if verbose:
                    print(f"  → Calling: {tool_name}")
                    print(f"    Args: {json.dumps(arguments)[:100]}...")

                tool_info = tool_lookup.get(tool_name)
                if tool_info:
                    try:
                        result = await call_mcp_tool(
                            tool_info["server_url"],
                            tool_info["mcp_tool_name"],
                            arguments,
                        )
                        if verbose:
                            print(f"    Result: {result[:100]}...")

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result,
                            }
                        )
                    except Exception as e:
                        error_msg = f"Error calling tool: {e}"
                        if verbose:
                            print(f"    Error: {error_msg}")
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": error_msg,
                            }
                        )
                else:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Unknown tool: {tool_name}",
                        }
                    )
        else:
            messages.append({"role": "assistant", "content": message.content})
            return message.content

    return "Max iterations reached without final response"


async def run_test_queries(verbose: bool = False):
    """Run predefined test queries."""
    print("=" * 60)
    print("CSP Agent Local Test")
    print("=" * 60)

    # Discover tools
    print("\nDiscovering MCP tools...")
    all_tools = []
    for server_name, server_url in MCP_SERVERS.items():
        tools = await discover_tools(server_name, server_url)
        all_tools.extend(tools)
        if tools:
            print(f"  ✓ {server_name}: {len(tools)} tools")

    print(f"\nTotal tools available: {len(all_tools)}")

    # Create tool lookup
    tool_lookup = {t["openai_tool"]["function"]["name"]: t for t in all_tools}

    # Create OpenAI client
    print("\nConnecting to Azure OpenAI...")
    client = create_openai_client()
    print(f"  ✓ Connected to {DEPLOYMENT_NAME}")

    # Test queries
    test_queries = [
        "What are the requirements for an electrical permit for a solar panel installation?",
        "I want to install solar panels. What's the process with LADBS for permits and LADWP for interconnection?",
        "How do I dispose of old batteries and paint cans?",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"User: {query}")
        print("=" * 60)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        response = await chat_with_agent(
            client, all_tools, tool_lookup, messages, query, verbose
        )

        print(f"\nAgent: {response}")

    print(f"\n{'='*60}")
    print("Test Complete!")
    print("=" * 60)


async def run_interactive(verbose: bool = False):
    """Run interactive chat session."""
    print("=" * 60)
    print("CSP Agent Interactive Mode")
    print("Type 'quit' or 'exit' to end the session")
    print("=" * 60)

    # Discover tools
    print("\nDiscovering MCP tools...")
    all_tools = []
    for server_name, server_url in MCP_SERVERS.items():
        tools = await discover_tools(server_name, server_url)
        all_tools.extend(tools)
        if tools:
            print(f"  ✓ {server_name}: {len(tools)} tools")

    tool_lookup = {t["openai_tool"]["function"]["name"]: t for t in all_tools}

    print("\nConnecting to Azure OpenAI...")
    client = create_openai_client()
    print(f"  ✓ Connected to {DEPLOYMENT_NAME}")
    print("\nReady! Ask me anything about LA city services.\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            response = await chat_with_agent(
                client, all_tools, tool_lookup, messages, user_input, verbose
            )
            print(f"\nAgent: {response}\n")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


async def run_single_query(query: str, verbose: bool = False):
    """Run a single query."""
    print("Discovering MCP tools...")
    all_tools = []
    for server_name, server_url in MCP_SERVERS.items():
        tools = await discover_tools(server_name, server_url)
        all_tools.extend(tools)

    tool_lookup = {t["openai_tool"]["function"]["name"]: t for t in all_tools}

    client = create_openai_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print(f"\nQuery: {query}\n")
    response = await chat_with_agent(
        client, all_tools, tool_lookup, messages, query, verbose
    )
    print(f"Response:\n{response}")


def main():
    parser = argparse.ArgumentParser(description="Test CSP Agent locally")
    parser.add_argument(
        "--query", "-q", type=str, help="Run a single query"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show tool calls"
    )

    args = parser.parse_args()

    if args.query:
        asyncio.run(run_single_query(args.query, args.verbose))
    elif args.interactive:
        asyncio.run(run_interactive(args.verbose))
    else:
        asyncio.run(run_test_queries(args.verbose))


if __name__ == "__main__":
    main()
