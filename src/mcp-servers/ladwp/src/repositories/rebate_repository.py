"""Rebate repository for LADWP CosmosDB operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..models import (
    RebateApplication,
    RebateStatus,
    EquipmentType,
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


class RebateRepository(BaseRepository):
    """Repository for rebate CRUD operations."""

    container_name = "rebates"
    partition_key_field = "userId"

    def _generate_application_id(self) -> str:
        """Generate a unique application ID."""
        import random
        import string
        random_suffix = "".join(random.choices(string.digits, k=4))
        return f"CRP-2026-{random_suffix}"

    async def create_rebate(
        self,
        user_id: str,
        account_number: str,
        equipment_type: EquipmentType,
        equipment_details: str,
        purchase_date: str,
        invoice_total: float,
        estimated_rebate: float,
        ahri_certificate: Optional[str] = None,
        ladbs_permit_number: Optional[str] = None,
    ) -> RebateApplication:
        """
        Create a new rebate application.

        Args:
            user_id: The user ID.
            account_number: LADWP account number.
            equipment_type: Type of equipment.
            equipment_details: Equipment details.
            purchase_date: Date of purchase.
            invoice_total: Total invoice amount.
            estimated_rebate: Estimated rebate amount.
            ahri_certificate: Optional AHRI certificate number.
            ladbs_permit_number: Optional associated LADBS permit.

        Returns:
            RebateApplication: The created rebate application.
        """
        application_id = self._generate_application_id()
        now = datetime.now(timezone.utc)
        
        item = {
            "id": str(uuid4()),
            "userId": user_id,
            "applicationId": application_id,
            "accountNumber": account_number,
            "equipmentType": equipment_type.value,
            "status": RebateStatus.SUBMITTED.value,
            "equipmentDetails": equipment_details,
            "purchaseDate": purchase_date,
            "invoiceTotal": invoice_total,
            "ahriCertificate": ahri_certificate,
            "ladbsPermitNumber": ladbs_permit_number,
            "estimatedRebate": estimated_rebate,
            "approvedAmount": None,
            "denialReason": None,
            "paidAt": None,
            "submittedAt": now.isoformat(),
            "createdAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }
        
        created_item = await self.create(item)
        return self._to_rebate(created_item)

    async def get_rebate(
        self, rebate_id: str, user_id: str
    ) -> Optional[RebateApplication]:
        """
        Get a rebate by ID and user ID.

        Args:
            rebate_id: The rebate document ID.
            user_id: The user ID (partition key).

        Returns:
            Optional[RebateApplication]: The rebate if found, None otherwise.
        """
        item = await self.get_by_id(rebate_id, user_id)
        if item:
            return self._to_rebate(item)
        return None

    async def get_by_application_id(
        self, application_id: str
    ) -> Optional[RebateApplication]:
        """
        Get a rebate by application ID (cross-partition query).

        Args:
            application_id: The application ID.

        Returns:
            Optional[RebateApplication]: The rebate if found, None otherwise.
        """
        query = "SELECT * FROM c WHERE c.applicationId = @applicationId"
        parameters = [{"name": "@applicationId", "value": application_id}]
        
        items = await self.query(query, parameters)
        if items:
            return self._to_rebate(items[0])
        return None

    async def list_by_user(self, user_id: str) -> List[RebateApplication]:
        """
        List all rebates for a user.

        Args:
            user_id: The user ID.

        Returns:
            List[RebateApplication]: List of rebates.
        """
        items = await self.list_by_partition(user_id, order_by="createdAt DESC")
        return [self._to_rebate(item) for item in items]

    async def list_by_account(self, account_number: str) -> List[RebateApplication]:
        """
        List all rebates for an account (cross-partition query).

        Args:
            account_number: The account number.

        Returns:
            List[RebateApplication]: List of rebates.
        """
        query = "SELECT * FROM c WHERE c.accountNumber = @accountNumber ORDER BY c.createdAt DESC"
        parameters = [{"name": "@accountNumber", "value": account_number}]
        
        items = await self.query(query, parameters)
        return [self._to_rebate(item) for item in items]

    async def update_status(
        self,
        rebate_id: str,
        user_id: str,
        status: RebateStatus,
        approved_amount: Optional[float] = None,
        denial_reason: Optional[str] = None,
    ) -> RebateApplication:
        """
        Update the status of a rebate.

        Args:
            rebate_id: The rebate document ID.
            user_id: The user ID (partition key).
            status: The new status.
            approved_amount: Optional approved amount.
            denial_reason: Optional denial reason.

        Returns:
            RebateApplication: The updated rebate.

        Raises:
            NotFoundError: If the rebate is not found.
        """
        item = await self.get_by_id(rebate_id, user_id)
        if not item:
            raise NotFoundError(f"Rebate with ID {rebate_id} not found")
        
        item["status"] = status.value
        
        if approved_amount is not None:
            item["approvedAmount"] = approved_amount
        
        if denial_reason is not None:
            item["denialReason"] = denial_reason
        
        # Set paid_at if status is paid
        if status == RebateStatus.PAID and not item.get("paidAt"):
            item["paidAt"] = datetime.now(timezone.utc).isoformat()
        
        updated_item = await self.update(rebate_id, user_id, item)
        return self._to_rebate(updated_item)

    def _to_rebate(self, item: Dict[str, Any]) -> RebateApplication:
        """Convert a CosmosDB document to a RebateApplication model."""
        return RebateApplication(
            application_id=item.get("applicationId", ""),
            account_number=item.get("accountNumber", ""),
            equipment_type=EquipmentType(item.get("equipmentType", "heat_pump_hvac")),
            status=RebateStatus(item.get("status", "submitted")),
            submitted_at=datetime.fromisoformat(item["submittedAt"].replace("Z", "+00:00"))
                if item.get("submittedAt") else datetime.now(timezone.utc),
            equipment_details=item.get("equipmentDetails", ""),
            estimated_rebate=item.get("estimatedRebate", 0.0),
            approved_amount=item.get("approvedAmount"),
            paid_at=datetime.fromisoformat(item["paidAt"].replace("Z", "+00:00"))
                if item.get("paidAt") else None,
            denial_reason=item.get("denialReason"),
        )
