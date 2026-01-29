"""Test script for CSP Agent with deployed MCP servers."""

import asyncio
import json
import os

from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


# MCP Server URLs (deployed to Azure Container Apps)
MCP_SERVERS = {
    "LADBS": "https://aldelar-csp-mcp-ladbs.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp",
    "LADWP": "https://aldelar-csp-mcp-ladwp.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp",
    "LASAN": "https://aldelar-csp-mcp-lasan.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp",
    "CSP": "https://aldelar-csp-mcp-csp.gentlewave-1b3fce06.northcentralus.azurecontainerapps.io/mcp",
}

AZURE_OPENAI_ENDPOINT = "https://aldelar-csp-foundry.cognitiveservices.azure.com/"
DEPLOYMENT_NAME = "gpt-4.1"


async def discover_tools(server_name: str, server_url: str) -> list:
    """Discover tools from an MCP server."""
    tools = []
    try:
        async with streamablehttp_client(server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    # Convert MCP tool to OpenAI function format
                    openai_tool = {
                        "type": "function",
                        "function": {
                            "name": f"{server_name}_{tool.name}",
                            "description": f"[{server_name}] {tool.description}",
                            "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                        }
                    }
                    tools.append({
                        "openai_tool": openai_tool,
                        "server_name": server_name,
                        "server_url": server_url,
                        "mcp_tool_name": tool.name
                    })
        print(f"  ✓ {server_name}: {len(tools)} tools discovered")
    except Exception as e:
        print(f"  ✗ {server_name}: Failed to connect - {e}")
    return tools


async def call_mcp_tool(server_url: str, tool_name: str, arguments: dict) -> str:
    """Call an MCP tool and return the result."""
    async with streamablehttp_client(server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else ""


def create_openai_client():
    """Create Azure OpenAI client with default credentials."""
    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=token.token,
        api_version="2024-10-21",
    )
    return client


async def test_agent_conversation(all_tools: list, user_message: str):
    """Test a conversation with the agent."""
    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print(f"{'='*60}")
    
    # Create OpenAI client
    client = create_openai_client()
    
    # System prompt
    system_prompt = """You are the Citizen Services Portal Agent (CSP Agent), an AI assistant for 
City of Los Angeles government services. You help citizens navigate services across LADBS 
(Building & Safety), LADWP (Water & Power), LASAN (Sanitation), and other departments.

When you need information, use the appropriate tools. Tool names are prefixed with the agency name 
(e.g., LADBS_queryKB, LADWP_queryKB, LASAN_queryKB).

Be helpful, concise, and guide citizens through their requests step by step."""

    # Prepare OpenAI tools
    openai_tools = [t["openai_tool"] for t in all_tools]
    
    # Create tool lookup
    tool_lookup = {t["openai_tool"]["function"]["name"]: t for t in all_tools}
    
    # Initial message
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    # Chat loop with tool calling
    max_iterations = 5
    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            tool_choice="auto" if openai_tools else None,
        )
        
        message = response.choices[0].message
        
        # Check for tool calls
        if message.tool_calls:
            messages.append(message)
            
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"\n  → Calling tool: {tool_name}")
                print(f"    Arguments: {json.dumps(arguments, indent=2)[:200]}...")
                
                # Find the tool info
                tool_info = tool_lookup.get(tool_name)
                if tool_info:
                    try:
                        result = await call_mcp_tool(
                            tool_info["server_url"],
                            tool_info["mcp_tool_name"],
                            arguments
                        )
                        print(f"    Result (truncated): {result[:200]}...")
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                    except Exception as e:
                        error_msg = f"Error calling tool: {e}"
                        print(f"    Error: {error_msg}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_msg
                        })
                else:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Unknown tool: {tool_name}"
                    })
        else:
            # Final response
            print(f"\n{'='*60}")
            print("Agent Response:")
            print(f"{'='*60}")
            print(message.content)
            return message.content
    
    print("Max iterations reached")
    return None


async def main():
    """Main test function."""
    print("=" * 60)
    print("CSP Agent Test - Connecting to deployed MCP Servers")
    print("=" * 60)
    
    # Discover tools from all MCP servers
    print("\nDiscovering tools from MCP servers...")
    all_tools = []
    for server_name, server_url in MCP_SERVERS.items():
        tools = await discover_tools(server_name, server_url)
        all_tools.extend(tools)
    
    print(f"\nTotal tools available: {len(all_tools)}")
    
    # List all tools
    print("\nAvailable tools:")
    for tool in all_tools:
        print(f"  - {tool['openai_tool']['function']['name']}")
    
    # Test queries
    test_queries = [
        "What are the requirements for an electrical permit for a solar panel installation?",
        # "I want to install solar panels. What's the process with LADBS for permits and LADWP for interconnection?",
        # "How do I dispose of old batteries and paint cans?",
    ]
    
    for query in test_queries:
        await test_agent_conversation(all_tools, query)
        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
