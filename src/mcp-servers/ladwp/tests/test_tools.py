"""Tests for LADWP MCP tools."""

import pytest
from datetime import datetime
from src.tools import LADWPTools


@pytest.fixture
def ladwp_tools():
    """Create LADWPTools instance for testing."""
    return LADWPTools()


@pytest.mark.asyncio
async def test_get_account_balance(ladwp_tools):
    """Test retrieving account balance."""
    result = await ladwp_tools.get_account_balance("123456789")

    assert "balance" in result or "account_number" in result
    assert "error" not in result


@pytest.mark.asyncio
async def test_get_bill_history(ladwp_tools):
    """Test retrieving billing history."""
    result = await ladwp_tools.get_bill_history("123456789", months=6)

    assert isinstance(result, dict)
    assert "account_number" in result
    assert "bills" in result


@pytest.mark.asyncio
async def test_make_payment(ladwp_tools):
    """Test submitting a payment."""
    result = await ladwp_tools.make_payment("123456789", 150.00, "credit_card")

    assert "confirmation" in result or "payment_id" in result
    assert result.get("success") is True


@pytest.mark.asyncio
async def test_report_outage(ladwp_tools):
    """Test reporting an outage."""
    result = await ladwp_tools.report_outage(
        address="123 Main St, Los Angeles, CA",
        outage_type="power",
        description="No power since 3pm"
    )

    assert "report_id" in result
    assert result.get("success") is True


@pytest.mark.asyncio
async def test_check_outage_status(ladwp_tools):
    """Test checking outage status."""
    result = await ladwp_tools.check_outage_status("OUT-12345")

    assert "status" in result or "outage_id" in result


@pytest.mark.asyncio
async def test_request_service_start(ladwp_tools):
    """Test starting new service."""
    result = await ladwp_tools.request_service_start(
        address="456 Oak Ave, Los Angeles, CA",
        service_date="2026-02-01",
        service_types=["electricity", "water"]
    )

    assert "request_id" in result
    assert result.get("success") is True


@pytest.mark.asyncio
async def test_request_service_stop(ladwp_tools):
    """Test stopping service."""
    result = await ladwp_tools.request_service_stop("123456789", "2026-02-15")

    assert "request_id" in result
    assert result.get("success") is True


@pytest.mark.asyncio
async def test_get_usage_history(ladwp_tools):
    """Test retrieving usage history."""
    result = await ladwp_tools.get_usage_history("123456789", "electricity", months=12)

    assert isinstance(result, dict)
    assert "account_number" in result
    assert "usage_records" in result
