"""Permit repository for LADBS CosmosDB operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..models import (
    Applicant,
    Permit,
    PermitFees,
    PermitStatus,
    PermitType,
)

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
    from cosmos.client import get_container
    from cosmos.exceptions import NotFoundError
except ImportError:
    # Fallback for when cosmos module is installed as package
    from citizen_services_shared.cosmos.base_repository import BaseRepository
    from citizen_services_shared.cosmos.client import get_container
    from citizen_services_shared.cosmos.exceptions import NotFoundError


class PermitRepository(BaseRepository):
    """Repository for permit CRUD operations."""

    container_name = "permits"
    partition_key_field = "userId"

    def _generate_permit_number(self) -> str:
        """Generate a unique permit number."""
        import random
        import string
        random_suffix = "".join(random.choices(string.digits, k=6))
        return f"PERMIT-2026-{random_suffix}"

    async def create_permit(
        self,
        user_id: str,
        permit_type: PermitType,
        address: str,
        work_description: str,
        estimated_cost: float,
        applicant: Applicant,
        documents: Optional[List[str]] = None,
    ) -> Permit:
        """
        Create a new permit application.

        Args:
            user_id: The user ID.
            permit_type: Type of permit.
            address: Property address.
            work_description: Description of work.
            estimated_cost: Estimated project cost.
            applicant: Applicant information.
            documents: List of document names.

        Returns:
            Permit: The created permit.
        """
        permit_number = self._generate_permit_number()
        
        # Calculate fees based on estimated cost
        plan_check = round(estimated_cost * 0.018, 2)  # ~1.8% of project cost
        permit_fee = round(estimated_cost * 0.032, 2)  # ~3.2% of project cost
        total = round(plan_check + permit_fee, 2)
        
        now = datetime.now(timezone.utc)
        
        item = {
            "id": str(uuid4()),
            "userId": user_id,
            "permitNumber": permit_number,
            "permitType": permit_type.value,
            "status": PermitStatus.SUBMITTED.value,
            "address": address,
            "workDescription": work_description,
            "estimatedCost": estimated_cost,
            "applicant": {
                "name": applicant.name,
                "email": applicant.email,
                "phone": applicant.phone,
                "contractorLicense": applicant.contractor_license,
            },
            "documents": documents or [],
            "fees": {
                "planCheck": plan_check,
                "permitFee": permit_fee,
                "otherFees": 0.0,
                "total": total,
            },
            "submittedAt": now.isoformat(),
            "approvedAt": None,
            "expiresAt": None,
            "nextSteps": "Awaiting plan check review",
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_permit(created_item)

    async def get_permit(
        self, permit_id: str, user_id: str
    ) -> Optional[Permit]:
        """
        Get a permit by ID and user ID.

        Args:
            permit_id: The permit document ID.
            user_id: The user ID (partition key).

        Returns:
            Optional[Permit]: The permit if found, None otherwise.
        """
        item = await self.get_by_id(permit_id, user_id)
        if item:
            return self._to_permit(item)
        return None

    async def get_by_permit_number(
        self, permit_number: str, user_id: Optional[str] = None
    ) -> Optional[Permit]:
        """
        Get a permit by permit number.
        
        If user_id is provided, uses efficient partition-aware query.
        Otherwise, falls back to cross-partition query.

        Args:
            permit_number: The permit number.
            user_id: Optional user ID for partition-aware query optimization.

        Returns:
            Optional[Permit]: The permit if found, None otherwise.
        """
        query = "SELECT * FROM c WHERE c.permitNumber = @permitNumber"
        parameters = [{"name": "@permitNumber", "value": permit_number}]
        
        if user_id:
            # Efficient: query within single partition
            items = await self.query(query, parameters, partition_key=user_id)
        else:
            # Fallback: cross-partition query (slower)
            items = await self.query(query, parameters)
        
        if items:
            return self._to_permit(items[0])
        return None

    async def list_by_user(self, user_id: str) -> List[Permit]:
        """
        List all permits for a user.

        Args:
            user_id: The user ID.

        Returns:
            List[Permit]: List of permits.
        """
        items = await self.list_by_partition(user_id, order_by="createdAt DESC")
        return [self._to_permit(item) for item in items]

    async def search_by_address(
        self, address: str, user_id: Optional[str] = None
    ) -> List[Permit]:
        """
        Search permits by address.
        
        If user_id is provided, uses partition-aware query for better performance.
        Otherwise, uses cross-partition query.

        Args:
            address: The address to search for.
            user_id: Optional user ID for partition-aware query optimization.

        Returns:
            List[Permit]: List of matching permits.
        """
        query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.address), LOWER(@address))"
        parameters = [{"name": "@address", "value": address}]
        
        if user_id:
            # Efficient: query within single partition
            items = await self.query(query, parameters, partition_key=user_id)
        else:
            # Fallback: cross-partition query (slower)
            items = await self.query(query, parameters)
        
        return [self._to_permit(item) for item in items]

    async def update_status(
        self,
        permit_id: str,
        user_id: str,
        status: PermitStatus,
        next_steps: Optional[str] = None,
    ) -> Permit:
        """
        Update the status of a permit.

        Args:
            permit_id: The permit document ID.
            user_id: The user ID (partition key).
            status: The new status.
            next_steps: Optional updated next steps.

        Returns:
            Permit: The updated permit.

        Raises:
            NotFoundError: If the permit is not found.
        """
        item = await self.get_by_id(permit_id, user_id)
        if not item:
            raise NotFoundError(f"Permit with ID {permit_id} not found")
        
        item["status"] = status.value
        if next_steps:
            item["nextSteps"] = next_steps
        
        # Set approved_at if status is approved
        if status == PermitStatus.APPROVED and not item.get("approvedAt"):
            item["approvedAt"] = datetime.now(timezone.utc).isoformat()
        
        updated_item = await self.update(permit_id, user_id, item)
        return self._to_permit(updated_item)

    def _to_permit(self, item: Dict[str, Any]) -> Permit:
        """Convert a CosmosDB document to a Permit model."""
        fees = None
        if item.get("fees"):
            fees = PermitFees(
                plan_check=item["fees"].get("planCheck", 0),
                permit_fee=item["fees"].get("permitFee", 0),
                other_fees=item["fees"].get("otherFees", 0),
                total=item["fees"].get("total", 0),
            )
        
        return Permit(
            permit_number=item.get("permitNumber", ""),
            permit_type=PermitType(item.get("permitType", "electrical")),
            status=PermitStatus(item.get("status", "submitted")),
            address=item.get("address", ""),
            description=item.get("workDescription", ""),
            applicant_name=item.get("applicant", {}).get("name", ""),
            submitted_at=self.parse_datetime(item.get("submittedAt")) or datetime.now(timezone.utc),
            approved_at=self.parse_datetime(item.get("approvedAt")),
            expires_at=self.parse_datetime(item.get("expiresAt")),
            fees=fees,
            next_steps=item.get("nextSteps"),
        )
