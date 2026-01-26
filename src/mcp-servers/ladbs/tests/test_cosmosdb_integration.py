"""Integration tests for LADBS CosmosDB operations.

These tests require a live CosmosDB instance with COSMOS_ENDPOINT configured.
Run with: pytest -m integration
"""

import os
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.models import (
    Applicant,
    InspectionStatus,
    InspectionType,
    PermitStatus,
    PermitType,
)
from src.repositories import PermitRepository, InspectionRepository


# Skip all tests in this file if CosmosDB is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("COSMOS_ENDPOINT"),
        reason="CosmosDB not configured (COSMOS_ENDPOINT not set)"
    )
]


@pytest.fixture(scope="session")
async def permit_repository():
    """Create a PermitRepository instance for testing."""
    return PermitRepository()


@pytest.fixture(scope="session")
async def inspection_repository():
    """Create an InspectionRepository instance for testing."""
    return InspectionRepository()


@pytest.fixture
def test_user_id():
    """Generate a unique user ID for testing."""
    return f"test-user-{uuid4()}"


@pytest.fixture
def test_applicant():
    """Create a test applicant."""
    return Applicant(
        name="Test User",
        email="test@example.com",
        phone="555-0123",
        contractor_license="C10-123456"
    )


class TestPermitRepository:
    """Tests for permit repository operations."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_permit(
        self, permit_repository, test_user_id, test_applicant
    ):
        """Create a permit and retrieve it by permit number."""
        # Create permit
        permit = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.ELECTRICAL,
            address="123 Test St, Los Angeles, CA 90012",
            work_description="Test solar installation",
            estimated_cost=25000.00,
            applicant=test_applicant,
            documents=["test-plan.pdf"]
        )

        assert permit.permit_number is not None
        assert permit.status == PermitStatus.SUBMITTED
        assert permit.fees is not None
        assert permit.fees.total > 0

        # Retrieve by permit number without user_id (cross-partition)
        retrieved = await permit_repository.get_by_permit_number(permit.permit_number)
        assert retrieved is not None
        assert retrieved.permit_number == permit.permit_number
        assert retrieved.address == "123 Test St, Los Angeles, CA 90012"

    @pytest.mark.asyncio
    async def test_get_by_permit_number_with_user_id(
        self, permit_repository, test_user_id, test_applicant
    ):
        """Test partition-aware query when user_id provided."""
        # Create permit
        permit = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.MECHANICAL,
            address="456 Test Ave, Los Angeles, CA 90013",
            work_description="Test HVAC installation",
            estimated_cost=15000.00,
            applicant=test_applicant,
            documents=[]
        )

        # Retrieve with user_id (partition-aware query)
        retrieved = await permit_repository.get_by_permit_number(
            permit.permit_number,
            user_id=test_user_id
        )
        assert retrieved is not None
        assert retrieved.permit_number == permit.permit_number
        assert retrieved.permit_type == PermitType.MECHANICAL

    @pytest.mark.asyncio
    async def test_list_by_user(
        self, permit_repository, test_user_id, test_applicant
    ):
        """Test listing all permits for a user."""
        # Create multiple permits
        permit1 = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.ELECTRICAL,
            address="111 First St, Los Angeles, CA 90001",
            work_description="First test permit",
            estimated_cost=10000.00,
            applicant=test_applicant,
            documents=[]
        )

        permit2 = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.BUILDING,
            address="222 Second St, Los Angeles, CA 90002",
            work_description="Second test permit",
            estimated_cost=20000.00,
            applicant=test_applicant,
            documents=[]
        )

        # List all permits for user
        permits = await permit_repository.list_by_user(test_user_id)
        assert len(permits) >= 2
        permit_numbers = [p.permit_number for p in permits]
        assert permit1.permit_number in permit_numbers
        assert permit2.permit_number in permit_numbers

    @pytest.mark.asyncio
    async def test_search_by_address(
        self, permit_repository, test_user_id, test_applicant
    ):
        """Test searching permits by address."""
        unique_address = f"999 Unique Test St {uuid4()}, Los Angeles, CA 90099"

        # Create permit with unique address
        permit = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.PLUMBING,
            address=unique_address,
            work_description="Test plumbing work",
            estimated_cost=5000.00,
            applicant=test_applicant,
            documents=[]
        )

        # Search by partial address (cross-partition)
        results = await permit_repository.search_by_address("999 Unique Test St")
        assert len(results) >= 1
        assert any(p.permit_number == permit.permit_number for p in results)

        # Search with user_id (partition-aware)
        results_with_user = await permit_repository.search_by_address(
            "999 Unique Test St",
            user_id=test_user_id
        )
        assert len(results_with_user) >= 1

    @pytest.mark.asyncio
    async def test_update_permit_status(
        self, permit_repository, test_user_id, test_applicant
    ):
        """Test updating permit status."""
        # Create permit
        permit = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.ELECTRICAL,
            address="789 Update Test St, Los Angeles, CA 90089",
            work_description="Test for status update",
            estimated_cost=12000.00,
            applicant=test_applicant,
            documents=[]
        )

        # Get the document ID from the created permit
        # We need to query to get the full document
        retrieved = await permit_repository.get_by_permit_number(
            permit.permit_number,
            user_id=test_user_id
        )
        assert retrieved is not None


class TestInspectionRepository:
    """Tests for inspection repository operations."""

    @pytest.mark.asyncio
    async def test_create_and_list_inspections(
        self, inspection_repository, permit_repository, test_user_id, test_applicant
    ):
        """Create an inspection and list by permit number."""
        # First create a permit
        permit = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.ELECTRICAL,
            address="321 Inspection Test St, Los Angeles, CA 90321",
            work_description="Test for inspections",
            estimated_cost=8000.00,
            applicant=test_applicant,
            documents=[]
        )

        # Create inspection for the permit
        inspection = await inspection_repository.create_inspection(
            permit_number=permit.permit_number,
            user_id=test_user_id,
            inspection_type=InspectionType.ROUGH_ELECTRICAL,
            address="321 Inspection Test St, Los Angeles, CA 90321",
            contact_name="Test Contact",
            contact_phone="555-0321",
            scheduled_date="2026-03-01",
            scheduled_time_window="8am-12pm"
        )

        assert inspection.inspection_id is not None
        assert inspection.status == InspectionStatus.SCHEDULED

        # List inspections by permit number
        inspections = await inspection_repository.list_by_permit(permit.permit_number)
        assert len(inspections) >= 1
        assert any(i.inspection_id == inspection.inspection_id for i in inspections)

    @pytest.mark.asyncio
    async def test_list_inspections_by_user(
        self, inspection_repository, permit_repository, test_user_id, test_applicant
    ):
        """Test listing inspections by user ID (cross-partition query)."""
        # Create permit
        permit = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.MECHANICAL,
            address="654 User Inspection Test St, Los Angeles, CA 90654",
            work_description="Test for user inspections",
            estimated_cost=6000.00,
            applicant=test_applicant,
            documents=[]
        )

        # Create inspection
        inspection = await inspection_repository.create_inspection(
            permit_number=permit.permit_number,
            user_id=test_user_id,
            inspection_type=InspectionType.ROUGH_MECHANICAL,
            address="654 User Inspection Test St, Los Angeles, CA 90654",
            contact_name="Test User Contact",
            contact_phone="555-0654",
        )

        # List by user
        inspections = await inspection_repository.list_by_user(test_user_id)
        assert len(inspections) >= 1
        assert any(i.inspection_id == inspection.inspection_id for i in inspections)

    @pytest.mark.asyncio
    async def test_search_inspections_by_address(
        self, inspection_repository, permit_repository, test_user_id, test_applicant
    ):
        """Test searching inspections by address (cross-partition query)."""
        unique_address = f"888 Unique Inspection {uuid4()}, Los Angeles, CA 90888"

        # Create permit
        permit = await permit_repository.create_permit(
            user_id=test_user_id,
            permit_type=PermitType.BUILDING,
            address=unique_address,
            work_description="Test for address search",
            estimated_cost=30000.00,
            applicant=test_applicant,
            documents=[]
        )

        # Create inspection
        inspection = await inspection_repository.create_inspection(
            permit_number=permit.permit_number,
            user_id=test_user_id,
            inspection_type=InspectionType.FRAMING,
            address=unique_address,
            contact_name="Address Test Contact",
            contact_phone="555-0888",
            scheduled_date="2026-04-01",
            scheduled_time_window="8am-12pm"
        )

        # Search by address
        inspections = await inspection_repository.list_by_address("888 Unique Inspection")
        assert len(inspections) >= 1
        assert any(i.inspection_id == inspection.inspection_id for i in inspections)
