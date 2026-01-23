"""LASAN (Los Angeles Bureau of Sanitation) MCP Server."""

import asyncio
from typing import List

from fastmcp import FastMCP

from src.tools import LASANTools

# Initialize FastMCP server
mcp = FastMCP("LASAN")

# Initialize tools
tools = LASANTools()


@mcp.tool(title="Get Collection Schedule")
async def get_collection_schedule(address: str) -> str:
    """
    Get trash and recycling collection schedule for an address.

    Args:
        address: Street address to check

    Returns:
        Collection schedule with pickup days
    """
    result = await tools.get_collection_schedule(address=address)
    return f"""Collection Schedule for {result["address"]}:
Trash Collection: {result["trash_day"]}
Recycling Collection: {result["recycling_day"]}
Green Waste Collection: {result["green_waste_day"]}
Next Pickup: {result["next_pickup"]}

Holiday Schedule Adjustments:
{chr(10).join([f"- {adj['holiday']} ({adj['date']}): {adj['adjustment']}" for adj in result.get("holiday_adjustments", [])])}"""


@mcp.tool(title="Schedule Bulky Pickup")
async def schedule_bulky_pickup(
    address: str,
    contact_name: str,
    contact_phone: str,
    items: List[str],
    preferred_date: str,
    special_instructions: str = "",
) -> str:
    """
    Schedule a bulky item pickup (furniture, appliances, etc.).

    Args:
        address: Pickup address
        contact_name: Contact person name
        contact_phone: Contact phone number
        items: List of items to pick up (e.g., ["sofa", "mattress", "refrigerator"])
        preferred_date: Preferred pickup date (YYYY-MM-DD format)
        special_instructions: Any special instructions

    Returns:
        Pickup request confirmation with request ID
    """
    result = await tools.schedule_bulky_pickup(
        address=address,
        contact_name=contact_name,
        contact_phone=contact_phone,
        items=items,
        preferred_date=preferred_date,
        special_instructions=special_instructions,
    )
    return f"""Bulky Pickup Scheduled!
Request ID: {result["request_id"]}
Address: {result["address"]}
Contact: {result["contact_name"]} ({result["contact_phone"]})
Items: {", ".join(result["items"])}
Scheduled Date: {result["scheduled_date"]}
Status: {result["status"]}

{result["message"]}"""


@mcp.tool(title="Check Pickup Status")
async def check_pickup_status(request_id: str) -> str:
    """
    Check status of a bulky item pickup request.

    Args:
        request_id: The pickup request ID

    Returns:
        Current status of the pickup request
    """
    result = await tools.check_pickup_status(request_id=request_id)
    if "error" in result:
        return f"Error: {result['error']}"
    return f"""Pickup Status for {result["request_id"]}:
Status: {result["status"]}
Scheduled Date: {result.get("scheduled_date", "Not scheduled")}
Items: {", ".join(result["items"])}
Notes: {result.get("notes", "No additional notes")}"""


@mcp.tool(title="Report Illegal Dumping")
async def report_illegal_dumping(
    location_address: str,
    description: str,
    materials: List[str],
    reporter_name: str = "",
    reporter_phone: str = "",
) -> str:
    """
    Report illegal dumping at a location.

    Args:
        location_address: Address or location description where dumping occurred
        description: Description of the dumping
        materials: Types of materials dumped (e.g., ["construction debris", "furniture", "tires"])
        reporter_name: Optional reporter name
        reporter_phone: Optional reporter phone

    Returns:
        Report confirmation with report ID
    """
    result = await tools.report_illegal_dumping(
        location_address=location_address,
        description=description,
        materials=materials,
        reporter_name=reporter_name,
        reporter_phone=reporter_phone,
    )
    return f"""Illegal Dumping Report Submitted!
Report ID: {result["report_id"]}
Location: {result["location"]}
Materials: {", ".join(result["materials"])}
Status: {result["status"]}
Reported At: {result["reported_at"]}

{result["message"]}"""


