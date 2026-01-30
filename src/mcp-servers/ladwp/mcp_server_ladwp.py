"""LADWP (Los Angeles Department of Water and Power) MCP Server."""

import asyncio
import json
import logging
from typing import List, Optional

from fastmcp import FastMCP

from src.tools import LADWPTools

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("LADWP")

# Initialize tools
tools = LADWPTools()


@mcp.tool(title="Query Knowledge Base")
async def queryKB(
    query: str,
    top: int = 5,
) -> str:
    """
    Search LADWP (Los Angeles Department of Water and Power) knowledge base for rate plans, rebates, solar programs.

    Args:
        query: Natural language query
        top: Number of results to return (default 5)

    Returns:
        KnowledgeResult with matching document chunks
    """
    logger.info(f"[LADWP] 🔧 queryKB(query=\"{query[:50]}...\", top={top})")
    result = await tools.queryKB(query=query, top=top)
    logger.info(f"[LADWP]    ↳ returned {result.get('total_results', 0)} results")
    return json.dumps(result, indent=2)


@mcp.tool(title="Show Account")
async def account_show(
    account_number: str,
) -> str:
    """
    Get current account information including rate plan and pending requests.

    Args:
        account_number: The utility account number

    Returns:
        Account information with rate plan, meter type, and pending requests
    """
    logger.info(f"[LADWP] 🔧 account_show(account=\"{account_number}\")")
    result = await tools.account_show(account_number=account_number)
    logger.info(f"[LADWP]    ↳ account status: {result.get('status', 'N/A')}")
    return json.dumps(result, indent=2)


@mcp.tool(title="List Rate Plans")
async def plans_list(
    account_number: str,
) -> str:
    """
    List available LADWP (Los Angeles Department of Water and Power) rate plans.

    Args:
        account_number: The utility account number, aka user_id

    Returns:
        PlansListResult with available plans and recommendation
    """
    logger.info(f"[LADWP] 🔧 plans_list(account=\"{account_number}\")")
    result = await tools.plans_list(account_number=account_number)
    logger.info(f"[LADWP]    ↳ returned {len(result.get('available_plans', []))} plans")
    return json.dumps(result, indent=2)


@mcp.tool(title="Enroll in Time-of-Use Plan")
async def tou_enroll(
    account_number: str,
    rate_plan: str,
) -> str:
    """
    Enroll in a Time-of-Use rate plan.

    Args:
        account_number: The utility account number
        rate_plan: Rate plan to enroll in (TOU-D-A, TOU-D-B, TOU-D-PRIME)

    Returns:
        TOUEnrollmentResult with confirmation and effective date
    """
    logger.info(f"[LADWP] 🔧 tou_enroll(account=\"{account_number}\", plan=\"{rate_plan}\")")
    result = await tools.tou_enroll(account_number=account_number, rate_plan=rate_plan)
    logger.info(f"[LADWP]    ↳ enrollment: {result.get('confirmation_number', 'N/A')}")
    return json.dumps(result, indent=2)


@mcp.tool(title="Submit Solar Interconnection")
async def interconnection_submit(
    address: str,
    system_size_kw: float,
    applicant_name: str,
    applicant_email: str,
    battery_size_kwh: Optional[float] = None,
    inverter: Optional[str] = None,
    panels: Optional[str] = None,
    battery: Optional[str] = None,
) -> str:
    """
    Prepare solar interconnection application (requires user action - email submission).

    Args:
        address: Service address
        system_size_kw: Solar system size in kW
        applicant_name: Applicant's name
        applicant_email: Applicant's email
        battery_size_kwh: Battery size in kWh (optional)
        inverter: Inverter model (optional)
        panels: Panel specifications (optional)
        battery: Battery model (optional)

    Returns:
        UserActionResponse with email draft and checklist
    """
    logger.info(f"[LADWP] 🔧 interconnection_submit(address=\"{address}\", size={system_size_kw}kW)")
    result = await tools.interconnection_submit(
        address=address,
        system_size_kw=system_size_kw,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        battery_size_kwh=battery_size_kwh,
        inverter=inverter,
        panels=panels,
        battery=battery,
    )
    logger.info(f"[LADWP]    ↳ prepared user action: {result.get('action_type', 'N/A')}")
    return json.dumps(result, indent=2)


@mcp.tool(title="Get Interconnection Status")
async def interconnection_getStatus(
    application_id: Optional[str] = None,
    address: Optional[str] = None,
) -> str:
    """
    Check interconnection application status.

    Args:
        application_id: Interconnection application ID
        address: Service address (alternative to application_id)

    Returns:
        Interconnection status with next steps
    """
    logger.info(f"[LADWP] 🔧 interconnection_getStatus(app_id=\"{application_id}\", address=\"{address}\")")
    result = await tools.interconnection_getStatus(application_id=application_id, address=address)
    logger.info(f"[LADWP]    ↳ status: {result.get('status', 'N/A')}")
    return json.dumps(result, indent=2)


@mcp.tool(title="List Filed Rebates")
async def rebates_filed(
    account_number: str,
) -> str:
    """
    List all rebate applications for an account.

    Args:
        account_number: The utility account number aka user_id

    Returns:
        RebatesFiledResult with all applications and their status
    """
    logger.info(f"[LADWP] 🔧 rebates_filed(account=\"{account_number}\")")
    result = await tools.rebates_filed(account_number=account_number)
    logger.info(f"[LADWP]    ↳ returned {len(result.get('applications', []))} rebates")
    return json.dumps(result, indent=2)


@mcp.tool(title="Apply for Rebate")
async def rebates_apply(
    account_number: str,
    equipment_type: str,
    equipment_details: str,
    purchase_date: str,
    invoice_total: float,
    ahri_certificate: str,
    ladbs_permit_number: str,
) -> str:
    """
    Submit a rebate application.

    Args:
        account_number: The utility account number
        equipment_type: Type of equipment (heat_pump_hvac, heat_pump_water_heater, smart_thermostat)
        equipment_details: Equipment make, model, specs
        purchase_date: Date of purchase (YYYY-MM-DD)
        invoice_total: Total invoice amount
        ahri_certificate: AHRI certificate number
        ladbs_permit_number: LADBS permit number

    Returns:
        RebateApplyResult with application ID and estimated rebate
    """
    logger.info(f"[LADWP] 🔧 rebates_apply(account=\"{account_number}\", type=\"{equipment_type}\")")
    result = await tools.rebates_apply(
        account_number=account_number,
        equipment_type=equipment_type,
        equipment_details=equipment_details,
        purchase_date=purchase_date,
        invoice_total=invoice_total,
        ahri_certificate=ahri_certificate,
        ladbs_permit_number=ladbs_permit_number,
    )
    logger.info(f"[LADWP]    ↳ application: {result.get('application_id', 'N/A')}")
    return json.dumps(result, indent=2)


@mcp.tool(title="Get Rebate Status")
async def rebates_getStatus(
    application_id: str,
) -> str:
    """
    Get detailed status of a specific rebate application.

    Args:
        application_id: The rebate application ID

    Returns:
        RebateApplication with detailed status
    """
    logger.info(f"[LADWP] 🔧 rebates_getStatus(app_id=\"{application_id}\")")
    result = await tools.rebates_getStatus(application_id=application_id)
    logger.info(f"[LADWP]    ↳ status: {result.get('status', 'N/A')}")
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", "8000"))
    # Use streamable-http transport with stateless_http=True for scalability
    # stateless mode creates fresh transport per request, avoiding session timeout issues
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=port, transport="streamable-http", stateless_http=True))
