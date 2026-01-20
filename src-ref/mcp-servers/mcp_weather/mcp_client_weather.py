# client.py
import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv
load_dotenv()

async def run_client():
    # Connect to the HTTP MCP server
    host = os.environ.get("MCP_WEATHER_SERVER_HOST", "localhost")
    port = os.environ.get("MCP_WEATHER_SERVER_PORT", "8000")
    
    # Use HTTPS for Azure Container Apps (port 443) or HTTP for local testing
    protocol = "https" if port == "443" else "http"
    
    # Don't include port 443 in URL for HTTPS (standard port)
    if protocol == "https" and port == "443":
        server_url = f"{protocol}://{host}/mcp"
    else:
        server_url = f"{protocol}://{host}:{port}/mcp"
    
    print(f"Connecting to: {server_url}")
    
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            print("Initializing MCP session...")
            await session.initialize()
            
            # List available tools
            tools_response = await session.list_tools()
            print("Available tools:")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")
            
            # Call a tool
            result = await session.call_tool(
                "get_weather_forecast",
                arguments={"city": "Los Angeles"}
            )
            print(f"\nTool result: {result.content}")

if __name__ == "__main__":
    asyncio.run(run_client())