@mcp.tool(title="Check Dumping Report Status")
async def check_dumping_report_status(report_id: str) -> str:
    """
    Check status of an illegal dumping report.

    Args:
        report_id: The report ID

    Returns:
        Current status of the report
    """
    result = await tools.check_dumping_report_status(report_id=report_id)
    if "error" in result:
        return f"Error: {result['error']}"
    return f"""Dumping Report Status for {result["report_id"]}:
Location: {result["location"]}
Status: {result["status"]}
Last Updated: {result["last_updated"]}
Notes: {result.get("notes", "No additional notes")}"""


@mcp.tool(title="Request Bin Replacement")
async def request_bin_replacement(
    address: str,
    bin_type: str,
    reason: str,
    contact_name: str,
    contact_phone: str,
) -> str:
    """
    Request replacement of a trash, recycling, or green waste bin.

    Args:
        address: Service address
        bin_type: Type of bin - "black" (trash), "blue" (recycling), or "green" (green waste)
        reason: Reason for replacement - "damaged", "missing", "stolen", or "wrong_size"
        contact_name: Contact person name
        contact_phone: Contact phone number

    Returns:
        Replacement request confirmation
    """
    result = await tools.request_bin_replacement(
        address=address,
        bin_type=bin_type,
        reason=reason,
        contact_name=contact_name,
        contact_phone=contact_phone,
    )
    return f"""Bin Replacement Request Submitted!
Request ID: {result["request_id"]}
Address: {result["address"]}
Bin Type: {result["bin_type"]}
Reason: {result["reason"]}
Status: {result["status"]}
Estimated Delivery: {result["estimated_delivery"]}

{result["message"]}"""


@mcp.tool(title="Get Recycling Info")
async def get_recycling_info(material: str = "") -> str:
    """
    Get recycling guidelines and information.

    Args:
        material: Optional specific material to check (e.g., "plastic", "glass", "electronics")

    Returns:
        Recycling guidelines and accepted materials
    """
    result = await tools.get_recycling_info(material=material)

    if "material_query" in result:
        # Specific material query
        output = [f"Recycling Information for: {result['material_query']}"]
        output.append("-" * 60)
        output.append(f"Accepted: {result.get('accepted', 'Unknown')}")
        output.append(f"\nDetails: {result.get('details', 'No details available')}")
        if result.get("special_notes"):
            output.append(f"\nSpecial Notes: {result['special_notes']}")
    else:
        # General guidelines
        output = ["Recycling Guidelines"]
        output.append("-" * 60)
        output.append("\nAccepted Materials:")
        for item in result.get("accepted_materials", []):
            output.append(f"  ✓ {item}")
        output.append("\nNOT Accepted:")
        for item in result.get("not_accepted", []):
            output.append(f"  ✗ {item}")
        output.append("\nPreparation Tips:")
        for tip in result.get("preparation_tips", []):
            output.append(f"  • {tip}")

    return "\n".join(output)


@mcp.tool(title="Report Missed Collection")
async def report_missed_collection(
    address: str,
    collection_type: str,
    scheduled_date: str,
    contact_name: str,
    contact_phone: str,
) -> str:
    """
    Report a missed trash or recycling collection.

    Args:
        address: Service address
        collection_type: Type of collection - "trash", "recycling", or "green_waste"
        scheduled_date: The date collection was supposed to occur (YYYY-MM-DD format)
        contact_name: Contact person name
        contact_phone: Contact phone number

    Returns:
        Report confirmation with follow-up information
    """
    result = await tools.report_missed_collection(
        address=address,
        collection_type=collection_type,
        scheduled_date=scheduled_date,
        contact_name=contact_name,
        contact_phone=contact_phone,
    )
    return f"""Missed Collection Report Submitted!
Report ID: {result["report_id"]}
Address: {result["address"]}
Collection Type: {result["collection_type"]}
Scheduled Date: {result["scheduled_date"]}
Status: {result["status"]}
Follow-up Date: {result["follow_up_date"]}

{result["message"]}"""


if __name__ == "__main__":
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=8000))
