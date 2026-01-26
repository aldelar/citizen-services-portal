"""Tests for LADBS MCP tools."""

import pytest
from datetime import datetime
from src.tools import LADBSTools


@pytest.fixture
def ladbs_tools():
    """Create LADBSTools instance for testing."""
    return LADBSTools()


@pytest.mark.asyncio
async def test_query_knowledge_base(ladbs_tools):
    """Test knowledge base query."""
    result = await ladbs_tools.queryKB(
        query="What are the requirements for electrical permits?",
        top=5
    )

    assert isinstance(result, dict)
    assert "query" in result
    assert "results" in result
    assert "total_results" in result
    assert len(result["results"]) > 0


@pytest.mark.asyncio
async def test_permits_search_by_number(ladbs_tools):
    """Test permit search by permit number."""
    result = await ladbs_tools.permits_search(
        permit_number="PERMIT-12345678"
    )

    assert isinstance(result, dict)
    assert "permits" in result
    assert "total_count" in result


@pytest.mark.asyncio
async def test_permits_search_by_address(ladbs_tools):
    """Test permit search by address."""
    result = await ladbs_tools.permits_search(
        address="123 Main St, Los Angeles, CA 90012"
    )

    assert isinstance(result, dict)
    assert "permits" in result
    assert "total_count" in result


@pytest.mark.asyncio
async def test_permits_submit(ladbs_tools):
    """Test permit submission."""
    result = await ladbs_tools.permits_submit(
        user_id="test-user-123",
        permit_type="electrical",
        address="123 Main St, Los Angeles, CA 90001",
        applicant_name="John Doe",
        applicant_email="john@example.com",
        applicant_phone="555-1234",
        work_description="Kitchen remodel",
        estimated_cost=15000.00,
        documents=["plan.pdf"],
        contractor_license="C10-123456"
    )

    assert isinstance(result, dict)
    assert result["success"] is True
    assert "permit_number" in result
    assert result["status"] == "submitted"


@pytest.mark.asyncio
async def test_permits_get_status(ladbs_tools):
    """Test permit status check."""
    result = await ladbs_tools.permits_getStatus(
        permit_number="PERMIT-12345678"
    )

    assert isinstance(result, dict)
    assert "permit_number" in result
    assert "status" in result


@pytest.mark.asyncio
async def test_inspections_scheduled(ladbs_tools):
    """Test viewing scheduled inspections."""
    result = await ladbs_tools.inspections_scheduled(
        permit_number="PERMIT-12345678"
    )

    assert isinstance(result, dict)
    assert "inspections" in result
    assert "total_count" in result


@pytest.mark.asyncio
async def test_inspections_schedule(ladbs_tools):
    """Test preparing inspection scheduling materials."""
    result = await ladbs_tools.inspections_schedule(
        permit_number="PERMIT-12345678",
        inspection_type="rough_electrical",
        address="123 Main St, Los Angeles, CA 90012",
        contact_name="Jane Smith",
        contact_phone="555-0123"
    )

    assert isinstance(result, dict)
    assert result["requires_user_action"] is True
    assert result["action_type"] == "phone_call"
    assert "prepared_materials" in result
    assert "on_complete" in result

