"""LADWP (Los Angeles Department of Water and Power) MCP Server."""

import asyncio
from typing import List

from fastmcp import FastMCP

from src.tools import LADWPTools

# Initialize FastMCP server
mcp = FastMCP("LADWP")

# Initialize tools
tools = LADWPTools()


@mcp.tool(title="Get Account Balance")
async def get_account_balance(account_number: str) -> str:
    """
    Check the current balance for a LADWP utility account.

    Args:
        account_number: The utility account number

    Returns:
        Account balance information including electricity and water balances
    """
    result = await tools.get_account_balance(account_number=account_number)
    return f"""Account Balance for {result["account_number"]}:
Account Holder: {result["account_holder_name"]}
Service Address: {result["service_address"]}
Electricity Balance: ${result["electricity_balance"]:.2f}
Water Balance: ${result["water_balance"]:.2f}
Total Balance Due: ${result["total_balance"]:.2f}
Due Date: {result["due_date"]}
Account Status: {result["status"]}"""


@mcp.tool(title="Get Bill History")
async def get_bill_history(account_number: str, months: int = 12) -> str:
    """
    Retrieve billing history for a LADWP utility account.

    Args:
        account_number: The utility account number
        months: Number of months of history to retrieve (default: 12)

    Returns:
        List of bills with usage and charges
    """
    result = await tools.get_bill_history(account_number=account_number, months=months)

    output = [f"Billing History for Account {result['account_number']} (Last {result['months_requested']} months):"]
    output.append("-" * 60)

    for bill in result["bills"]:
        output.append(f"""
Bill ID: {bill["bill_id"]}
Period: {bill["billing_period_start"]} to {bill["billing_period_end"]}
Electricity: {bill["electricity_usage_kwh"]:.2f} kWh - ${bill["electricity_charges"]:.2f}
Water: {bill["water_usage_gallons"]:.2f} gallons - ${bill["water_charges"]:.2f}
Total: ${bill["total_amount"]:.2f}
Due Date: {bill["due_date"]}
Status: {"Paid" if bill["paid"] else "Unpaid"}
""")

    return "\n".join(output)


@mcp.tool(title="Make Payment")
async def make_payment(
    account_number: str,
    amount: float,
    payment_method: str,
) -> str:
    """
    Submit a payment for a LADWP utility account.

    Args:
        account_number: The utility account number
        amount: Payment amount in USD
        payment_method: Payment method (credit_card, debit_card, bank_account, check)

    Returns:
        Payment confirmation with confirmation number
    """
    result = await tools.make_payment(
        account_number=account_number,
        amount=amount,
        payment_method=payment_method,
    )
    return f"""Payment Processed Successfully!
Payment ID: {result["payment_id"]}
Account Number: {result["account_number"]}
Amount: ${result["amount"]:.2f}
Payment Method: {result["payment_method"]}
Confirmation Number: {result["confirmation_number"]}
Date: {result["payment_date"]}
Status: {result["status"]}"""


@mcp.tool(title="Report Outage")
async def report_outage(
    address: str,
    outage_type: str,
    description: str,
) -> str:
    """
    Report a power or water outage to LADWP.

    Args:
        address: Address where the outage is occurring
        outage_type: Type of outage - "power" or "water"
        description: Detailed description of the outage

    Returns:
        Outage report confirmation with report ID
    """
    result = await tools.report_outage(
        address=address,
        outage_type=outage_type,
        description=description,
    )
    return f"""Outage Report Submitted Successfully!
Report ID: {result["report_id"]}
Address: {result["address"]}
Outage Type: {result["outage_type"]}
Status: {result["status"]}
Reported At: {result["reported_at"]}
Estimated Response Time: {result["estimated_response_time"]}
{result["message"]}"""


@mcp.tool(title="Check Outage Status")
async def check_outage_status(outage_id: str) -> str:
    """
    Check the status of a reported outage.

    Args:
        outage_id: The outage report ID

    Returns:
        Current status and estimated restoration time
    """
    result = await tools.check_outage_status(outage_id=outage_id)
    if "error" in result:
        return f"Error: {result['error']}"
    return f"""Outage Status for {result["outage_id"]}:
Address: {result["address"]}
Outage Type: {result["outage_type"]}
Status: {result["status"]}
Reported At: {result["reported_at"]}
Estimated Restoration: {result["estimated_restoration"]}
Crew Assigned: {"Yes" if result["crew_assigned"] else "No"}
Notes: {result["notes"]}"""


@mcp.tool(title="Request Service Start")
async def request_service_start(
    address: str,
    service_date: str,
    service_types: List[str],
) -> str:
    """
    Request to start new utility service at an address.

    Args:
        address: Service address
        service_date: Requested service start date (YYYY-MM-DD format)
        service_types: List of service types to start (e.g., ["electricity", "water"])

    Returns:
        Service start confirmation with new account number
    """
    result = await tools.request_service_start(
        address=address,
        service_date=service_date,
        service_types=service_types,
    )
    return f"""Service Start Request Submitted!
Request ID: {result["request_id"]}
New Account Number: {result["new_account_number"]}
Address: {result["address"]}
Service Date: {result["service_date"]}
Service Types: {", ".join(result["service_types"])}
Status: {result["status"]}
{result["message"]}"""


@mcp.tool(title="Request Service Stop")
async def request_service_stop(
    account_number: str,
    stop_date: str,
) -> str:
    """
    Request to stop utility service.

    Args:
        account_number: The utility account number
        stop_date: Requested service stop date (YYYY-MM-DD format)

    Returns:
        Service stop confirmation
    """
    result = await tools.request_service_stop(
        account_number=account_number,
        stop_date=stop_date,
    )
    return f"""Service Stop Request Submitted!
Request ID: {result["request_id"]}
Account Number: {result["account_number"]}
Stop Date: {result["stop_date"]}
Status: {result["status"]}
Final Bill Date: {result["final_bill_date"]}
{result["message"]}"""


@mcp.tool(title="Get Usage History")
async def get_usage_history(
    account_number: str,
    utility_type: str,
    months: int = 12,
) -> str:
    """
    Get historical usage data for electricity or water.

    Args:
        account_number: The utility account number
        utility_type: Type of utility - "electricity" or "water"
        months: Number of months of history to retrieve (default: 12)

    Returns:
        Usage history with amounts and costs
    """
    result = await tools.get_usage_history(
        account_number=account_number,
        utility_type=utility_type,
        months=months,
    )

    output = [f"Usage History for Account {result['account_number']}"]
    output.append(f"Utility Type: {result['utility_type'].capitalize()}")
    output.append(f"Period: Last {result['months_requested']} months")
    output.append("-" * 60)

    total_usage = 0
    total_cost = 0

    for record in result["usage_records"]:
        output.append(f"""
Period: {record["period_start"]} to {record["period_end"]}
Usage: {record["usage_amount"]:.2f} {record["usage_unit"]}
Cost: ${record["cost"]:.2f}""")
        total_usage += record["usage_amount"]
        total_cost += record["cost"]

    output.append("-" * 60)
    unit = result["usage_records"][0]["usage_unit"] if result["usage_records"] else ""
    output.append(f"Total Usage: {total_usage:.2f} {unit}")
    output.append(f"Total Cost: ${total_cost:.2f}")
    if result["usage_records"]:
        num_records = len(result["usage_records"])
        output.append(f"Average Monthly Usage: {total_usage / num_records:.2f} {unit}")
        output.append(f"Average Monthly Cost: ${total_cost / num_records:.2f}")

    return "\n".join(output)


if __name__ == "__main__":
    asyncio.run(mcp.run_http_async(host="0.0.0.0", port=8000))
