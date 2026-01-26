"""Tests for LADWP MCP tools."""

import pytest
from datetime import datetime
from src.tools import LADWPTools


@pytest.fixture
def ladwp_tools():
    """Create LADWPTools instance for testing."""
    return LADWPTools()


@pytest.mark.asyncio
async def test_queryKB(ladwp_tools):
    """Test knowledge base query."""
    result = await ladwp_tools.queryKB(
        query="What are the LADWP time-of-use rate plans?",
        top=5
    )

    assert isinstance(result, dict)
    assert "query" in result
    assert "results" in result
    assert "total_results" in result
    assert len(result["results"]) > 0


@pytest.mark.asyncio
async def test_account_show(ladwp_tools):
    """Test account information retrieval."""
    result = await ladwp_tools.account_show(
        account_number="123456789"
    )

    assert isinstance(result, dict)
    assert "account_number" in result
    assert "current_rate_plan" in result
    assert "service_address" in result


@pytest.mark.asyncio
async def test_plans_list(ladwp_tools):
    """Test rate plan listing."""
    result = await ladwp_tools.plans_list(
        account_number="123456789"
    )

    assert isinstance(result, dict)
    assert "current_plan" in result
    assert "available_plans" in result
    assert len(result["available_plans"]) > 0


@pytest.mark.asyncio
async def test_tou_enroll(ladwp_tools):
    """Test TOU enrollment."""
    result = await ladwp_tools.tou_enroll(
        account_number="123456789",
        rate_plan="TOU-D-PRIME"
    )

    assert isinstance(result, dict)
    assert result["success"] is True
    assert "confirmation_number" in result
    assert "effective_date" in result


@pytest.mark.asyncio
async def test_interconnection_submit(ladwp_tools):
    """Test interconnection submission."""
    result = await ladwp_tools.interconnection_submit(
        address="123 Solar St, Los Angeles, CA 90012",
        system_size_kw=8.5,
        applicant_name="John Doe",
        applicant_email="john@example.com",
        battery_size_kwh=13.5,
        inverter="SolarEdge SE7600H",
        panels="LG NeON 2 400W x 20",
        battery="Tesla Powerwall 2"
    )

    assert isinstance(result, dict)
    assert result["requires_user_action"] is True
    assert result["action_type"] == "email"
    assert "prepared_materials" in result
    assert "on_complete" in result


@pytest.mark.asyncio
async def test_interconnection_getStatus(ladwp_tools):
    """Test interconnection status check."""
    result = await ladwp_tools.interconnection_getStatus(
        application_id="IA-2026-12345"
    )

    assert isinstance(result, dict)
    assert "status" in result
    assert "address" in result


@pytest.mark.asyncio
async def test_rebates_filed(ladwp_tools):
    """Test rebates filed listing."""
    result = await ladwp_tools.rebates_filed(
        account_number="123456789"
    )

    assert isinstance(result, dict)
    assert "applications" in result
    assert "total_count" in result


@pytest.mark.asyncio
async def test_rebates_apply(ladwp_tools):
    """Test rebate application submission."""
    result = await ladwp_tools.rebates_apply(
        account_number="123456789",
        equipment_type="heat_pump_hvac",
        equipment_details="Mitsubishi 3-zone ductless, 3 tons",
        purchase_date="2026-01-15",
        invoice_total=12500.00,
        ahri_certificate="AHRI-12345678",
        ladbs_permit_number="PERMIT-2026-001234"
    )

    assert isinstance(result, dict)
    assert result["success"] is True
    assert "application_id" in result
    assert "estimated_rebate" in result


@pytest.mark.asyncio
async def test_rebates_getStatus(ladwp_tools):
    """Test rebate status check."""
    result = await ladwp_tools.rebates_getStatus(
        application_id="CRP-2026-1234"
    )

    assert isinstance(result, dict)
    assert "status" in result
    assert "application_id" in result
