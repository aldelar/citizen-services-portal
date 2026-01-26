"""LADWP MCP Client - Test client for the LADWP MCP server."""

import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()


async def run_client():
    """Test all LADWP MCP server tools."""
    # Connect to the HTTP MCP server
    host = os.environ.get("MCP_SERVER_HOST", "localhost")
    port = os.environ.get("MCP_SERVER_PORT", "8000")

    # Use HTTPS for Azure Container Apps (port 443) or HTTP for local testing
    protocol = "https" if port == "443" else "http"

    # Don't include port 443 in URL for HTTPS (standard port)
    if protocol == "https" and port == "443":
        server_url = f"{protocol}://{host}/mcp"
    else:
        server_url = f"{protocol}://{host}:{port}/mcp"

    print("=" * 60)
    print("LADWP MCP Server Test Client")
    print(f"Connecting to: {server_url}")
    print("=" * 60)

    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            print("\nInitializing MCP session...")
            init_result = await session.initialize()

            print("\nServer Information:")
            print(f"  Server Name: {init_result.serverInfo.name}")
            print(f"  Server Version: {init_result.serverInfo.version}")
            print(f"  Protocol Version: {init_result.protocolVersion}")

            # List available capabilities
            print("\nServer Capabilities:")
            capabilities = init_result.capabilities
            print(f"  Tools: {capabilities.tools is not None}")
            print(f"  Resources: {capabilities.resources is not None}")
            print(f"  Prompts: {capabilities.prompts is not None}")

            # List available tools
            print("\n" + "=" * 60)
            print("Available Tools:")
            print("=" * 60)
            tools_response = await session.list_tools()
            for i, tool in enumerate(tools_response.tools, 1):
                print(f"\n{i}. {tool.name}")
                print(f"   Description: {tool.description}")
                if hasattr(tool, "inputSchema") and tool.inputSchema:
                    print("   Parameters:")
                    if "properties" in tool.inputSchema:
                        for param, details in tool.inputSchema["properties"].items():
                            param_type = details.get("type", "unknown")
                            param_desc = details.get("description", "No description")
                            print(f"     - {param} ({param_type}): {param_desc}")

            # List available resources
            print("\n" + "=" * 60)
            print("Available Resources:")
            print("=" * 60)
            try:
                resources_response = await session.list_resources()
                if resources_response.resources:
                    for i, resource in enumerate(resources_response.resources, 1):
                        print(f"\n{i}. {resource.name}")
                        print(f"   URI: {resource.uri}")
                        print(f"   Description: {resource.description}")
                else:
                    print("  No resources available")
            except Exception as e:
                print(f"  Resources not supported or error: {e}")

            # List available prompts
            print("\n" + "=" * 60)
            print("Available Prompts:")
            print("=" * 60)
            try:
                prompts_response = await session.list_prompts()
                if prompts_response.prompts:
                    for i, prompt in enumerate(prompts_response.prompts, 1):
                        print(f"\n{i}. {prompt.name}")
                        print(f"   Description: {prompt.description}")
                else:
                    print("  No prompts available")
            except Exception as e:
                print(f"  Prompts not supported or error: {e}")

            # Test tool calls
            print("\n" + "=" * 60)
            print("Testing Tool Calls:")
            print("=" * 60)

            # Test 1: Query Knowledge Base (AI Search)
            print("\n1. Testing queryKB (Knowledge Base Search)...")
            try:
                kb_result = await session.call_tool(
                    "queryKB",
                    {"query": "What are the LADWP time-of-use rate plans?", "top": 3}
                )
                print("   ✅ queryKB succeeded!")
                if kb_result.content:
                    for item in kb_result.content:
                        if hasattr(item, 'text'):
                            # Show first 500 chars of response
                            text = item.text[:500] + "..." if len(item.text) > 500 else item.text
                            print(f"   Response: {text}")
            except Exception as e:
                print(f"   ❌ queryKB failed: {e}")

            # Test 2: Get Account Information
            print("\n2. Testing account_show...")
            try:
                account_result = await session.call_tool(
                    "account_show",
                    {"account_number": "123456789"}
                )
                print("   ✅ account_show succeeded!")
                if account_result.content:
                    for item in account_result.content:
                        if hasattr(item, 'text'):
                            print(f"   Response: {item.text[:300]}...")
            except Exception as e:
                print(f"   ❌ account_show failed: {e}")

            # Test 3: List Rate Plans
            print("\n3. Testing plans_list...")
            try:
                plans_result = await session.call_tool(
                    "plans_list",
                    {"account_number": "123456789"}
                )
                print("   ✅ plans_list succeeded!")
                if plans_result.content:
                    for item in plans_result.content:
                        if hasattr(item, 'text'):
                            print(f"   Response: {item.text[:300]}...")
            except Exception as e:
                print(f"   ❌ plans_list failed: {e}")

            # Test 4: Get Filed Rebates
            print("\n4. Testing rebates_filed...")
            try:
                rebates_result = await session.call_tool(
                    "rebates_filed",
                    {"account_number": "123456789"}
                )
                print("   ✅ rebates_filed succeeded!")
                if rebates_result.content:
                    for item in rebates_result.content:
                        if hasattr(item, 'text'):
                            print(f"   Response: {item.text[:300]}...")
            except Exception as e:
                print(f"   ❌ rebates_filed failed: {e}")

            # Test 5: Get Interconnection Status
            print("\n5. Testing interconnection_getStatus...")
            try:
                status_result = await session.call_tool(
                    "interconnection_getStatus",
                    {"application_id": "IA-2026-12345"}
                )
                print("   ✅ interconnection_getStatus succeeded!")
                if status_result.content:
                    for item in status_result.content:
                        if hasattr(item, 'text'):
                            print(f"   Response: {item.text[:300]}...")
            except Exception as e:
                print(f"   ❌ interconnection_getStatus failed: {e}")

            print("\n" + "=" * 60)
            print("MCP Server Testing Complete!")
            print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_client())
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback

        traceback.print_exc()
