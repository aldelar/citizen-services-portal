"""Tests for LADBS MCP tools."""

import pytest
from datetime import datetime
from src.tools import LADBSTools


@pytest.fixture
def ladbs_tools():
    """Create LADBSTools instance for testing."""
    return LADBSTools()


@pytest.mark.asyncio
async def test_submit_permit_application(ladbs_tools):
    """Test permit application submission."""
    result = await ladbs_tools.submit_permit_application(
        applicant_name="John Doe",
        property_address="123 Main St, Los Angeles, CA 90001",
        work_description="Kitchen remodel",
        estimated_cost=15000.00,
    )

    assert result["success"] is True
    assert "permit_number" in result
    assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_check_permit_status(ladbs_tools):
    """Test permit status check."""
    result = await ladbs_tools.check_permit_status("PERMIT-12345678")

    assert "permit_number" in result
    assert "status" in result


@pytest.mark.asyncio
async def test_schedule_inspection(ladbs_tools):
    """Test inspection scheduling."""
    result = await ladbs_tools.schedule_inspection(
        permit_number="PERMIT-12345678",
        inspection_type="foundation",
        requested_date="2026-02-01",
        contact_name="Jane Smith",
        contact_phone="555-0123",
    )

    assert result["success"] is True
    assert "inspection_id" in result


@pytest.mark.asyncio
async def test_report_violation(ladbs_tools):
    """Test violation reporting."""
    result = await ladbs_tools.report_violation(
        property_address="456 Oak Ave, Los Angeles, CA 90002",
        violation_type="unpermitted_construction",
        description="Addition built without permits",
        reporter_name="Anonymous",
    )

    assert result["success"] is True
    assert "report_id" in result
    assert result["status"] == "submitted"
