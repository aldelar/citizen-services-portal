"""LASAN (Los Angeles Bureau of Sanitation) MCP Server."""

import asyncio
import json
import logging
from typing import List

from fastmcp import FastMCP

from src.tools import LASANTools

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("LASAN")

# Initialize tools
tools = LASANTools()


@mcp.tool(title="Query Knowledge Base")
async def queryKB(
    query: str,
    top: int = 5,
) -> str:
    """
    Search LASAN knowledge base for disposal guidelines, recycling info.

    Args:
        query: Natural language query
        top: Number of results to return (default 5)

    Returns:
        KnowledgeResult with matching document chunks
    """
    logger.info(f"[LASAN] 🔧 queryKB(query=\"{query[:50]}...\", top={top})")
    result = await tools.queryKB(query=query, top=top)
    logger.info(f"[LASAN]    ↳ returned {result.get('total_results', 0)} results")
    return json.dumps(result, indent=2)


@mcp.tool(title="View Scheduled Pickups")
async def pickup_scheduled(
    address: str,
) -> str:
    """
    View scheduled pickups for an address.

    Args:
        address: Street address to check

    Returns:
        PickupScheduledResult with scheduled pickups
    """
    logger.info(f"[LASAN] 🔧 pickup_scheduled(address=\"{address}\")")
    result = await tools.pickup_scheduled(address=address)
    logger.info(f"[LASAN]    ↳ returned {len(result.get('pickups', []))} pickups")
    return json.dumps(result, indent=2)


@mcp.tool(title="Schedule Pickup")
async def pickup_schedule(
    address: str,
    pickup_type: str,
    items: List[str],
    contact_name: str,
    contact_phone: str,
) -> str:
    """
    Prepare pickup scheduling request (requires user action - 311 call or MyLA311 app).

    Args:
        address: Pickup address
        pickup_type: Type of pickup (bulky_item, ewaste, hazardous)
        items: List of items to pick up
        contact_name: Contact person's name
        contact_phone: Contact phone number

    Returns:
        UserActionResponse with phone script and checklist
    """
    logger.info(f"[LASAN] 🔧 pickup_schedule(address=\"{address}\", type=\"{pickup_type}\", items={len(items)})")
    result = await tools.pickup_schedule(
        address=address,
        pickup_type=pickup_type,
        items=items,
        contact_name=contact_name,
        contact_phone=contact_phone,
    )
    logger.info(f"[LASAN]    ↳ prepared user action: {result.get('action_type', 'N/A')}")
    return json.dumps(result, indent=2)


@mcp.tool(title="Check Pickup Eligibility")
async def pickup_getEligibility(
    address: str,
    item_types: List[str],
) -> str:
    """
    Check what items are eligible for pickup at an address.

    Args:
        address: Street address
        item_types: List of items to check eligibility for

    Returns:
        EligibilityResult with eligible/ineligible items and alternatives
    """
    logger.info(f"[LASAN] 🔧 pickup_getEligibility(address=\"{address}\", items={item_types})")
    result = await tools.pickup_getEligibility(address=address, item_types=item_types)
    logger.info(f"[LASAN]    ↳ eligible: {len(result.get('eligible', []))}, ineligible: {len(result.get('ineligible', []))}")
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "8000"))
    # Use streamable-http transport for compatibility with agent-framework MCPStreamableHTTPTool
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=port, transport="streamable-http"))
