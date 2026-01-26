"""Integration tests for LADWP CosmosDB operations.

These tests require a live CosmosDB instance with COSMOS_ENDPOINT configured.
Run with: pytest -m integration
"""

import os
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.models import (
    EquipmentType,
    InterconnectionStatus,
    RatePlan,
    RebateStatus,
)
from src.repositories import (
    InterconnectionRepository,
    RebateRepository,
    TOUEnrollmentRepository,
)
from src.repositories.tou_enrollment_repository import TOUEnrollmentStatus


# Skip all tests in this file if CosmosDB is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("COSMOS_ENDPOINT"),
        reason="CosmosDB not configured (COSMOS_ENDPOINT not set)"
    )
]


@pytest.fixture(scope="session")
async def interconnection_repository():
    """Create an InterconnectionRepository instance for testing."""
    return InterconnectionRepository()


@pytest.fixture(scope="session")
async def rebate_repository():
    """Create a RebateRepository instance for testing."""
    return RebateRepository()


@pytest.fixture(scope="session")
async def tou_repository():
    """Create a TOUEnrollmentRepository instance for testing."""
    return TOUEnrollmentRepository()


@pytest.fixture
def test_user_id():
    """Generate a unique user ID for testing."""
    return f"test-user-{uuid4()}"


@pytest.fixture
def test_account_number():
    """Generate a unique account number for testing."""
    return f"ACC-{uuid4().hex[:10].upper()}"


class TestInterconnectionRepository:
    """Tests for interconnection repository operations."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_interconnection(
        self, interconnection_repository, test_user_id
    ):
        """Create an interconnection and retrieve it by application ID."""
        # Create interconnection
        interconnection = await interconnection_repository.create_interconnection(
            user_id=test_user_id,
            address="123 Solar St, Los Angeles, CA 90012",
            system_size_kw=8.5,
            applicant_name="Test User",
            applicant_email="test@example.com",
            inverter="SolarEdge SE7600H",
            panels="LG NeON 2 400W x 20",
            battery_size_kwh=13.5,
            battery="Tesla Powerwall 2",
        )

        assert interconnection.application_id is not None
        assert interconnection.status == InterconnectionStatus.SUBMITTED
        assert interconnection.system_size_kw == 8.5

        # Retrieve by application ID (cross-partition)
        retrieved = await interconnection_repository.get_by_application_id(
            interconnection.application_id
        )
        assert retrieved is not None
        assert retrieved.application_id == interconnection.application_id
        assert retrieved.address == "123 Solar St, Los Angeles, CA 90012"

    @pytest.mark.asyncio
    async def test_list_by_user(
        self, interconnection_repository, test_user_id
    ):
        """Test listing all interconnections for a user."""
        # Create multiple interconnections
        ic1 = await interconnection_repository.create_interconnection(
            user_id=test_user_id,
            address="111 First St, Los Angeles, CA 90001",
            system_size_kw=5.0,
            applicant_name="Test User",
            applicant_email="test@example.com",
            inverter="Enphase IQ8",
            panels="REC Alpha 380W x 13",
        )

        ic2 = await interconnection_repository.create_interconnection(
            user_id=test_user_id,
            address="222 Second St, Los Angeles, CA 90002",
            system_size_kw=10.0,
            applicant_name="Test User",
            applicant_email="test@example.com",
            inverter="SMA Sunny Boy",
            panels="Panasonic EverVolt 370W x 27",
        )

        # List all interconnections for user
        interconnections = await interconnection_repository.list_by_user(test_user_id)
        assert len(interconnections) >= 2
        app_ids = [ic.application_id for ic in interconnections]
        assert ic1.application_id in app_ids
        assert ic2.application_id in app_ids


class TestRebateRepository:
    """Tests for rebate repository operations."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_rebate(
        self, rebate_repository, test_user_id, test_account_number
    ):
        """Create a rebate and retrieve it by application ID."""
        # Create rebate
        rebate = await rebate_repository.create_rebate(
            user_id=test_user_id,
            account_number=test_account_number,
            equipment_type=EquipmentType.HEAT_PUMP_HVAC,
            equipment_details="Mitsubishi 3-zone ductless, 3 tons",
            purchase_date="2026-01-15",
            invoice_total=12500.00,
            estimated_rebate=7500.00,
            ahri_certificate="AHRI-12345678",
            ladbs_permit_number="PERMIT-2026-001234",
        )

        assert rebate.application_id is not None
        assert rebate.status == RebateStatus.SUBMITTED
        assert rebate.estimated_rebate == 7500.00

        # Retrieve by application ID (cross-partition)
        retrieved = await rebate_repository.get_by_application_id(
            rebate.application_id
        )
        assert retrieved is not None
        assert retrieved.application_id == rebate.application_id
        assert retrieved.account_number == test_account_number

    @pytest.mark.asyncio
    async def test_list_by_user(
        self, rebate_repository, test_user_id, test_account_number
    ):
        """Test listing all rebates for a user."""
        # Create multiple rebates
        rebate1 = await rebate_repository.create_rebate(
            user_id=test_user_id,
            account_number=test_account_number,
            equipment_type=EquipmentType.HEAT_PUMP_HVAC,
            equipment_details="First HVAC system",
            purchase_date="2026-01-10",
            invoice_total=8000.00,
            estimated_rebate=5000.00,
        )

        rebate2 = await rebate_repository.create_rebate(
            user_id=test_user_id,
            account_number=test_account_number,
            equipment_type=EquipmentType.HEAT_PUMP_WATER_HEATER,
            equipment_details="Rheem ProTerra",
            purchase_date="2026-01-20",
            invoice_total=3500.00,
            estimated_rebate=3000.00,
        )

        # List all rebates for user
        rebates = await rebate_repository.list_by_user(test_user_id)
        assert len(rebates) >= 2
        app_ids = [r.application_id for r in rebates]
        assert rebate1.application_id in app_ids
        assert rebate2.application_id in app_ids

    @pytest.mark.asyncio
    async def test_list_by_account_number(
        self, rebate_repository, test_user_id, test_account_number
    ):
        """Test listing rebates by account number."""
        # Create a rebate
        rebate = await rebate_repository.create_rebate(
            user_id=test_user_id,
            account_number=test_account_number,
            equipment_type=EquipmentType.SMART_THERMOSTAT,
            equipment_details="Nest Learning Thermostat",
            purchase_date="2026-01-25",
            invoice_total=250.00,
            estimated_rebate=150.00,
        )

        # List by account number
        rebates = await rebate_repository.list_by_account(test_account_number)
        assert len(rebates) >= 1
        assert any(r.application_id == rebate.application_id for r in rebates)


