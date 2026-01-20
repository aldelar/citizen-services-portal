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
            await session.initialize()

            # List available tools
            tools_response = await session.list_tools()
            print("\nAvailable tools:")
            for tool in tools_response.tools:
                print(f"- {tool.name}: {tool.description}")

            # Test 1: Submit permit application
            print("\n" + "=" * 60)
            print("Test 1: Submit Permit Application")
            print("=" * 60)
            result = await session.call_tool(
                "submit_permit_application",
                arguments={
                    "applicant_name": "John Doe",
                    "property_address": "123 Main St, Los Angeles, CA 90001",
                    "work_description": "Kitchen remodel with new electrical and plumbing",
                    "estimated_cost": 25000.00,
                },
            )
            print(f"Result: {result.content}")

            # Test 2: Check permit status
            print("\n" + "=" * 60)
            print("Test 2: Check Permit Status")
            print("=" * 60)
            result = await session.call_tool(
                "check_permit_status",
                arguments={"permit_number": "PERMIT-ABC12345"},
            )
            print(f"Result: {result.content}")

            # Test 3: Schedule inspection
            print("\n" + "=" * 60)
            print("Test 3: Schedule Inspection")
            print("=" * 60)
            result = await session.call_tool(
                "schedule_inspection",
                arguments={
                    "permit_number": "PERMIT-ABC12345",
                    "inspection_type": "foundation",
                    "requested_date": "2026-02-15",
                    "contact_name": "Jane Smith",
                    "contact_phone": "555-0123",
                },
            )
            print(f"Result: {result.content}")

            # Test 4: Report violation
            print("\n" + "=" * 60)
            print("Test 4: Report Code Violation")
            print("=" * 60)
            result = await session.call_tool(
                "report_violation",
                arguments={
                    "property_address": "456 Oak Ave, Los Angeles, CA 90002",
                    "violation_type": "unpermitted_construction",
                    "description": "Addition built on property without permits",
                    "reporter_name": "Anonymous Neighbor",
                },
            )
            print(f"Result: {result.content}")

            print("\n" + "=" * 60)
            print("All tests completed successfully!")
            print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_client())
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback

        traceback.print_exc()