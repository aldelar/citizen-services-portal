"""LADBS (Los Angeles Department of Building and Safety) MCP Server."""

import asyncio
import json
import logging
from typing import List, Optional

from fastmcp import FastMCP

from src.tools import LADBSTools

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

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
    Search LADBS (Los Angeles Department of Building and Safety) knowledge base for permit requirements, fees, processes.

    Args:
        query: Natural language query
        top: Number of results to return (default 5)

    Returns:
        KnowledgeResult with matching document chunks
    """
    logger.info(f"[LADBS] 🔧 queryKB(query=\"{query[:50]}...\", top={top})")
    result = await tools.queryKB(query=query, top=top)
    logger.info(f"[LADBS]    ↳ returned {result.get('total_results', 0)} results")
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
    logger.info(f"[LADBS] 🔧 permits_search(address=\"{address}\", permit_number=\"{permit_number}\")")
    result = await tools.permits_search(address=address, permit_number=permit_number)
    logger.info(f"[LADBS]    ↳ returned {len(result.get('permits', []))} permits")
    return json.dumps(result, indent=2)


@mcp.tool(title="Submit Permit Application")
async def permits_submit(
    user_id: str,
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
        user_id: User ID (required for creating permit in CosmosDB)
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
    logger.info(f"[LADBS] 🔧 permits_submit(type=\"{permit_type}\", address=\"{address}\", user_id=\"{user_id}\")")
    result = await tools.permits_submit(
        user_id=user_id,
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
    logger.info(f"[LADBS]    ↳ created permit {result.get('permit_number', 'N/A')}")
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
    logger.info(f"[LADBS] 🔧 permits_getStatus(permit_number=\"{permit_number}\")")
    result = await tools.permits_getStatus(permit_number=permit_number)
    logger.info(f"[LADBS]    ↳ status: {result.get('status', 'N/A')}")
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
    logger.info(f"[LADBS] 🔧 inspections_scheduled(permit=\"{permit_number}\", address=\"{address}\")")
    result = await tools.inspections_scheduled(permit_number=permit_number, address=address)
    logger.info(f"[LADBS]    ↳ returned {len(result.get('inspections', []))} inspections")
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
    logger.info(f"[LADBS] 🔧 inspections_schedule(permit=\"{permit_number}\", type=\"{inspection_type}\")")
    result = await tools.inspections_schedule(
        permit_number=permit_number,
        inspection_type=inspection_type,
        address=address,
        contact_name=contact_name,
        contact_phone=contact_phone,
    )
    logger.info(f"[LADBS]    ↳ prepared user action: {result.get('action_type', 'N/A')}")
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "8000"))
    # Use streamable-http transport with stateless_http=True for scalability
    # stateless mode creates fresh transport per request, avoiding session timeout issues
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=port, transport="streamable-http", stateless_http=True))
