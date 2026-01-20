"""LADBS (Los Angeles Department of Building and Safety) MCP Server."""

from fastmcp import FastMCP
from src.tools import LADBSTools

# Initialize FastMCP server
mcp = FastMCP("LADBS")

# Initialize tools
tools = LADBSTools()


@mcp.tool()
async def submit_permit_application(
    applicant_name: str,
    property_address: str,
    work_description: str,
    estimated_cost: float,
) -> dict:
    """
    Submit a building permit application to LADBS.

    Args:
        applicant_name: Full name of the applicant
        property_address: Complete property address
        work_description: Detailed description of proposed work
        estimated_cost: Estimated cost in USD

    Returns:
        Application confirmation with permit number
    """
    return await tools.submit_permit_application(
        applicant_name=applicant_name,
        property_address=property_address,
        work_description=work_description,
        estimated_cost=estimated_cost,
    )


@mcp.tool()
async def check_permit_status(permit_number: str) -> dict:
    """
    Check the status of a building permit.

    Args:
        permit_number: The permit number to check

    Returns:
        Current permit status and details
    """
    return await tools.check_permit_status(permit_number=permit_number)


@mcp.tool()
async def schedule_inspection(
    permit_number: str,
    inspection_type: str,
    requested_date: str,
    contact_name: str,
    contact_phone: str,
) -> dict:
    """
    Schedule a building inspection.

    Args:
        permit_number: Permit number for the inspection
        inspection_type: Type of inspection (foundation, framing, final, etc.)
        requested_date: Requested date in YYYY-MM-DD format
        contact_name: Contact person's full name
        contact_phone: Contact phone number

    Returns:
        Inspection confirmation with details
    """
    return await tools.schedule_inspection(
        permit_number=permit_number,
        inspection_type=inspection_type,
        requested_date=requested_date,
        contact_name=contact_name,
        contact_phone=contact_phone,
    )


@mcp.tool()
async def report_violation(
    property_address: str,
    violation_type: str,
    description: str,
    reporter_name: str | None = None,
    reporter_contact: str | None = None,
) -> dict:
    """
    Report a building code violation.

    Args:
        property_address: Address where violation occurred
        violation_type: Type of violation
        description: Detailed description of the violation
        reporter_name: Reporter's name (optional, can be anonymous)
        reporter_contact: Reporter's contact info (optional)

    Returns:
        Violation report confirmation
    """
    return await tools.report_violation(
        property_address=property_address,
        violation_type=violation_type,
        description=description,
        reporter_name=reporter_name,
        reporter_contact=reporter_contact,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=8000))