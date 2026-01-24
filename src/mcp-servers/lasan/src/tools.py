"""MCP tools for LASAN services."""

from typing import Any, Dict, List

from .models import (
    EligibilityResult,
    KnowledgeResult,
    PickupScheduledResult,
    PickupType,
    ScheduledPickup,
    UserActionResponse,
)
from .services import LASANService


class LASANTools:
    """LASAN MCP tools implementation."""

    def __init__(self):
        """Initialize LASAN tools with service layer."""
        self.service = LASANService()

    async def queryKB(
        self,
        query: str,
        top: int = 5,
    ) -> Dict[str, Any]:
        """
        Search LASAN knowledge base for disposal guidelines, recycling info.

        Args:
            query: Natural language query
            top: Number of results to return (default 5)

        Returns:
            KnowledgeResult with matching document chunks
        """
        result = await self.service.query_knowledge_base(query, top)
        return result.model_dump()

    async def pickup_scheduled(
        self,
        address: str,
    ) -> Dict[str, Any]:
        """
        View scheduled pickups for an address.

        Args:
            address: Street address to check

        Returns:
            PickupScheduledResult with scheduled pickups
        """
        result = await self.service.get_scheduled_pickups(address)
        return result.model_dump()

    async def pickup_schedule(
        self,
        address: str,
        pickup_type: str,
        items: List[str],
        contact_name: str,
        contact_phone: str,
    ) -> Dict[str, Any]:
        """
        Prepare pickup scheduling request (requires user action - 311 call or MyLA311 app).

        Args:
            address: Pickup address
            pickup_type: Type of pickup (bulky_item, ewaste, hazardous)
            items: List of items to pick up
            contact_name: Contact person's name
            contact_phone: Contact phone number

        Returns:
            UserActionResponse with phone script and checklist
        """
        result = await self.service.prepare_pickup_scheduling(
            address=address,
            pickup_type=PickupType(pickup_type),
            items=items,
            contact_name=contact_name,
            contact_phone=contact_phone,
        )
        return result.model_dump()

    async def pickup_getEligibility(
        self,
        address: str,
        item_types: List[str],
    ) -> Dict[str, Any]:
        """
        Check what items are eligible for pickup at an address.

        Args:
            address: Street address
            item_types: List of items to check eligibility for

        Returns:
            EligibilityResult with eligible/ineligible items and alternatives
        """
        result = await self.service.check_pickup_eligibility(address, item_types)
        return result.model_dump()
