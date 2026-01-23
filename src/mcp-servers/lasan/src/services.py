"""Business logic and external service integration for LASAN."""

import random
import string
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from .config import settings
from .models import (
    BinReplacementRequest,
    BulkyPickupRequest,
    BulkyPickupStatus,
    CollectionSchedule,
    DumpingReportStatus,
    IllegalDumpingReport,
    MissedCollectionReport,
)


class LASANService:
    """Service layer for LASAN operations."""

    def __init__(self):
        """Initialize LASAN service."""
        self.api_endpoint = settings.lasan_api_endpoint
        self.api_key = settings.lasan_api_key

    def _generate_id(self, prefix: str = "ID") -> str:
        """Generate a random ID."""
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{prefix}-{random_suffix}"

    async def get_collection_schedule(self, address: str) -> CollectionSchedule:
        """
        Get collection schedule for an address.

        This is a mock implementation. Replace with actual LASAN API integration.
        """
        # TODO: Replace with actual LASAN API call

        # Mock response with rotating days based on address
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        trash_day_idx = hash(address) % 5
        recycling_day_idx = (trash_day_idx + 3) % 5
        green_waste_day_idx = (trash_day_idx + 1) % 5

        next_pickup = date.today() + timedelta(days=(trash_day_idx - date.today().weekday()) % 7 + 1)

        return CollectionSchedule(
            address=address,
            trash_day=days[trash_day_idx],
            recycling_day=days[recycling_day_idx],
            green_waste_day=days[green_waste_day_idx],
            next_pickup=next_pickup,
            holiday_adjustments=[
                {"holiday": "Memorial Day", "date": "2026-05-25", "adjustment": "Delayed by 1 day"},
                {"holiday": "Independence Day", "date": "2026-07-04", "adjustment": "Delayed by 1 day"},
            ],
        )

    async def schedule_bulky_pickup(self, request: BulkyPickupRequest) -> Dict[str, Any]:
        """
        Schedule a bulky item pickup.

        This is a mock implementation. Replace with actual LASAN API integration.
        """
        # TODO: Replace with actual LASAN API call

        request_id = self._generate_id("BULKY")

        return {
            "success": True,
            "request_id": request_id,
            "address": request.address,
            "contact_name": request.contact_name,
            "contact_phone": request.contact_phone,
            "items": request.items,
            "scheduled_date": request.preferred_date.isoformat(),
            "status": "scheduled",
            "message": (
                f"Bulky item pickup scheduled for {request.preferred_date.strftime('%Y-%m-%d')}. "
                f"Request ID: {request_id}. Please place items at curb by 6 AM on pickup day."
            ),
        }

    async def check_pickup_status(self, request_id: str) -> Optional[BulkyPickupStatus]:
        """
        Check status of a bulky item pickup request.

        This is a mock implementation. Replace with actual LASAN API integration.
        """
        # TODO: Replace with actual LASAN API call

        # Mock response
        statuses = ["scheduled", "confirmed", "completed"]
        status = random.choice(statuses)

        return BulkyPickupStatus(
            request_id=request_id,
            status=status,
            scheduled_date=date.today() + timedelta(days=random.randint(1, 7)),
            items=["sofa", "mattress", "refrigerator"],
            notes="Crew will arrive between 7 AM and 3 PM." if status != "completed" else "Pickup completed.",
        )

    async def report_illegal_dumping(self, report: IllegalDumpingReport) -> Dict[str, Any]:
        """
        Report illegal dumping.

        This is a mock implementation. Replace with actual LASAN API integration.
        """
        # TODO: Replace with actual LASAN API call

        report_id = self._generate_id("DUMP")

        return {
            "success": True,
            "report_id": report_id,
            "location": report.location_address,
            "description": report.description,
            "materials": report.materials,
            "status": "received",
            "reported_at": report.reported_at.isoformat(),
            "message": (
                f"Illegal dumping report received. Report ID: {report_id}. "
                "Investigation will begin within 24-48 hours."
            ),
        }

    async def check_dumping_report_status(self, report_id: str) -> Optional[DumpingReportStatus]:
        """
        Check status of an illegal dumping report.

        This is a mock implementation. Replace with actual LASAN API integration.
        """
        # TODO: Replace with actual LASAN API call

        # Mock response
        statuses = ["received", "investigating", "cleanup_scheduled", "resolved"]
        status = random.choice(statuses)

        status_notes = {
            "received": "Report received and pending review.",
            "investigating": "Investigation team has been dispatched to assess the situation.",
            "cleanup_scheduled": "Cleanup has been scheduled for within 3 business days.",
            "resolved": "Cleanup completed. Area has been restored.",
        }

        return DumpingReportStatus(
            report_id=report_id,
            status=status,
            location="Location under investigation",
            last_updated=datetime.now(),
            notes=status_notes[status],
        )

    async def request_bin_replacement(self, request: BinReplacementRequest) -> Dict[str, Any]:
        """
        Request bin replacement.

        This is a mock implementation. Replace with actual LASAN API integration.
        """
        # TODO: Replace with actual LASAN API call

        request_id = self._generate_id("BIN")

        bin_names = {
            "black": "Black Trash Bin",
            "blue": "Blue Recycling Bin",
            "green": "Green Waste Bin",
        }

        return {
            "success": True,
            "request_id": request_id,
            "address": request.address,
            "bin_type": bin_names.get(request.bin_type.value, request.bin_type.value),
            "reason": request.reason,
            "status": "scheduled",
            "estimated_delivery": (date.today() + timedelta(days=random.randint(3, 7))).isoformat(),
            "message": (
                f"Bin replacement request received. Request ID: {request_id}. "
                f"Your new {bin_names.get(request.bin_type.value)} will be delivered within 3-7 business days."
            ),
        }

    async def get_recycling_info(self, material: str = "") -> Dict[str, Any]:
        """
        Get recycling information.

        This is a mock implementation. Replace with actual LASAN API integration.
        """
        # TODO: Replace with actual LASAN API call

        recycling_guidelines = {
            "accepted_materials": [
                "Paper (newspapers, magazines, office paper, cardboard)",
                "Plastic bottles and containers (#1-#7)",
                "Glass bottles and jars",
                "Aluminum and steel cans",
                "Cartons (milk, juice, soup containers)",
            ],
            "not_accepted": [
                "Plastic bags (take to store drop-off)",
                "Styrofoam",
                "Food waste (use green waste bin)",
                "Hazardous materials",
                "Electronic waste (schedule e-waste pickup)",
            ],
            "preparation_tips": [
                "Rinse containers to remove food residue",
                "Remove caps and lids",
                "Flatten cardboard boxes",
                "Keep materials loose (no bags)",
            ],
        }

        if material:
            material_lower = material.lower()
            # Provide specific info for requested material
            material_specific = {
                "plastic": {
                    "accepted": True,
                    "details": "Plastic bottles and containers (#1-#7) are accepted. Rinse and remove caps.",
                    "special_notes": "Plastic bags should be taken to store drop-off locations.",
                },
                "glass": {
                    "accepted": True,
                    "details": "Glass bottles and jars of all colors are accepted. Rinse clean.",
                    "special_notes": "Remove metal lids. Broken glass should be wrapped and placed in trash.",
                },
                "paper": {
                    "accepted": True,
                    "details": "All paper including newspapers, magazines, and office paper are accepted.",
                    "special_notes": "Shredded paper should be in a paper bag. No wet or food-soiled paper.",
                },
                "cardboard": {
                    "accepted": True,
                    "details": "Cardboard and corrugated boxes are accepted. Flatten boxes.",
                    "special_notes": "Remove all packing materials and tape if possible.",
                },
                "electronics": {
                    "accepted": False,
                    "details": "Electronics require special e-waste pickup.",
                    "special_notes": "Schedule a bulky item pickup for electronics or take to e-waste facility.",
                },
            }

            specific_info = material_specific.get(material_lower, {
                "accepted": "Unknown",
                "details": f"For specific information about {material}, please contact LASAN at 1-800-773-2489.",
            })

            return {
                "material_query": material,
                **specific_info,
                "general_guidelines": recycling_guidelines,
            }

        return recycling_guidelines

    async def report_missed_collection(self, report: MissedCollectionReport) -> Dict[str, Any]:
        """
        Report a missed collection.

        This is a mock implementation. Replace with actual LASAN API integration.
        """
        # TODO: Replace with actual LASAN API call

        report_id = self._generate_id("MISS")

        collection_names = {
            "trash": "Trash",
            "recycling": "Recycling",
            "green_waste": "Green Waste",
        }

        return {
            "success": True,
            "report_id": report_id,
            "address": report.address,
            "collection_type": collection_names.get(report.collection_type.value, report.collection_type.value),
            "scheduled_date": report.scheduled_date.isoformat(),
            "status": "received",
            "follow_up_date": (date.today() + timedelta(days=1)).isoformat(),
            "message": (
                f"Missed collection report received. Report ID: {report_id}. "
                "We will attempt to service your location within 1 business day. "
                "Please ensure containers are accessible at the curb."
            ),
        }
