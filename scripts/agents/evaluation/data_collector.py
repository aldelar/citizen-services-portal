#!/usr/bin/env python3
"""
Collect agent responses for evaluation.

This script reads test queries from a JSONL file, sends each query to the CSP Agent
(using existing test_csp_agent_local.py logic), captures the response and any context
(KB queries made), and outputs a complete JSONL ready for evaluation.

Usage:
    uv run python -m evaluation.data_collector \
        --input evaluation_data/test_queries.jsonl \
        --output evaluation_data/collected_responses.jsonl

    # With verbose output showing tool calls
    uv run python -m evaluation.data_collector \
        --input evaluation_data/test_queries.jsonl \
        --output evaluation_data/collected_responses.jsonl \
        --verbose
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

# Configuration - reuse from test_csp_agent_local.py
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
API_VERSION = os.environ.get("AZURE_API_VERSION", "2024-10-21")

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
        api_version=API_VERSION,
    )
    return client


async def chat_with_agent_and_capture_context(
    client: AzureOpenAI,
    all_tools: list,
    tool_lookup: dict,
    messages: list,
    user_message: str,
    verbose: bool = False,
) -> tuple[str, str, list[dict]]:
    """
    Send a message to the agent and get a response with context capture.

    Returns:
        Tuple of (response_text, context_text, tool_calls_made)
    """
    messages.append({"role": "user", "content": user_message})

    openai_tools = [t["openai_tool"] for t in all_tools]

    context_parts = []
    tool_calls_made = []
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

                        # Capture context from KB queries
                        if "queryKB" in tool_name.lower() or "query" in tool_name.lower():
                            context_parts.append(result)

                        # Record the tool call
                        tool_calls_made.append(
                            {
                                "tool_name": tool_name,
                                "arguments": arguments,
                                "result": result[:500] if len(result) > 500 else result,
                            }
                        )

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
            context = "\n\n".join(context_parts) if context_parts else ""
            return message.content or "", context, tool_calls_made

    return "Max iterations reached without final response", "", tool_calls_made


async def collect_responses(
    input_file: Path,
    output_file: Path,
    verbose: bool = False,
) -> None:
    """Collect agent responses for each test query."""
    print("=" * 60)
    print("CSP Agent Response Collector for Evaluation")
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

    if not all_tools:
        print("⚠ No tools available. Check MCP server connectivity.")
        print("Proceeding without tools - agent will generate responses without KB access.")

    # Create tool lookup
    tool_lookup = {t["openai_tool"]["function"]["name"]: t for t in all_tools}

    # Create OpenAI client
    print("\nConnecting to Azure OpenAI...")
    client = create_openai_client()
    print(f"  ✓ Connected to {DEPLOYMENT_NAME}")

    # Read test queries
    print(f"\nReading test queries from: {input_file}")
    test_cases = []
    with open(input_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                test_cases.append(json.loads(line))

    print(f"  Found {len(test_cases)} test queries")

    # Collect responses
    print("\nCollecting responses...")
    results = []

    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        print(f"\n[{i}/{len(test_cases)}] {query[:60]}...")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        try:
            response, context, tool_calls = await chat_with_agent_and_capture_context(
                client, all_tools, tool_lookup, messages, query, verbose
            )

            results.append(
                {
                    "query": query,
                    "response": response,
                    "context": context if context else test_case.get("context", ""),
                    "ground_truth": test_case.get("ground_truth", ""),
                    "tool_calls": tool_calls,
                }
            )
            print(f"  ✓ Response: {response[:80]}...")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append(
                {
                    "query": query,
                    "response": f"Error: {e}",
                    "context": test_case.get("context", ""),
                    "ground_truth": test_case.get("ground_truth", ""),
                    "tool_calls": [],
                }
            )

    # Write results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        for result in results:
            f.write(json.dumps(result) + "\n")

    print(f"\n{'='*60}")
    print(f"Collected {len(results)} responses")
    print(f"Output written to: {output_file}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Collect CSP Agent responses for evaluation"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path("evaluation_data/test_queries.jsonl"),
        help="Path to input JSONL with test queries",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("evaluation_data/collected_responses.jsonl"),
        help="Path to output JSONL with collected responses",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show tool calls and results",
    )

    args = parser.parse_args()

    asyncio.run(collect_responses(args.input, args.output, args.verbose))


if __name__ == "__main__":
    main()
