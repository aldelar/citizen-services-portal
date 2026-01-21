"""LADBS MCP Client - Test client for the LADBS MCP server."""

import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv

load_dotenv()


async def run_client():
    """Test all LADBS MCP server tools."""
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
    print(f"LADBS MCP Server Test Client")
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

            print("\n" + "=" * 60)
            print("MCP Server Discovery Complete!")
            print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_client())
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback

        traceback.print_exc()