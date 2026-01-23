"""Tests for LASAN MCP tools."""

import pytest
from datetime import datetime
from src.tools import LASANTools


@pytest.fixture
def lasan_tools():
    """Create LASANTools instance for testing."""
    return LASANTools()


@pytest.mark.asyncio
async def test_get_collection_schedule(lasan_tools):
    """Test retrieving collection schedule."""
    result = await lasan_tools.get_collection_schedule("123 Main St, Los Angeles, CA")

    assert "address" in result
    assert "trash_day" in result
    assert "recycling_day" in result
    assert "green_waste_day" in result
    assert "error" not in result


@pytest.mark.asyncio
async def test_schedule_bulky_pickup(lasan_tools):
    """Test scheduling bulky item pickup."""
    result = await lasan_tools.schedule_bulky_pickup(
        address="123 Main St, Los Angeles, CA",
        contact_name="John Doe",
        contact_phone="555-1234",
        items=["sofa", "mattress"],
        preferred_date="2026-02-15"
    )

    assert "request_id" in result
    assert result.get("success") is True
    assert "scheduled_date" in result


@pytest.mark.asyncio
async def test_check_pickup_status(lasan_tools):
    """Test checking pickup status."""
    result = await lasan_tools.check_pickup_status("BULKY-12345")

    assert "status" in result or "request_id" in result


@pytest.mark.asyncio
async def test_report_illegal_dumping(lasan_tools):
    """Test reporting illegal dumping."""
    result = await lasan_tools.report_illegal_dumping(
        location_address="456 Oak Ave, Los Angeles, CA",
        description="Large pile of construction debris",
        materials=["wood", "concrete", "metal"],
        reporter_name="Jane Smith",
        reporter_phone="555-5678"
    )

    assert "report_id" in result
    assert result.get("success") is True


@pytest.mark.asyncio
async def test_check_dumping_report_status(lasan_tools):
    """Test checking dumping report status."""
    result = await lasan_tools.check_dumping_report_status("DUMP-12345")

    assert "status" in result or "report_id" in result


@pytest.mark.asyncio
async def test_request_bin_replacement(lasan_tools):
    """Test requesting bin replacement."""
    result = await lasan_tools.request_bin_replacement(
        address="789 Pine St, Los Angeles, CA",
        bin_type="blue",
        reason="damaged",
        contact_name="Bob Johnson",
        contact_phone="555-9876"
    )

    assert "request_id" in result
    assert result.get("success") is True


@pytest.mark.asyncio
async def test_get_recycling_info(lasan_tools):
    """Test getting recycling information."""
    # Test general info
    result = await lasan_tools.get_recycling_info()
    assert isinstance(result, dict)
    assert "accepted_materials" in result or "general_guidelines" in result

    # Test specific material query
    result = await lasan_tools.get_recycling_info("plastic")
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_report_missed_collection(lasan_tools):
    """Test reporting missed collection."""
    result = await lasan_tools.report_missed_collection(
        address="321 Elm St, Los Angeles, CA",
        collection_type="recycling",
        scheduled_date="2026-01-20",
        contact_name="Alice Williams",
        contact_phone="555-4321"
    )

    assert "report_id" in result
    assert result.get("success") is True
