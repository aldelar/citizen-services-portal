"""Test client for Reporting MCP server."""

import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run test client against local or deployed server."""
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
    print(f"Reporting MCP Server Test Client")
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
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    print(f"   Parameters:")
                    if 'properties' in tool.inputSchema:
                        for param, details in tool.inputSchema['properties'].items():
                            param_type = details.get('type', 'unknown')
                            param_desc = details.get('description', 'No description')
                            print(f"     - {param} ({param_type}): {param_desc}")

            # Test tool calls
            print("\n" + "=" * 60)
            print("Testing Tool Calls:")
            print("=" * 60)

            # Test 1: Get average duration for permit submission
            print("\n1. Testing steps_getAverageDuration (permits.submit)...")
            try:
                result = await session.call_tool(
                    "steps_getAverageDuration",
                    arguments={
                        "tool_name": "permits.submit",
                        "city": "Los Angeles",
                    }
                )
                print("   ✅ steps_getAverageDuration succeeded!")
                if result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            print(f"   Response: {item.text}")
            except Exception as e:
                print(f"   ❌ steps_getAverageDuration failed: {e}")

            # Test 2: Get average duration for TOU enrollment
            print("\n2. Testing steps_getAverageDuration (tou.enroll)...")
            try:
                result = await session.call_tool(
                    "steps_getAverageDuration",
                    arguments={
                        "tool_name": "tou.enroll",
                        "city": "Los Angeles",
                    }
                )
                print("   ✅ steps_getAverageDuration succeeded!")
                if result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            print(f"   Response: {item.text}")
            except Exception as e:
                print(f"   ❌ steps_getAverageDuration failed: {e}")

            # Test 3: Log a completed step
            print("\n3. Testing steps_logCompleted...")
            try:
                result = await session.call_tool(
                    "steps_logCompleted",
                    arguments={
                        "tool_name": "permits.submit",
                        "city": "Los Angeles",
                        "started_at": "2026-01-15T10:00:00Z",
                        "completed_at": "2026-02-28T14:30:00Z",
                    }
                )
                print("   ✅ steps_logCompleted succeeded!")
                if result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            print(f"   Response: {item.text}")
            except Exception as e:
                print(f"   ❌ steps_logCompleted failed: {e}")

            # Test 4: Get average duration for rebates (no city filter)
            print("\n4. Testing steps_getAverageDuration (rebates.apply, no city)...")
            try:
                result = await session.call_tool(
                    "steps_getAverageDuration",
                    arguments={
                        "tool_name": "rebates.apply",
                    }
                )
                print("   ✅ steps_getAverageDuration succeeded!")
                if result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            print(f"   Response: {item.text}")
            except Exception as e:
                print(f"   ❌ steps_getAverageDuration failed: {e}")

            print("\n" + "=" * 60)
            print("MCP Server Testing Complete!")
            print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback

        traceback.print_exc()
