"""Test client for Reporting MCP server."""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    """Run test client against local server."""
    # Connect to local server
    server_url = "http://localhost:8000/sse"
    
    print(f"Connecting to {server_url}...")
    
    async with sse_client(server_url) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            print("\n=== Available Tools ===")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description[:80]}...")
            
            # Test 1: Get average duration for permit submission
            print("\n=== Test: Get Average Duration (permits.submit) ===")
            result = await session.call_tool(
                "steps_getAverageDuration",
                arguments={
                    "tool_name": "permits.submit",
                    "city": "Los Angeles",
                }
            )
            print(f"Result: {result.content[0].text}")
            
            # Test 2: Get average duration for TOU enrollment
            print("\n=== Test: Get Average Duration (tou.enroll) ===")
            result = await session.call_tool(
                "steps_getAverageDuration",
                arguments={
                    "tool_name": "tou.enroll",
                    "city": "Los Angeles",
                }
            )
            print(f"Result: {result.content[0].text}")
            
            # Test 3: Log a completed step
            print("\n=== Test: Log Completed Step ===")
            result = await session.call_tool(
                "steps_logCompleted",
                arguments={
                    "tool_name": "permits.submit",
                    "city": "Los Angeles",
                    "started_at": "2026-01-15T10:00:00Z",
                    "completed_at": "2026-02-28T14:30:00Z",
                }
            )
            print(f"Result: {result.content[0].text}")
            
            # Test 4: Get average duration for rebates
            print("\n=== Test: Get Average Duration (rebates.apply) ===")
            result = await session.call_tool(
                "steps_getAverageDuration",
                arguments={
                    "tool_name": "rebates.apply",
                }
            )
            print(f"Result: {result.content[0].text}")
            
            print("\n=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())
