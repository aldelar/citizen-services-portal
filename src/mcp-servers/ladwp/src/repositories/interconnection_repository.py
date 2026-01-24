"""Interconnection repository for LADWP CosmosDB operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..models import (
    Interconnection,
    InterconnectionStatus,
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
    from cosmos.exceptions import NotFoundError
except ImportError:
    # Fallback for when cosmos module is installed as package
    from citizen_services_shared.cosmos.base_repository import BaseRepository
    from citizen_services_shared.cosmos.exceptions import NotFoundError


class InterconnectionRepository(BaseRepository):
    """Repository for interconnection CRUD operations."""

    container_name = "interconnections"
    partition_key_field = "userId"

    def _generate_application_id(self) -> str:
        """Generate a unique application ID."""
        import random
        import string
        random_suffix = "".join(random.choices(string.digits, k=5))
        return f"IA-2026-{random_suffix}"

    async def create_interconnection(
        self,
        user_id: str,
        address: str,
        system_size_kw: float,
        applicant_name: str,
        applicant_email: str,
        inverter: str,
        panels: str,
        battery_size_kwh: Optional[float] = None,
        battery: Optional[str] = None,
        ladbs_permit_number: Optional[str] = None,
    ) -> Interconnection:
        """
        Create a new interconnection application.

        Args:
            user_id: The user ID.
            address: Service address.
            system_size_kw: System size in kW.
            applicant_name: Applicant name.
            applicant_email: Applicant email.
            inverter: Inverter model.
            panels: Panel details.
            battery_size_kwh: Optional battery size.
            battery: Optional battery model.
            ladbs_permit_number: Optional associated LADBS permit.

        Returns:
            Interconnection: The created interconnection application.
        """
        application_id = self._generate_application_id()
        now = datetime.now(timezone.utc)
        
        item = {
            "id": str(uuid4()),
            "userId": user_id,
            "applicationId": application_id,
            "address": address,
            "systemSizeKw": system_size_kw,
            "batterySizeKwh": battery_size_kwh,
            "status": InterconnectionStatus.SUBMITTED.value,
            "applicant": {
                "name": applicant_name,
                "email": applicant_email,
            },
            "equipment": {
                "inverter": inverter,
                "panels": panels,
                "battery": battery,
            },
            "ladbsPermitNumber": ladbs_permit_number,
            "submittedAt": now.isoformat(),
            "approvedAt": None,
            "ptoDate": None,
            "nextSteps": "Awaiting engineering review",
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_interconnection(created_item)

    async def get_interconnection(
        self, interconnection_id: str, user_id: str
    ) -> Optional[Interconnection]:
        """
        Get an interconnection by ID and user ID.

        Args:
            interconnection_id: The interconnection document ID.
            user_id: The user ID (partition key).

        Returns:
            Optional[Interconnection]: The interconnection if found, None otherwise.
        """
        item = await self.get_by_id(interconnection_id, user_id)
        if item:
            return self._to_interconnection(item)
        return None

    async def get_by_application_id(
        self, application_id: str
    ) -> Optional[Interconnection]:
        """
        Get an interconnection by application ID (cross-partition query).

        Args:
            application_id: The application ID.

        Returns:
            Optional[Interconnection]: The interconnection if found, None otherwise.
        """
        query = "SELECT * FROM c WHERE c.applicationId = @applicationId"
        parameters = [{"name": "@applicationId", "value": application_id}]
        
        items = await self.query(query, parameters)
        if items:
            return self._to_interconnection(items[0])
        return None

    async def list_by_user(self, user_id: str) -> List[Interconnection]:
        """
        List all interconnections for a user.

        Args:
            user_id: The user ID.

        Returns:
            List[Interconnection]: List of interconnections.
        """
        items = await self.list_by_partition(user_id, order_by="createdAt DESC")
        return [self._to_interconnection(item) for item in items]

    async def update_status(
        self,
        interconnection_id: str,
        user_id: str,
        status: InterconnectionStatus,
        next_steps: Optional[str] = None,
    ) -> Interconnection:
        """
        Update the status of an interconnection.

        Args:
            interconnection_id: The interconnection document ID.
            user_id: The user ID (partition key).
            status: The new status.
            next_steps: Optional updated next steps.

        Returns:
            Interconnection: The updated interconnection.

        Raises:
            NotFoundError: If the interconnection is not found.
        """
        item = await self.get_by_id(interconnection_id, user_id)
        if not item:
            raise NotFoundError(f"Interconnection with ID {interconnection_id} not found")
        
        item["status"] = status.value
        if next_steps:
            item["nextSteps"] = next_steps
        
        now = datetime.now(timezone.utc)
        
        # Set approved_at if status is approved
        if status == InterconnectionStatus.APPROVED and not item.get("approvedAt"):
            item["approvedAt"] = now.isoformat()
        
        # Set pto_date if PTO is issued
        if status == InterconnectionStatus.PTO_ISSUED and not item.get("ptoDate"):
            item["ptoDate"] = now.isoformat()
        
        updated_item = await self.update(interconnection_id, user_id, item)
        return self._to_interconnection(updated_item)

    def _to_interconnection(self, item: Dict[str, Any]) -> Interconnection:
        """Convert a CosmosDB document to an Interconnection model."""
        return Interconnection(
            application_id=item.get("applicationId"),
            address=item.get("address", ""),
            system_size_kw=item.get("systemSizeKw", 0.0),
            battery_size_kwh=item.get("batterySizeKwh"),
            status=InterconnectionStatus(item.get("status", "not_submitted")),
            submitted_at=datetime.fromisoformat(item["submittedAt"].replace("Z", "+00:00"))
                if item.get("submittedAt") else None,
            approved_at=datetime.fromisoformat(item["approvedAt"].replace("Z", "+00:00"))
                if item.get("approvedAt") else None,
            pto_date=datetime.fromisoformat(item["ptoDate"].replace("Z", "+00:00"))
                if item.get("ptoDate") else None,
            next_steps=item.get("nextSteps"),
        )
