#!/usr/bin/env python3
"""
MCP Servers Health Check and Tool Discovery Script.

This script tests connectivity and discovers tools from all deployed MCP servers.
Can be used for both local and Azure-deployed servers.

Usage:
    # Test Azure-deployed servers (default, uses azd env)
    uv run python test_mcp_servers.py

    # Test local servers
    uv run python test_mcp_servers.py --local

    # Test specific server
    uv run python test_mcp_servers.py --server ladbs
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from typing import Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


# Server name mappings - maps server key to azd env variable pattern
MCP_SERVER_CONFIGS = {
    "LADBS": "MCP_LADBS_URL",
    "LADWP": "MCP_LADWP_URL",
    "LASAN": "MCP_LASAN_URL",
    "CSP": "MCP_CSP_URL",
}


def get_azd_env_values() -> dict:
    """
    Get environment values from azd env get-values.
    
    Returns a dictionary of environment variable names to values.
    """
    try:
        result = subprocess.run(
            ["azd", "env", "get-values"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        env_values = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                # Parse KEY="value" or KEY=value format
                match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
                if match:
                    key = match.group(1)
                    value = match.group(2)
                    # Remove surrounding quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    env_values[key] = value
        
        return env_values
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to get azd env values: {e.stderr}")
        return {}
    except FileNotFoundError:
        print("Warning: azd CLI not found. Please install Azure Developer CLI.")
        return {}


def get_azure_mcp_servers() -> dict:
    """
    Get Azure MCP server URLs from azd environment.
    
    Parses MCP_*_URL values from azd env get-values output.
    """
    azd_env = get_azd_env_values()
    servers = {}
    
    for server_name, env_var in MCP_SERVER_CONFIGS.items():
        url = azd_env.get(env_var)
        if url:
            servers[server_name] = url
    
    return servers


# Local MCP server URLs (for development)
LOCAL_MCP_SERVERS = {
    "LADBS": "http://localhost:8001/mcp",
    "LADWP": "http://localhost:8002/mcp",
    "LASAN": "http://localhost:8003/mcp",
    "CSP": "http://localhost:8004/mcp",
}


async def check_server_health(name: str, url: str, verbose: bool = False) -> dict:
    """Check health and discover tools from an MCP server."""
    result = {
        "name": name,
        "url": url,
        "status": "unknown",
        "version": None,
        "tools": [],
        "tool_count": 0,
        "error": None,
    }

    try:
        async with streamablehttp_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                init_result = await session.initialize()
                result["version"] = init_result.serverInfo.version
                result["protocol_version"] = init_result.protocolVersion

                tools_response = await session.list_tools()
                result["tools"] = [
                    {
                        "name": tool.name,
                        "description": tool.description[:100] + "..."
                        if len(tool.description) > 100
                        else tool.description,
                    }
                    for tool in tools_response.tools
                ]
                result["tool_count"] = len(tools_response.tools)
                result["status"] = "healthy"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def test_tool_call(
    name: str, url: str, tool_name: str, arguments: dict
) -> dict:
    """Test calling a specific tool on an MCP server."""
    result = {
        "server": name,
        "tool": tool_name,
        "arguments": arguments,
        "status": "unknown",
        "response": None,
        "error": None,
    }

    try:
        async with streamablehttp_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tool_result = await session.call_tool(tool_name, arguments)
                result["response"] = (
                    tool_result.content[0].text if tool_result.content else None
                )
                result["status"] = "success"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def run_health_check(
    servers: dict, verbose: bool = False, test_tools: bool = False
) -> list:
    """Run health check on all specified servers."""
    results = []

    print("=" * 60)
    print("MCP Servers Health Check")
    print("=" * 60)

    for name, url in servers.items():
        result = await check_server_health(name, url, verbose)
        results.append(result)

        if result["status"] == "healthy":
            print(f"✓ {name}: {result['tool_count']} tools (v{result['version']})")
            if verbose:
                print(f"  URL: {url}")
                for tool in result["tools"]:
                    print(f"    - {tool['name']}: {tool['description']}")
        else:
            print(f"✗ {name}: {result['error']}")

    print("=" * 60)

    # Optionally test tool calls
    if test_tools:
        print("\nTesting Tool Calls:")
        print("-" * 60)

        test_cases = [
            ("LADBS", "queryKB", {"query": "electrical permit requirements", "top": 1}),
            ("LADWP", "queryKB", {"query": "solar interconnection", "top": 1}),
            ("LASAN", "queryKB", {"query": "hazardous waste disposal", "top": 1}),
        ]

        for server_name, tool_name, args in test_cases:
            if server_name in servers:
                url = servers[server_name]
                tool_result = await test_tool_call(server_name, url, tool_name, args)
                if tool_result["status"] == "success":
                    response_preview = (
                        tool_result["response"][:150] + "..."
                        if tool_result["response"] and len(tool_result["response"]) > 150
                        else tool_result["response"]
                    )
                    print(f"✓ {server_name}.{tool_name}: {response_preview}")
                else:
                    print(f"✗ {server_name}.{tool_name}: {tool_result['error']}")

        print("-" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test MCP servers health and tool discovery"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Test local servers instead of Azure-deployed ones",
    )
    parser.add_argument(
        "--server",
        type=str,
        choices=["ladbs", "ladwp", "lasan", "csp"],
        help="Test only a specific server",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--test-tools", "-t", action="store_true", help="Test tool calls"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results as JSON"
    )

    args = parser.parse_args()

    # Select server configuration
    if args.local:
        servers = LOCAL_MCP_SERVERS
    else:
        servers = get_azure_mcp_servers()
        if not servers:
            print("Error: No Azure MCP server URLs configured.")
            print("Please set the following environment variables:")
            print("  MCP_LADBS_URL, MCP_LADWP_URL, MCP_LASAN_URL, MCP_CSP_URL")
            print("\nAlternatively, use --local to test local servers.")
            sys.exit(1)

    # Filter to specific server if requested
    if args.server:
        server_key = args.server.upper()
        if server_key not in servers:
            print(f"Error: Server '{args.server}' not configured.")
            print(f"Available servers: {', '.join(servers.keys())}")
            sys.exit(1)
        servers = {server_key: servers[server_key]}

    # Run health check
    results = asyncio.run(
        run_health_check(servers, verbose=args.verbose, test_tools=args.test_tools)
    )

    if args.json:
        print(json.dumps(results, indent=2))

    # Exit with error if any server is unhealthy
    unhealthy = [r for r in results if r["status"] != "healthy"]
    if unhealthy:
        sys.exit(1)


if __name__ == "__main__":
    main()
