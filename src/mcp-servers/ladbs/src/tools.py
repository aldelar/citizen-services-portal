"""MCP tools for LADBS services."""

from typing import Any, Dict, List, Optional, Union

from .models import (
    Applicant,
    Inspection,
    InspectionListResult,
    InspectionStatus,
    InspectionType,
    KnowledgeResult,
    Permit,
    PermitSearchResult,
    PermitStatus,
    PermitSubmitResult,
    PermitType,
    UserActionResponse,
)
from .services import LADBSService


class LADBSTools:
    """LADBS MCP tools implementation."""

    def __init__(self):
        """Initialize LADBS tools with service layer."""
        self.service = LADBSService()

    async def queryKB(
        self,
        query: str,
        top: int = 5,
    ) -> Dict[str, Any]:
        """
        Search LADBS knowledge base for permit requirements, fees, processes.

        Args:
            query: Natural language query
            top: Number of results to return (default 5)

        Returns:
            KnowledgeResult with matching document chunks
        """
        result = await self.service.query_knowledge_base(query, top)
        return result.model_dump(mode="json")

    async def permits_search(
        self,
        user_id: Optional[str] = None,
        address: Optional[str] = None,
        permit_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find existing permits by address or permit number.

        Args:
            user_id: Optional user ID for optimized partition-aware query
            address: Property address to search
            permit_number: Specific permit number to look up

        Returns:
            PermitSearchResult with matching permits
        """
        result = await self.service.search_permits(
            user_id=user_id, address=address, permit_number=permit_number
        )
        return result.model_dump(mode="json")

    async def permits_submit(
        self,
        user_id: str,
        permit_type: str,
        address: str,
        applicant_name: str,
        applicant_email: str,
        applicant_phone: str,
        work_description: str,
        estimated_cost: float,
        documents: List[str],
        contractor_license: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a new permit application.

        Args:
            user_id: User ID (required for creating permit in CosmosDB)
            permit_type: Type of permit (electrical, mechanical, building, plumbing)
            address: Property address
            applicant_name: Applicant's name
            applicant_email: Applicant's email
            applicant_phone: Applicant's phone number
            work_description: Description of the proposed work
            estimated_cost: Estimated cost of the work
            documents: List of document references/URLs
            contractor_license: Contractor license number (optional)

        Returns:
            PermitSubmitResult with permit number and next steps
        """
        applicant = Applicant(
            name=applicant_name,
            email=applicant_email,
            phone=applicant_phone,
            contractor_license=contractor_license,
        )
        result = await self.service.submit_permit(
            user_id=user_id,
            permit_type=PermitType(permit_type),
            address=address,
            applicant=applicant,
            work_description=work_description,
            estimated_cost=estimated_cost,
            documents=documents,
        )
        return result.model_dump(mode="json")

    async def permits_getStatus(
        self,
        permit_number: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check the current status of a permit.

        Args:
            permit_number: Permit number to check
            user_id: Optional user ID for optimized partition-aware query

        Returns:
            Permit with current status and next steps
        """
        result = await self.service.get_permit_status(permit_number, user_id=user_id)
        return result.model_dump(mode="json")

    async def inspections_scheduled(
        self,
        user_id: Optional[str] = None,
        permit_number: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        View scheduled inspections for a permit or address.

        Args:
            user_id: Optional user ID for optimized queries
            permit_number: Permit number to look up inspections for
            address: Address to look up inspections for

        Returns:
            InspectionListResult with scheduled inspections
        """
        result = await self.service.get_scheduled_inspections(
            user_id=user_id,
            permit_number=permit_number,
            address=address,
        )
        return result.model_dump(mode="json")

    async def inspections_schedule(
        self,
        permit_number: str,
        inspection_type: str,
        address: str,
        contact_name: str,
        contact_phone: str,
    ) -> Dict[str, Any]:
        """
        Prepare materials for scheduling an inspection (requires user action - phone call to 311).

        Args:
            permit_number: Permit number for the inspection
            inspection_type: Type of inspection (rough_electrical, final_electrical, etc.)
            address: Property address
            contact_name: Contact person's name
            contact_phone: Contact phone number

        Returns:
            UserActionResponse with phone script and checklist
        """
        result = await self.service.prepare_inspection_scheduling(
            permit_number=permit_number,
            inspection_type=InspectionType(inspection_type),
            address=address,
            contact_name=contact_name,
            contact_phone=contact_phone,
        )
        return result.model_dump(mode="json")
