"""MCP tools for LASAN services."""

from datetime import date, datetime
from typing import Any, Dict, List

from .models import (
    BinReplacementRequest,
    BinType,
    BulkyPickupRequest,
    CollectionType,
    IllegalDumpingReport,
    MissedCollectionReport,
)
from .services import LASANService


class LASANTools:
    """LASAN MCP tools implementation."""

    def __init__(self):
        """Initialize LASAN tools with service layer."""
        self.service = LASANService()

class LASANTools:
    """LASAN MCP tools implementation."""

    def __init__(self):
        """Initialize LASAN tools with service layer."""
        self.service = LASANService()

    async def get_collection_schedule(self, address: str) -> Dict[str, Any]:
        """
        Get trash and recycling collection schedule for an address.

        Args:
            address: Street address to check

        Returns:
            Collection schedule with pickup days
        """
        schedule = await self.service.get_collection_schedule(address)
        return schedule.model_dump()

    async def schedule_bulky_pickup(
        self,
        address: str,
        contact_name: str,
        contact_phone: str,
        items: List[str],
        preferred_date: str,
        special_instructions: str = "",
    ) -> Dict[str, Any]:
        """
        Schedule a bulky item pickup.

        Args:
            address: Pickup address
            contact_name: Contact person name
            contact_phone: Contact phone number
            items: List of items to pick up (e.g., ["sofa", "mattress", "refrigerator"])
            preferred_date: Preferred pickup date (YYYY-MM-DD)
            special_instructions: Any special instructions

        Returns:
            Pickup request confirmation with request ID
        """
        request = BulkyPickupRequest(
            address=address,
            contact_name=contact_name,
            contact_phone=contact_phone,
            items=items,
            preferred_date=date.fromisoformat(preferred_date),
            special_instructions=special_instructions or None,
            requested_at=datetime.now(),
        )
        result = await self.service.schedule_bulky_pickup(request)
        return result

    async def check_pickup_status(self, request_id: str) -> Dict[str, Any]:
        """
        Check status of a bulky item pickup request.

        Args:
            request_id: The pickup request ID

        Returns:
            Current status of the pickup request
        """
        status = await self.service.check_pickup_status(request_id)
        return status.model_dump() if status else {"error": "Request not found"}

    async def report_illegal_dumping(
        self,
        location_address: str,
        description: str,
        materials: List[str],
        reporter_name: str = "",
        reporter_phone: str = "",
    ) -> Dict[str, Any]:
        """
        Report illegal dumping at a location.

        Args:
            location_address: Address or location description where dumping occurred
            description: Description of the dumping
            materials: Types of materials dumped (e.g., ["construction debris", "furniture", "tires"])
            reporter_name: Optional reporter name
            reporter_phone: Optional reporter phone

        Returns:
            Report confirmation with report ID
        """
        report = IllegalDumpingReport(
            location_address=location_address,
            description=description,
            materials=materials,
            reporter_name=reporter_name or None,
            reporter_phone=reporter_phone or None,
            reported_at=datetime.now(),
        )
        result = await self.service.report_illegal_dumping(report)
        return result

    async def check_dumping_report_status(self, report_id: str) -> Dict[str, Any]:
        """
        Check status of an illegal dumping report.

        Args:
            report_id: The report ID

        Returns:
            Current status of the report
        """
        status = await self.service.check_dumping_report_status(report_id)
        return status.model_dump() if status else {"error": "Report not found"}

    async def request_bin_replacement(
        self,
        address: str,
        bin_type: str,
        reason: str,
        contact_name: str,
        contact_phone: str,
    ) -> Dict[str, Any]:
        """
        Request replacement of a trash, recycling, or green waste bin.

        Args:
            address: Service address
            bin_type: Type of bin (black, blue, or green)
            reason: Reason for replacement (damaged, missing, stolen, wrong_size)
            contact_name: Contact person name
            contact_phone: Contact phone number

        Returns:
            Replacement request confirmation
        """
        request = BinReplacementRequest(
            address=address,
            bin_type=BinType(bin_type.lower()),
            reason=reason,
            contact_name=contact_name,
            contact_phone=contact_phone,
            requested_at=datetime.now(),
        )
        result = await self.service.request_bin_replacement(request)
        return result

    async def get_recycling_info(self, material: str = "") -> Dict[str, Any]:
        """
        Get recycling guidelines and information.

        Args:
            material: Optional specific material to check (e.g., "plastic", "glass", "electronics")

        Returns:
            Recycling guidelines and accepted materials
        """
        info = await self.service.get_recycling_info(material)
        return info

    async def report_missed_collection(
        self,
        address: str,
        collection_type: str,
        scheduled_date: str,
        contact_name: str,
        contact_phone: str,
    ) -> Dict[str, Any]:
        """
        Report a missed trash or recycling collection.

        Args:
            address: Service address
            collection_type: Type of collection (trash, recycling, green_waste)
            scheduled_date: The date collection was supposed to occur (YYYY-MM-DD)
            contact_name: Contact person name
            contact_phone: Contact phone number

        Returns:
            Report confirmation with follow-up information
        """
        report = MissedCollectionReport(
            address=address,
            collection_type=CollectionType(collection_type.lower()),
            scheduled_date=date.fromisoformat(scheduled_date),
            contact_name=contact_name,
            contact_phone=contact_phone,
            reported_at=datetime.now(),
        )
        result = await self.service.report_missed_collection(report)
        return result
