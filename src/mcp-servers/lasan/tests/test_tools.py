"""Tests for LASAN MCP tools."""

import pytest
from datetime import datetime
from src.tools import LASANTools


@pytest.fixture
def lasan_tools():
    """Create LASANTools instance for testing."""
    return LASANTools()


@pytest.mark.asyncio
async def test_queryKB(lasan_tools):
    """Test knowledge base query."""
    result = await lasan_tools.queryKB(
        query="How do I schedule a bulky item pickup?",
        top=5
    )

    assert isinstance(result, dict)
    assert "query" in result
    assert "results" in result
    assert "total_results" in result
    assert len(result["results"]) > 0


@pytest.mark.asyncio
async def test_pickup_scheduled(lasan_tools):
    """Test viewing scheduled pickups."""
    result = await lasan_tools.pickup_scheduled(
        address="123 Main St, Los Angeles, CA 90012"
    )

    assert isinstance(result, dict)
    assert "address" in result
    assert "pickups" in result
    assert "total_count" in result


@pytest.mark.asyncio
async def test_pickup_schedule(lasan_tools):
    """Test preparing pickup scheduling materials."""
    result = await lasan_tools.pickup_schedule(
        address="123 Main St, Los Angeles, CA 90012",
        pickup_type="bulky_item",
        items=["old sofa", "mattress"],
        contact_name="John Doe",
        contact_phone="555-1234"
    )

    assert isinstance(result, dict)
    assert result["requires_user_action"] is True
    assert result["action_type"] == "phone_call"
    assert result["target"] == "311"
    assert "prepared_materials" in result
    assert "on_complete" in result


@pytest.mark.asyncio
async def test_pickup_getEligibility(lasan_tools):
    """Test checking pickup eligibility."""
    result = await lasan_tools.pickup_getEligibility(
        address="123 Main St, Los Angeles, CA 90012",
        item_types=["old couch", "concrete", "old TV"]
    )

    assert isinstance(result, dict)
    assert "address" in result
    assert "eligible_items" in result
    assert "ineligible_items" in result
    assert "annual_limit" in result
    assert "collections_remaining" in result

    # Check that concrete is ineligible (construction debris)
    ineligible_types = [item["item_type"] for item in result["ineligible_items"]]
    assert "concrete" in ineligible_types

    # Check that old couch is eligible
    eligible_types = [item["item_type"] for item in result["eligible_items"]]
    assert "old couch" in eligible_types

    # Check that old TV is eligible as e-waste
    tv_item = next(
        (item for item in result["eligible_items"] if item["item_type"] == "old TV"),
        None
    )
    assert tv_item is not None
    assert tv_item["pickup_type"] == "ewaste"
