"""Business logic and external service integration for LASAN."""

import logging
import os
import random
import string
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from .config import settings
from .models import (
    DocumentChunk,
    EligibilityResult,
    EligibleItem,
    IneligibleItem,
    KnowledgeResult,
    OnCompletePrompt,
    PickupScheduledResult,
    PickupStatus,
    PickupType,
    PreparedMaterials,
    ScheduledPickup,
    UserActionResponse,
)

logger = logging.getLogger(__name__)

# Check if CosmosDB is configured
_cosmos_enabled = bool(os.environ.get("COSMOS_ENDPOINT"))


def _get_repositories():
    """Get repository instances if CosmosDB is enabled."""
    if not _cosmos_enabled:
        return None
    
    try:
        from .repositories import PickupRepository
        return PickupRepository()
    except Exception as e:
        logger.warning(f"Failed to initialize CosmosDB repositories: {e}")
        return None


class LASANService:
    """Service layer for LASAN operations."""

    def __init__(self):
        """Initialize LASAN service."""
        self.api_endpoint = settings.lasan_api_endpoint
        self.api_key = settings.lasan_api_key
        self._pickup_repo = _get_repositories()

    @property
    def cosmos_enabled(self) -> bool:
        """Check if CosmosDB is enabled."""
        return self._pickup_repo is not None

    def _generate_id(self, prefix: str = "ID") -> str:
        """Generate a random ID."""
        random_suffix = "".join(random.choices(string.digits, k=6))
        return f"{prefix}-2026-{random_suffix}"

    async def query_knowledge_base(self, query: str, top: int = 5) -> KnowledgeResult:
        """
        Query the LASAN knowledge base (AI Search).

        This is a mock implementation.
        """
        # TODO: Replace with actual Azure AI Search call

        mock_chunks = [
            DocumentChunk(
                content="LASAN bulky item pickup service: LA residents get 10 free bulky item collections per year, up to 10 items each. Items accepted include furniture, appliances (including refrigerators with Freon), mattresses, and electronics. Place items curbside by 6am on collection day.",
                source="lasan-bulky-item-guide.pdf",
                relevance_score=0.94,
            ),
            DocumentChunk(
                content="Construction debris is NOT accepted for city pickup. This includes concrete, roof tiles, drywall, lumber, and dirt. Options for disposal: 1) Private hauling service (Junkluggers, 1-800-GOT-JUNK), 2) Self-haul to LA County landfill, 3) S.A.F.E. Centers for small quantities (weekends 9am-3pm).",
                source="lasan-what-we-collect.pdf",
                relevance_score=0.89,
            ),
            DocumentChunk(
                content="E-waste curbside pickup: Schedule through 311 or MyLA311 app. Accepted items include TVs, computers, monitors, printers, cables, and small electronics. Items must be at curb by 6am. No lithium batteries loose - tape terminals or bring to S.A.F.E. Center.",
                source="lasan-ewaste-guide.pdf",
                relevance_score=0.82,
            ),
        ]

        return KnowledgeResult(
            query=query,
            results=mock_chunks[:top],
            total_results=len(mock_chunks),
        )

    async def get_scheduled_pickups(
        self,
        address: str,
        user_id: Optional[str] = None,
    ) -> PickupScheduledResult:
        """
        Get scheduled pickups for an address.

        Uses CosmosDB if configured, otherwise returns mock data.
        """
        # Use CosmosDB if available
        if self._pickup_repo:
            try:
                pickups = []
                if user_id:
                    pickups = await self._pickup_repo.list_by_user(user_id)
                elif address:
                    pickups = await self._pickup_repo.search_by_address(address)
                return PickupScheduledResult(
                    address=address,
                    pickups=pickups,
                    total_count=len(pickups),
                )
            except Exception as e:
                logger.error(f"Error getting pickups from CosmosDB: {e}")
                # Fall through to mock data

        # Return empty for demo - pickups added as user schedules them
        return PickupScheduledResult(
            address=address,
            pickups=[],
            total_count=0,
        )

    async def prepare_pickup_scheduling(
        self,
        address: str,
        pickup_type: PickupType,
        items: List[str],
        contact_name: str,
        contact_phone: str,
    ) -> UserActionResponse:
        """
        Prepare materials for pickup scheduling (user must call 311).
        """
        pickup_name = pickup_type.value.replace("_", " ")
        items_list = ", ".join(items)

        # Determine item-specific notes
        item_notes = []
        for item in items:
            item_lower = item.lower()
            if "furnace" in item_lower or "ac" in item_lower or "refrigerator" in item_lower:
                item_notes.append(f"{item} (appliances with Freon - LASAN handles refrigerant)")
            elif "tv" in item_lower or "computer" in item_lower or "monitor" in item_lower:
                item_notes.append(f"{item} (e-waste)")
            else:
                item_notes.append(item)

        return UserActionResponse(
            requires_user_action=True,
            action_type="phone_call",
            target="311",
            reason=f"LASAN {pickup_name} pickup scheduling requires 311 call or MyLA311 app",
            prepared_materials=PreparedMaterials(
                phone_script=f"Call 311 and say: 'I need to schedule a {pickup_name} pickup at {address}. I have {items_list} to dispose of. My name is {contact_name}, phone {contact_phone}.'",
                checklist=[
                    f"Items to pick up: {', '.join(item_notes)}",
                    "Maximum 10 bulky pickups per year, up to 10 items each",
                    "Place items curbside by 6am on collection day",
                    "Do not block sidewalk or street",
                ],
                contact_info={
                    "phone": "311",
                    "hours": "24/7",
                    "app": "MyLA311 (iOS/Android)",
                    "website": "https://myla311.lacity.org",
                },
                documents_needed=[],
            ),
            on_complete=OnCompletePrompt(
                prompt="Once scheduled, please tell me the pickup date and confirmation number",
                expected_info=["scheduled_date", "confirmation_number"],
            ),
        )

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
    ) -> Optional[ScheduledPickup]:
        """
        Create a pickup record after user schedules via 311.

        Uses CosmosDB if configured, otherwise returns None.
        """
        if self._pickup_repo:
            try:
                pickup = await self._pickup_repo.create_pickup(
                    user_id=user_id,
                    pickup_type=pickup_type,
                    address=address,
                    items=items,
                    scheduled_date=scheduled_date,
                    contact_name=contact_name,
                    contact_phone=contact_phone,
                    notes=notes,
                )
                return pickup
            except Exception as e:
                logger.error(f"Error creating pickup in CosmosDB: {e}")
                return None
        return None

    async def check_pickup_eligibility(
        self,
        address: str,
        item_types: List[str],
    ) -> EligibilityResult:
        """
        Check what items are eligible for pickup.

        This is a mock implementation.
        """
        # TODO: Replace with actual LASAN API call

        eligible_items = []
        ineligible_items = []

        for item in item_types:
            item_lower = item.lower()

            # Check for construction debris (not accepted)
            if any(debris in item_lower for debris in ["concrete", "tile", "drywall", "lumber", "dirt", "brick"]):
                ineligible_items.append(
                    IneligibleItem(
                        item_type=item,
                        reason="Construction debris is not accepted for city pickup",
                        alternatives=[
                            "Private hauling service (e.g., Junkluggers, 1-800-GOT-JUNK)",
                            "Self-haul to landfill",
                            "S.A.F.E. Centers (limited quantities, weekends 9am-3pm)",
                        ],
                    )
                )
            # Check for e-waste
            elif any(ewaste in item_lower for ewaste in ["tv", "computer", "monitor", "cable", "wire", "panel", "electronic"]):
                eligible_items.append(
                    EligibleItem(
                        item_type=item,
                        pickup_type=PickupType.EWASTE,
                        notes="E-waste curbside pickup available",
                    )
                )
            # Check for appliances with refrigerant
            elif any(appliance in item_lower for appliance in ["furnace", "ac", "air condition", "refrigerator", "freezer"]):
                eligible_items.append(
                    EligibleItem(
                        item_type=item,
                        pickup_type=PickupType.BULKY_ITEM,
                        notes="Freon-containing appliances accepted; LASAN handles refrigerant disposal",
                    )
                )
            # Check for hazardous materials
            elif any(hazard in item_lower for hazard in ["paint", "battery", "chemical", "oil", "pesticide"]):
                eligible_items.append(
                    EligibleItem(
                        item_type=item,
                        pickup_type=PickupType.HAZARDOUS,
                        notes="Hazardous materials - take to S.A.F.E. Center or schedule HHW pickup",
                    )
                )
            # Default to bulky item
            else:
                eligible_items.append(
                    EligibleItem(
                        item_type=item,
                        pickup_type=PickupType.BULKY_ITEM,
                        notes="Standard bulky item pickup",
                    )
                )

        return EligibilityResult(
            address=address,
            eligible_items=eligible_items,
            ineligible_items=ineligible_items,
            annual_limit=10,
            collections_used=2,  # Mock value
            collections_remaining=8,
        )
