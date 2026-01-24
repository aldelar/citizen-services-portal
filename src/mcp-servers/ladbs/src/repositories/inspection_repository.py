"""Inspection repository for LADBS CosmosDB operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..models import (
    Inspection,
    InspectionStatus,
    InspectionType,
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


class InspectionRepository(BaseRepository):
    """Repository for inspection CRUD operations."""

    container_name = "inspections"
    partition_key_field = "permitNumber"

    def _generate_inspection_id(self) -> str:
        """Generate a unique inspection ID."""
        import random
        import string
        random_suffix = "".join(random.choices(string.digits, k=6))
        return f"INS-{random_suffix}"

    async def create_inspection(
        self,
        permit_number: str,
        user_id: str,
        inspection_type: InspectionType,
        address: str,
        contact_name: str,
        contact_phone: str,
        scheduled_date: Optional[str] = None,
        scheduled_time_window: Optional[str] = None,
    ) -> Inspection:
        """
        Create a new inspection record.

        Args:
            permit_number: The associated permit number.
            user_id: The user ID.
            inspection_type: Type of inspection.
            address: Inspection address.
            contact_name: Contact name.
            contact_phone: Contact phone.
            scheduled_date: Scheduled date (optional).
            scheduled_time_window: Time window (optional).

        Returns:
            Inspection: The created inspection.
        """
        inspection_id = self._generate_inspection_id()
        now = datetime.now(timezone.utc)
        
        status = InspectionStatus.SCHEDULED if scheduled_date else InspectionStatus.SCHEDULED
        
        item = {
            "id": str(uuid4()),
            "permitNumber": permit_number,
            "userId": user_id,
            "inspectionId": inspection_id,
            "inspectionType": inspection_type.value,
            "status": status.value,
            "address": address,
            "scheduledDate": scheduled_date,
            "scheduledTimeWindow": scheduled_time_window,
            "completedAt": None,
            "result": None,
            "inspectorNotes": None,
            "contactName": contact_name,
            "contactPhone": contact_phone,
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_inspection(created_item)

    async def get_inspection(
        self, inspection_doc_id: str, permit_number: str
    ) -> Optional[Inspection]:
        """
        Get an inspection by document ID and permit number.

        Args:
            inspection_doc_id: The inspection document ID.
            permit_number: The permit number (partition key).

        Returns:
            Optional[Inspection]: The inspection if found, None otherwise.
        """
        item = await self.get_by_id(inspection_doc_id, permit_number)
        if item:
            return self._to_inspection(item)
        return None

    async def get_by_inspection_id(
        self, inspection_id: str
    ) -> Optional[Inspection]:
        """
        Get an inspection by inspection ID (cross-partition query).

        Args:
            inspection_id: The inspection ID (e.g., INS-123456).

        Returns:
            Optional[Inspection]: The inspection if found, None otherwise.
        """
        query = "SELECT * FROM c WHERE c.inspectionId = @inspectionId"
        parameters = [{"name": "@inspectionId", "value": inspection_id}]
        
        items = await self.query(query, parameters)
        if items:
            return self._to_inspection(items[0])
        return None

    async def list_by_permit(self, permit_number: str) -> List[Inspection]:
        """
        List all inspections for a permit.

        Args:
            permit_number: The permit number.

        Returns:
            List[Inspection]: List of inspections.
        """
        items = await self.list_by_partition(permit_number, order_by="createdAt DESC")
        return [self._to_inspection(item) for item in items]

    async def list_by_user(self, user_id: str) -> List[Inspection]:
        """
        List all inspections for a user (cross-partition query).

        Args:
            user_id: The user ID.

        Returns:
            List[Inspection]: List of inspections.
        """
        query = "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.createdAt DESC"
        parameters = [{"name": "@userId", "value": user_id}]
        
        items = await self.query(query, parameters)
        return [self._to_inspection(item) for item in items]

    async def list_by_address(self, address: str) -> List[Inspection]:
        """
        Search inspections by address (cross-partition query).

        Args:
            address: The address to search for.

        Returns:
            List[Inspection]: List of matching inspections.
        """
        query = "SELECT * FROM c WHERE CONTAINS(LOWER(c.address), LOWER(@address))"
        parameters = [{"name": "@address", "value": address}]
        
        items = await self.query(query, parameters)
        return [self._to_inspection(item) for item in items]

    async def update_status(
        self,
        inspection_doc_id: str,
        permit_number: str,
        status: InspectionStatus,
        result: Optional[str] = None,
        inspector_notes: Optional[str] = None,
    ) -> Inspection:
        """
        Update the status of an inspection.

        Args:
            inspection_doc_id: The inspection document ID.
            permit_number: The permit number (partition key).
            status: The new status.
            result: Optional result (pass/fail).
            inspector_notes: Optional inspector notes.

        Returns:
            Inspection: The updated inspection.

        Raises:
            NotFoundError: If the inspection is not found.
        """
        item = await self.get_by_id(inspection_doc_id, permit_number)
        if not item:
            raise NotFoundError(f"Inspection with ID {inspection_doc_id} not found")
        
        item["status"] = status.value
        
        if result is not None:
            item["result"] = result
        
        if inspector_notes is not None:
            item["inspectorNotes"] = inspector_notes
        
        # Set completed_at if status indicates completion
        if status in [InspectionStatus.COMPLETED, InspectionStatus.PASSED, InspectionStatus.FAILED]:
            if not item.get("completedAt"):
                item["completedAt"] = datetime.now(timezone.utc).isoformat()
        
        updated_item = await self.update(inspection_doc_id, permit_number, item)
        return self._to_inspection(updated_item)

    def _to_inspection(self, item: Dict[str, Any]) -> Inspection:
        """Convert a CosmosDB document to an Inspection model."""
        scheduled_date = self.parse_date_as_datetime(item.get("scheduledDate"))
        
        return Inspection(
            inspection_id=item.get("inspectionId", ""),
            permit_number=item.get("permitNumber", ""),
            inspection_type=InspectionType(item.get("inspectionType", "rough_electrical")),
            status=InspectionStatus(item.get("status", "scheduled")),
            scheduled_date=scheduled_date,
            scheduled_time_window=item.get("scheduledTimeWindow"),
            completed_at=self.parse_datetime(item.get("completedAt")),
            result=item.get("result"),
            inspector_notes=item.get("inspectorNotes"),
        )
