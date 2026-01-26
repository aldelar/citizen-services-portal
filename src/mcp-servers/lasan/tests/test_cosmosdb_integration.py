"""Integration tests for LASAN CosmosDB operations.

These tests require a live CosmosDB instance with COSMOS_ENDPOINT configured.
Run with: pytest -m integration
"""

import os
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.models import (
    PickupStatus,
    PickupType,
)
from src.repositories import PickupRepository


# Skip all tests in this file if CosmosDB is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("COSMOS_ENDPOINT"),
        reason="CosmosDB not configured (COSMOS_ENDPOINT not set)"
    )
]


@pytest.fixture(scope="session")
async def pickup_repository():
    """Create a PickupRepository instance for testing."""
    return PickupRepository()


@pytest.fixture
def test_user_id():
    """Generate a unique user ID for testing."""
    return f"test-user-{uuid4()}"


class TestPickupRepository:
    """Tests for pickup repository operations."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_pickup(
        self, pickup_repository, test_user_id
    ):
        """Create a pickup and retrieve it by pickup ID."""
        # Create pickup
        pickup = await pickup_repository.create_pickup(
            user_id=test_user_id,
            pickup_type=PickupType.BULKY_ITEM,
            address="123 Test St, Los Angeles, CA 90012",
            items=["old sofa", "mattress"],
            scheduled_date="2026-03-01",
            contact_name="Test User",
            contact_phone="555-0123",
            notes="Please pick up from side yard"
        )

        assert pickup.pickup_id is not None
        assert pickup.status == PickupStatus.SCHEDULED
        assert pickup.confirmation_number is not None

        # Retrieve by pickup ID (cross-partition)
        retrieved = await pickup_repository.get_by_pickup_id(pickup.pickup_id)
        assert retrieved is not None
        assert retrieved.pickup_id == pickup.pickup_id
        assert retrieved.address == "123 Test St, Los Angeles, CA 90012"

    @pytest.mark.asyncio
    async def test_list_by_user(
        self, pickup_repository, test_user_id
    ):
        """Test listing all pickups for a user."""
        # Create multiple pickups
        pickup1 = await pickup_repository.create_pickup(
            user_id=test_user_id,
            pickup_type=PickupType.BULKY_ITEM,
            address="111 First St, Los Angeles, CA 90001",
            items=["old chair"],
            scheduled_date="2026-03-05",
            contact_name="Test User 1",
            contact_phone="555-0001"
        )

        pickup2 = await pickup_repository.create_pickup(
            user_id=test_user_id,
            pickup_type=PickupType.EWASTE,
            address="222 Second St, Los Angeles, CA 90002",
            items=["old TV", "computer monitor"],
            scheduled_date="2026-03-10",
            contact_name="Test User 2",
            contact_phone="555-0002"
        )

        # List all pickups for user
        pickups = await pickup_repository.list_by_user(test_user_id)
        assert len(pickups) >= 2
        pickup_ids = [p.pickup_id for p in pickups]
        assert pickup1.pickup_id in pickup_ids
        assert pickup2.pickup_id in pickup_ids

    @pytest.mark.asyncio
    async def test_search_by_address(
        self, pickup_repository, test_user_id
    ):
        """Test searching pickups by address."""
        unique_address = f"999 Unique Test St {uuid4()}, Los Angeles, CA 90099"

        # Create pickup with unique address
        pickup = await pickup_repository.create_pickup(
            user_id=test_user_id,
            pickup_type=PickupType.BULKY_ITEM,
            address=unique_address,
            items=["desk"],
            scheduled_date="2026-03-15",
            contact_name="Address Test",
            contact_phone="555-0099"
        )

        # Search by partial address (cross-partition)
        results = await pickup_repository.search_by_address("999 Unique Test St")
        assert len(results) >= 1
        assert any(p.pickup_id == pickup.pickup_id for p in results)

    @pytest.mark.asyncio
    async def test_update_pickup_status(
        self, pickup_repository, test_user_id
    ):
        """Test updating pickup status."""
        # Create pickup
        pickup = await pickup_repository.create_pickup(
            user_id=test_user_id,
            pickup_type=PickupType.BULKY_ITEM,
            address="789 Update Test St, Los Angeles, CA 90089",
            items=["old dresser"],
            scheduled_date="2026-03-20",
            contact_name="Status Test",
            contact_phone="555-0089"
        )

        # Get the document to find its ID
        retrieved = await pickup_repository.get_by_pickup_id(pickup.pickup_id)
        assert retrieved is not None
        assert retrieved.status == PickupStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_create_bulky_item_pickup(
        self, pickup_repository, test_user_id
    ):
        """Test bulky item pickup creation."""
        pickup = await pickup_repository.create_pickup(
            user_id=test_user_id,
            pickup_type=PickupType.BULKY_ITEM,
            address="456 Bulky Item St, Los Angeles, CA 90046",
            items=["couch", "loveseat", "coffee table"],
            scheduled_date="2026-04-01",
            contact_name="Bulky Test",
            contact_phone="555-0046"
        )

        assert pickup.pickup_type == PickupType.BULKY_ITEM
        assert len(pickup.items) == 3
        assert "couch" in pickup.items

    @pytest.mark.asyncio
    async def test_create_ewaste_pickup(
        self, pickup_repository, test_user_id
    ):
        """Test e-waste pickup creation."""
        pickup = await pickup_repository.create_pickup(
            user_id=test_user_id,
            pickup_type=PickupType.EWASTE,
            address="789 Ewaste Ave, Los Angeles, CA 90078",
            items=["old laptop", "printer", "cables"],
            scheduled_date="2026-04-05",
            contact_name="Ewaste Test",
            contact_phone="555-0078"
        )

        assert pickup.pickup_type == PickupType.EWASTE
        assert "old laptop" in pickup.items

    @pytest.mark.asyncio
    async def test_create_hazardous_pickup(
        self, pickup_repository, test_user_id
    ):
        """Test hazardous waste pickup creation."""
        pickup = await pickup_repository.create_pickup(
            user_id=test_user_id,
            pickup_type=PickupType.HAZARDOUS,
            address="321 Hazmat Blvd, Los Angeles, CA 90032",
            items=["paint cans", "motor oil"],
            scheduled_date="2026-04-10",
            contact_name="Hazmat Test",
            contact_phone="555-0032",
            notes="Paint cans are sealed"
        )

        assert pickup.pickup_type == PickupType.HAZARDOUS
        assert pickup.notes == "Paint cans are sealed"