class TestTOUEnrollmentRepository:
    """Tests for TOU enrollment repository operations."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_enrollment(
        self, tou_repository, test_user_id, test_account_number
    ):
        """Create an enrollment and retrieve it by confirmation number."""
        # Create enrollment
        enrollment = await tou_repository.create_enrollment(
            user_id=test_user_id,
            account_number=test_account_number,
            rate_plan=RatePlan.TOU_D_PRIME,
            previous_plan="standard",
            effective_date="2026-02-15",
            meter_swap_required=True,
            meter_swap_date="2026-02-12",
        )

        assert enrollment.confirmation_number is not None
        assert enrollment.status == TOUEnrollmentStatus.PENDING
        assert enrollment.rate_plan == RatePlan.TOU_D_PRIME

        # Retrieve by confirmation number (cross-partition)
        retrieved = await tou_repository.get_by_confirmation_number(
            enrollment.confirmation_number
        )
        assert retrieved is not None
        assert retrieved.confirmation_number == enrollment.confirmation_number
        assert retrieved.account_number == test_account_number

    @pytest.mark.asyncio
    async def test_list_by_user(
        self, tou_repository, test_user_id
    ):
        """Test listing all enrollments for a user."""
        # Create account numbers for this test
        account1 = f"ACC-{uuid4().hex[:10].upper()}"
        account2 = f"ACC-{uuid4().hex[:10].upper()}"

        # Create multiple enrollments
        enrollment1 = await tou_repository.create_enrollment(
            user_id=test_user_id,
            account_number=account1,
            rate_plan=RatePlan.TOU_D_A,
            previous_plan="standard",
            effective_date="2026-03-01",
        )

        enrollment2 = await tou_repository.create_enrollment(
            user_id=test_user_id,
            account_number=account2,
            rate_plan=RatePlan.TOU_D_B,
            previous_plan="standard",
            effective_date="2026-03-15",
        )

        # List all enrollments for user
        enrollments = await tou_repository.list_by_user(test_user_id)
        assert len(enrollments) >= 2
        confirmation_numbers = [e.confirmation_number for e in enrollments]
        assert enrollment1.confirmation_number in confirmation_numbers
        assert enrollment2.confirmation_number in confirmation_numbers

    @pytest.mark.asyncio
    async def test_list_by_account(
        self, tou_repository, test_user_id, test_account_number
    ):
        """Test listing enrollments by account."""
        # Create an enrollment
        enrollment = await tou_repository.create_enrollment(
            user_id=test_user_id,
            account_number=test_account_number,
            rate_plan=RatePlan.TOU_D_PRIME,
            previous_plan="TOU-D-A",
            effective_date="2026-04-01",
        )

        # List by account
        enrollments = await tou_repository.list_by_account(test_account_number)
        assert len(enrollments) >= 1
        assert any(
            e.confirmation_number == enrollment.confirmation_number
            for e in enrollments
        )
