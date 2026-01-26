"""LADBS (Los Angeles Department of Building and Safety) MCP Server."""

import asyncio
import json
from typing import List, Optional

from fastmcp import FastMCP

from src.tools import LADBSTools

# Initialize FastMCP server
mcp = FastMCP("LADBS")

# Initialize tools
tools = LADBSTools()


@mcp.tool(title="Query Knowledge Base")
async def queryKB(
    query: str,
    top: int = 5,
) -> str:
    """
    Search LADBS knowledge base for permit requirements, fees, processes.

    Args:
        query: Natural language query
        top: Number of results to return (default 5)

    Returns:
        KnowledgeResult with matching document chunks
    """
    result = await tools.queryKB(query=query, top=top)
    return json.dumps(result, indent=2)


@mcp.tool(title="Search Permits")
async def permits_search(
    address: Optional[str] = None,
    permit_number: Optional[str] = None,
) -> str:
    """
    Find existing permits by address or permit number.

    Args:
        address: Property address to search
        permit_number: Specific permit number to look up

    Returns:
        PermitSearchResult with matching permits
    """
    result = await tools.permits_search(address=address, permit_number=permit_number)
    return json.dumps(result, indent=2)


@mcp.tool(title="Submit Permit Application")
async def permits_submit(
    permit_type: str,
    address: str,
    applicant_name: str,
    applicant_email: str,
    applicant_phone: str,
    work_description: str,
    estimated_cost: float,
    documents: List[str],
    contractor_license: Optional[str] = None,
) -> str:
    """
    Submit a new permit application.

    Args:
        permit_type: Type of permit (electrical, mechanical, building, plumbing)
        address: Property address
        applicant_name: Applicant's name
        applicant_email: Applicant's email
        applicant_phone: Applicant's phone number
        work_description: Description of the proposed work
        estimated_cost: Estimated cost of the work
        documents: List of document references/URLs
        contractor_license: Contractor license number (optional)

    Returns:
        PermitSubmitResult with permit number and next steps
    """
    result = await tools.permits_submit(
        permit_type=permit_type,
        address=address,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        applicant_phone=applicant_phone,
        work_description=work_description,
        estimated_cost=estimated_cost,
        documents=documents,
        contractor_license=contractor_license,
    )
    return json.dumps(result, indent=2)


@mcp.tool(title="Get Permit Status")
async def permits_getStatus(
    permit_number: str,
) -> str:
    """
    Check the current status of a permit.

    Args:
        permit_number: Permit number to check

    Returns:
        Permit with current status and next steps
    """
    result = await tools.permits_getStatus(permit_number=permit_number)
    return json.dumps(result, indent=2)


@mcp.tool(title="View Scheduled Inspections")
async def inspections_scheduled(
    permit_number: Optional[str] = None,
    address: Optional[str] = None,
) -> str:
    """
    View scheduled inspections for a permit or address.

    Args:
        permit_number: Permit number to look up inspections for
        address: Address to look up inspections for

    Returns:
        InspectionListResult with scheduled inspections
    """
    result = await tools.inspections_scheduled(permit_number=permit_number, address=address)
    return json.dumps(result, indent=2)


@mcp.tool(title="Schedule Inspection")
async def inspections_schedule(
    permit_number: str,
    inspection_type: str,
    address: str,
    contact_name: str,
    contact_phone: str,
) -> str:
    """
    Prepare materials for scheduling an inspection (requires user action - phone call to 311).

    Args:
        permit_number: Permit number for the inspection
        inspection_type: Type of inspection (rough_electrical, final_electrical, etc.)
        address: Property address
        contact_name: Contact person's name
        contact_phone: Contact phone number

    Returns:
        UserActionResponse with phone script and checklist
    """
    result = await tools.inspections_schedule(
        permit_number=permit_number,
        inspection_type=inspection_type,
        address=address,
        contact_name=contact_name,
        contact_phone=contact_phone,
    )
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "8000"))
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=port))
