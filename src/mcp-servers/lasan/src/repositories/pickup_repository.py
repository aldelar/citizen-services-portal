"""Pickup repository for LASAN CosmosDB operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..models import (
    ScheduledPickup,
    PickupStatus,
    PickupType,
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


class PickupRepository(BaseRepository):
    """Repository for pickup CRUD operations."""

    container_name = "pickups"
    partition_key_field = "userId"

    def _generate_pickup_id(self) -> str:
        """Generate a unique pickup ID."""
        import random
        import string
        random_suffix = "".join(random.choices(string.digits, k=4))
        return f"PU-2026-{random_suffix}"

    def _generate_confirmation_number(self) -> str:
        """Generate a unique confirmation number."""
        import random
        import string
        random_suffix = "".join(random.choices(string.digits, k=5))
        return f"311-CONF-{random_suffix}"

    async def create_pickup(
        self,
        user_id: str,
        pickup_type: PickupType,
        address: str,
        items: List[str],
        scheduled_date: str,
        contact_name: str,
        contact_phone: str,
        notes: Optional[str] = None,
    ) -> ScheduledPickup:
        """
        Create a new pickup request.

        Args:
            user_id: The user ID.
            pickup_type: Type of pickup.
            address: Pickup address.
            items: List of items for pickup.
            scheduled_date: Scheduled pickup date.
            contact_name: Contact name.
            contact_phone: Contact phone.
            notes: Optional notes.

        Returns:
            ScheduledPickup: The created pickup.
        """
        pickup_id = self._generate_pickup_id()
        confirmation_number = self._generate_confirmation_number()
        now = datetime.now(timezone.utc)
        
        item = {
            "id": str(uuid4()),
            "userId": user_id,
            "pickupId": pickup_id,
            "pickupType": pickup_type.value,
            "status": PickupStatus.SCHEDULED.value,
            "address": address,
            "items": items,
            "scheduledDate": scheduled_date,
            "confirmationNumber": confirmation_number,
            "contactName": contact_name,
            "contactPhone": contact_phone,
            "notes": notes,
            "completedAt": None,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_pickup(created_item)

    async def get_pickup(
        self, pickup_doc_id: str, user_id: str
    ) -> Optional[ScheduledPickup]:
        """
        Get a pickup by document ID and user ID.

        Args:
            pickup_doc_id: The pickup document ID.
            user_id: The user ID (partition key).

        Returns:
            Optional[ScheduledPickup]: The pickup if found, None otherwise.
        """
        item = await self.get_by_id(pickup_doc_id, user_id)
        if item:
            return self._to_pickup(item)
        return None

    async def get_by_pickup_id(
        self, pickup_id: str
    ) -> Optional[ScheduledPickup]:
        """
        Get a pickup by pickup ID (cross-partition query).

        Args:
            pickup_id: The pickup ID (e.g., PU-2026-1234).

        Returns:
            Optional[ScheduledPickup]: The pickup if found, None otherwise.
        """
        query = "SELECT * FROM c WHERE c.pickupId = @pickupId"
        parameters = [{"name": "@pickupId", "value": pickup_id}]
        
        items = await self.query(query, parameters)
        if items:
            return self._to_pickup(items[0])
        return None

    async def list_by_user(self, user_id: str) -> List[ScheduledPickup]:
        """
        List all pickups for a user.

        Args:
            user_id: The user ID.

        Returns:
            List[ScheduledPickup]: List of pickups.
        """
        items = await self.list_by_partition(user_id, order_by="createdAt DESC")
        return [self._to_pickup(item) for item in items]

    async def search_by_address(self, address: str) -> List[ScheduledPickup]:
        """
        Search pickups by address (cross-partition query).

        Args:
            address: The address to search for.

        Returns:
            List[ScheduledPickup]: List of matching pickups.
        """
        query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.address), LOWER(@address))"
        parameters = [{"name": "@address", "value": address}]
        
        items = await self.query(query, parameters)
        return [self._to_pickup(item) for item in items]

    async def update_status(
        self,
        pickup_doc_id: str,
        user_id: str,
        status: PickupStatus,
    ) -> ScheduledPickup:
        """
        Update the status of a pickup.

        Args:
            pickup_doc_id: The pickup document ID.
            user_id: The user ID (partition key).
            status: The new status.

        Returns:
            ScheduledPickup: The updated pickup.

        Raises:
            NotFoundError: If the pickup is not found.
        """
        item = await self.get_by_id(pickup_doc_id, user_id)
        if not item:
            raise NotFoundError(f"Pickup with ID {pickup_doc_id} not found")
        
        item["status"] = status.value
        
        # Set completed_at if status indicates completion
        if status == PickupStatus.COMPLETED and not item.get("completedAt"):
            item["completedAt"] = datetime.now(timezone.utc).isoformat()
        
        updated_item = await self.update(pickup_doc_id, user_id, item)
        return self._to_pickup(updated_item)

    def _to_pickup(self, item: Dict[str, Any]) -> ScheduledPickup:
        """Convert a CosmosDB document to a ScheduledPickup model."""
        scheduled_date = None
        if item.get("scheduledDate"):
            try:
                # Parse as datetime if it includes time
                scheduled_date = datetime.fromisoformat(
                    item["scheduledDate"].replace("Z", "+00:00")
                )
            except ValueError:
                # It's just a date string, convert to datetime
                from datetime import date
                d = date.fromisoformat(item["scheduledDate"])
                scheduled_date = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
        
        return ScheduledPickup(
            pickup_id=item.get("pickupId", ""),
            pickup_type=PickupType(item.get("pickupType", "bulky_item")),
            address=item.get("address", ""),
            scheduled_date=scheduled_date or datetime.now(timezone.utc),
            items=item.get("items", []),
            status=PickupStatus(item.get("status", "scheduled")),
            confirmation_number=item.get("confirmationNumber"),
            notes=item.get("notes"),
        )
