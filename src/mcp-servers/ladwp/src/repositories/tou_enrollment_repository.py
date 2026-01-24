"""TOU Enrollment repository for LADWP CosmosDB operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..models import RatePlan

logger = logging.getLogger(__name__)

# Import shared cosmos client - path relative to package structure
import sys
import os

# Add shared module to path if needed
shared_path = os.path.join(os.path.dirname(__file__), "../../../../shared")
if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

try:
    from cosmos.base_repository import BaseRepository
    from cosmos.exceptions import NotFoundError
except ImportError:
    # Fallback for when cosmos module is installed as package
    from citizen_services_shared.cosmos.base_repository import BaseRepository
    from citizen_services_shared.cosmos.exceptions import NotFoundError


# TOU Enrollment status enum (not in models.py, define here)
from enum import Enum


class TOUEnrollmentStatus(str, Enum):
    """Status of TOU enrollment."""
    PENDING = "pending"
    ACTIVE = "active"
    CANCELLED = "cancelled"


class TOUEnrollment:
    """TOU Enrollment data class."""
    
    def __init__(
        self,
        confirmation_number: str,
        account_number: str,
        rate_plan: RatePlan,
        previous_plan: str,
        status: TOUEnrollmentStatus,
        effective_date: str,
        meter_swap_required: bool,
        meter_swap_date: Optional[str] = None,
        enrolled_at: Optional[datetime] = None,
    ):
        self.confirmation_number = confirmation_number
        self.account_number = account_number
        self.rate_plan = rate_plan
        self.previous_plan = previous_plan
        self.status = status
        self.effective_date = effective_date
        self.meter_swap_required = meter_swap_required
        self.meter_swap_date = meter_swap_date
        self.enrolled_at = enrolled_at


class TOUEnrollmentRepository(BaseRepository):
    """Repository for TOU enrollment CRUD operations."""

    container_name = "tou_enrollments"
    partition_key_field = "accountNumber"

    def _generate_confirmation_number(self) -> str:
        """Generate a unique confirmation number."""
        import random
        import string
        random_suffix = "".join(random.choices(string.digits, k=5))
        return f"TOU-2026-{random_suffix}"

    async def create_enrollment(
        self,
        user_id: str,
        account_number: str,
        rate_plan: RatePlan,
        previous_plan: str,
        effective_date: str,
        meter_swap_required: bool = False,
        meter_swap_date: Optional[str] = None,
    ) -> TOUEnrollment:
        """
        Create a new TOU enrollment.

        Args:
            user_id: The user ID.
            account_number: LADWP account number.
            rate_plan: The TOU rate plan.
            previous_plan: Previous rate plan.
            effective_date: When the new rate takes effect.
            meter_swap_required: Whether a meter swap is needed.
            meter_swap_date: Scheduled meter swap date.

        Returns:
            TOUEnrollment: The created enrollment.
        """
        confirmation_number = self._generate_confirmation_number()
        now = datetime.now(timezone.utc)
        
        item = {
            "id": str(uuid4()),
            "userId": user_id,
            "accountNumber": account_number,
            "confirmationNumber": confirmation_number,
            "ratePlan": rate_plan.value,
            "previousPlan": previous_plan,
            "status": TOUEnrollmentStatus.PENDING.value,
            "effectiveDate": effective_date,
            "meterSwapRequired": meter_swap_required,
            "meterSwapDate": meter_swap_date,
            "enrolledAt": now.isoformat(),
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_enrollment(created_item)

    async def get_enrollment(
        self, enrollment_id: str, account_number: str
    ) -> Optional[TOUEnrollment]:
        """
        Get an enrollment by ID and account number.

        Args:
            enrollment_id: The enrollment document ID.
            account_number: The account number (partition key).

        Returns:
            Optional[TOUEnrollment]: The enrollment if found, None otherwise.
        """
        item = await self.get_by_id(enrollment_id, account_number)
        if item:
            return self._to_enrollment(item)
        return None

    async def get_by_confirmation_number(
        self, confirmation_number: str
    ) -> Optional[TOUEnrollment]:
        """
        Get an enrollment by confirmation number (cross-partition query).

        Args:
            confirmation_number: The confirmation number.

        Returns:
            Optional[TOUEnrollment]: The enrollment if found, None otherwise.
        """
        query = "SELECT * FROM c WHERE c.confirmationNumber = @confirmationNumber"
        parameters = [{"name": "@confirmationNumber", "value": confirmation_number}]
        
        items = await self.query(query, parameters)
        if items:
            return self._to_enrollment(items[0])
        return None

    async def list_by_account(self, account_number: str) -> List[TOUEnrollment]:
        """
        List all enrollments for an account.

        Args:
            account_number: The account number.

        Returns:
            List[TOUEnrollment]: List of enrollments.
        """
        items = await self.list_by_partition(account_number, order_by="createdAt DESC")
        return [self._to_enrollment(item) for item in items]

    async def list_by_user(self, user_id: str) -> List[TOUEnrollment]:
        """
        List all enrollments for a user (cross-partition query).

        Args:
            user_id: The user ID.

        Returns:
            List[TOUEnrollment]: List of enrollments.
        """
        query = "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.createdAt DESC"
        parameters = [{"name": "@userId", "value": user_id}]
        
        items = await self.query(query, parameters)
        return [self._to_enrollment(item) for item in items]

    async def update_status(
        self,
        enrollment_id: str,
        account_number: str,
        status: TOUEnrollmentStatus,
    ) -> TOUEnrollment:
        """
        Update the status of an enrollment.

        Args:
            enrollment_id: The enrollment document ID.
            account_number: The account number (partition key).
            status: The new status.

        Returns:
            TOUEnrollment: The updated enrollment.

        Raises:
            NotFoundError: If the enrollment is not found.
        """
        item = await self.get_by_id(enrollment_id, account_number)
        if not item:
            raise NotFoundError(f"Enrollment with ID {enrollment_id} not found")
        
        item["status"] = status.value
        
        updated_item = await self.update(enrollment_id, account_number, item)
        return self._to_enrollment(updated_item)

    def _to_enrollment(self, item: Dict[str, Any]) -> TOUEnrollment:
        """Convert a CosmosDB document to a TOUEnrollment."""
        return TOUEnrollment(
            confirmation_number=item.get("confirmationNumber", ""),
            account_number=item.get("accountNumber", ""),
            rate_plan=RatePlan(item.get("ratePlan", "TOU-D-A")),
            previous_plan=item.get("previousPlan", "standard"),
            status=TOUEnrollmentStatus(item.get("status", "pending")),
            effective_date=item.get("effectiveDate", ""),
            meter_swap_required=item.get("meterSwapRequired", False),
            meter_swap_date=item.get("meterSwapDate"),
            enrolled_at=datetime.fromisoformat(item["enrolledAt"].replace("Z", "+00:00"))
                if item.get("enrolledAt") else None,
        )
