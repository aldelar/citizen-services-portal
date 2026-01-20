"""MCP tools for LADBS services."""

from typing import Dict, Any
from datetime import datetime
from .models import PermitApplication, PermitStatus, InspectionRequest, ViolationReport
from .services import LADBSService


class LADBSTools:
    """LADBS MCP tools implementation."""

    def __init__(self):
        """Initialize LADBS tools with service layer."""
        self.service = LADBSService()

    async def submit_permit_application(
        self,
        applicant_name: str,
        property_address: str,
        work_description: str,
        estimated_cost: float,
    ) -> Dict[str, Any]:
        """
        Submit a building permit application.

        Args:
            applicant_name: Name of the applicant
            property_address: Property address
            work_description: Description of proposed work
            estimated_cost: Estimated cost of work

        Returns:
            Application confirmation with permit number
        """
        application = PermitApplication(
            applicant_name=applicant_name,
            property_address=property_address,
            work_description=work_description,
            estimated_cost=estimated_cost,
            submitted_at=datetime.now(),
        )

        result = await self.service.submit_permit(application)
        return result

    async def check_permit_status(self, permit_number: str) -> Dict[str, Any]:
        """
        Check the status of a building permit.

        Args:
            permit_number: Permit number to check

        Returns:
            Current permit status information
        """
        status = await self.service.get_permit_status(permit_number)
        return status.model_dump() if status else {"error": "Permit not found"}

    async def schedule_inspection(
        self,
        permit_number: str,
        inspection_type: str,
        requested_date: str,
        contact_name: str,
        contact_phone: str,
    ) -> Dict[str, Any]:
        """
        Schedule a building inspection.

        Args:
            permit_number: Permit number
            inspection_type: Type of inspection (foundation, framing, final, etc.)
            requested_date: Requested inspection date (YYYY-MM-DD)
            contact_name: Contact person name
            contact_phone: Contact phone number

        Returns:
            Inspection confirmation details
        """
        request = InspectionRequest(
            permit_number=permit_number,
            inspection_type=inspection_type,
            requested_date=datetime.fromisoformat(requested_date),
            contact_name=contact_name,
            contact_phone=contact_phone,
        )

        result = await self.service.schedule_inspection(request)
        return result

    async def report_violation(
        self,
        property_address: str,
        violation_type: str,
        description: str,
        reporter_name: str | None = None,
        reporter_contact: str | None = None,
    ) -> Dict[str, Any]:
        """
        Report a code violation.

        Args:
            property_address: Address of violation
            violation_type: Type of violation
            description: Detailed description
            reporter_name: Reporter name (optional)
            reporter_contact: Reporter contact (optional)

        Returns:
            Violation report confirmation
        """
        report = ViolationReport(
            property_address=property_address,
            violation_type=violation_type,
            description=description,
            reporter_name=reporter_name,
            reporter_contact=reporter_contact,
            reported_at=datetime.now(),
        )

        result = await self.service.report_violation(report)
        return result
