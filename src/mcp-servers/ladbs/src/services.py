"""Business logic and external service integration for LADBS."""

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .config import settings
from .models import (
    Applicant,
    DocumentChunk,
    Inspection,
    InspectionListResult,
    InspectionStatus,
    InspectionType,
    KnowledgeResult,
    OnCompletePrompt,
    Permit,
    PermitFees,
    PermitSearchResult,
    PermitStatus,
    PermitSubmitResult,
    PermitType,
    PreparedMaterials,
    UserActionResponse,
)


class LADBSService:
    """Service layer for LADBS operations."""

    def __init__(self):
        """Initialize LADBS service."""
        self.api_endpoint = settings.ladbs_api_endpoint
        self.api_key = settings.ladbs_api_key

    def _generate_id(self, prefix: str = "ID") -> str:
        """Generate a random ID."""
        random_suffix = "".join(random.choices(string.digits, k=6))
        return f"{prefix}-2026-{random_suffix}"

    async def query_knowledge_base(self, query: str, top: int = 5) -> KnowledgeResult:
        """
        Query the LADBS knowledge base (AI Search).

        This is a mock implementation. Replace with actual Azure AI Search integration.
        """
        # TODO: Replace with actual Azure AI Search call
        # Example:
        # search_client = SearchClient(endpoint, index_name, credential)
        # results = search_client.search(query, top=top)

        # Mock response with realistic LADBS content
        mock_chunks = [
            DocumentChunk(
                content="For electrical permits involving solar PV systems, you need: 1) Site plan showing panel layout, 2) Single-line electrical diagram, 3) Equipment specifications (inverter, panels), 4) Structural calculations for roof mounting, 5) C-10 contractor license documentation.",
                source="ladbs-electrical-permits.pdf",
                relevance_score=0.94,
            ),
            DocumentChunk(
                content="Electrical permit fees for solar installations: Plan check fee is typically $450 for residential systems under 10kW. Permit fee is based on valuation, approximately $800 for a standard residential solar installation. Additional fees may apply for battery storage systems.",
                source="ladbs-fee-schedule-2026.pdf",
                relevance_score=0.87,
            ),
            DocumentChunk(
                content="Inspection requirements for solar PV: 1) Rough electrical inspection after conduit and wiring installation, before covering. 2) Final electrical inspection after all equipment is installed and operational. Both inspections must pass before interconnection.",
                source="ladbs-inspection-guide.pdf",
                relevance_score=0.82,
            ),
        ]

        return KnowledgeResult(
            query=query,
            results=mock_chunks[:top],
            total_results=len(mock_chunks),
        )

    async def search_permits(
        self,
        address: Optional[str] = None,
        permit_number: Optional[str] = None,
    ) -> PermitSearchResult:
        """
        Search for permits by address or permit number.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADBS API call

        if permit_number:
            # Return specific permit
            permit = Permit(
                permit_number=permit_number,
                permit_type=PermitType.ELECTRICAL,
                status=PermitStatus.APPROVED,
                address=address or "123 Main St, Los Angeles, CA 90012",
                description="Solar PV installation with battery storage",
                applicant_name="John Smith",
                submitted_at=datetime(2026, 1, 15, 10, 0, 0),
                approved_at=datetime(2026, 1, 28, 14, 30, 0),
                expires_at=datetime(2027, 1, 28),
                fees=PermitFees(plan_check=450, permit_fee=800, other_fees=0, total=1250),
                next_steps="Schedule rough electrical inspection before starting work",
            )
            return PermitSearchResult(permits=[permit], total_count=1)

        if address:
            # Return permits for address
            permit = Permit(
                permit_number=self._generate_id("PERMIT"),
                permit_type=PermitType.ELECTRICAL,
                status=PermitStatus.SUBMITTED,
                address=address,
                description="Electrical upgrade",
                applicant_name="Property Owner",
                submitted_at=datetime.now() - timedelta(days=7),
                fees=PermitFees(plan_check=200, permit_fee=350, other_fees=0, total=550),
                next_steps="Awaiting plan review",
            )
            return PermitSearchResult(permits=[permit], total_count=1)

        return PermitSearchResult(permits=[], total_count=0)

    async def submit_permit(
        self,
        permit_type: PermitType,
        address: str,
        applicant: Applicant,
        work_description: str,
        estimated_cost: float,
        documents: List[str],
    ) -> PermitSubmitResult:
        """
        Submit a new permit application.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADBS API call

        permit_number = self._generate_id("PERMIT")

        # Calculate fees based on estimated cost
        plan_check = round(estimated_cost * 0.018, 2)  # ~1.8% of project cost
        permit_fee = round(estimated_cost * 0.032, 2)  # ~3.2% of project cost
        total = round(plan_check + permit_fee, 2)

        return PermitSubmitResult(
            success=True,
            permit_number=permit_number,
            status=PermitStatus.SUBMITTED,
            submitted_at=datetime.now(),
            fees=PermitFees(plan_check=plan_check, permit_fee=permit_fee, other_fees=0, total=total),
            estimated_review_time="4-6 weeks",
            next_steps="You'll receive email updates on review progress. Plan check fees are due within 30 days.",
        )

    async def get_permit_status(self, permit_number: str) -> Permit:
        """
        Get the current status of a permit.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADBS API call

        # Mock response - would query database in real implementation
        return Permit(
            permit_number=permit_number,
            permit_type=PermitType.ELECTRICAL,
            status=PermitStatus.APPROVED,
            address="123 Main St, Los Angeles, CA 90012",
            description="Solar PV installation with battery storage",
            applicant_name="John Smith",
            submitted_at=datetime(2026, 1, 15, 10, 0, 0),
            approved_at=datetime(2026, 1, 28, 14, 30, 0),
            expires_at=datetime(2027, 1, 28),
            fees=PermitFees(plan_check=450, permit_fee=800, other_fees=0, total=1250),
            next_steps="Schedule rough electrical inspection before starting work",
        )

    async def get_scheduled_inspections(
        self,
        permit_number: Optional[str] = None,
        address: Optional[str] = None,
    ) -> InspectionListResult:
        """
        Get scheduled inspections for a permit or address.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADBS API call

        inspections = []
        if permit_number or address:
            inspections = [
                Inspection(
                    inspection_id=self._generate_id("INS"),
                    permit_number=permit_number or "PERMIT-2026-001234",
                    inspection_type=InspectionType.ROUGH_ELECTRICAL,
                    status=InspectionStatus.SCHEDULED,
                    scheduled_date=datetime.now() + timedelta(days=3),
                    scheduled_time_window="8am-12pm",
                ),
            ]

        return InspectionListResult(inspections=inspections, total_count=len(inspections))

    async def prepare_inspection_scheduling(
        self,
        permit_number: str,
        inspection_type: InspectionType,
        address: str,
        contact_name: str,
        contact_phone: str,
    ) -> UserActionResponse:
        """
        Prepare materials for inspection scheduling (user must call 311).

        This returns prepared materials since inspection scheduling requires a phone call.
        """
        inspection_name = inspection_type.value.replace("_", " ")

        return UserActionResponse(
            requires_user_action=True,
            action_type="phone_call",
            target="311",
            reason="LADBS inspection scheduling is only available via phone or the LADBS website",
            prepared_materials=PreparedMaterials(
                phone_script=f"Call 311 and say: 'I need to schedule a {inspection_name} inspection for permit number {permit_number} at {address}. My name is {contact_name} and my phone number is {contact_phone}.'",
                checklist=[
                    f"Have permit number ready: {permit_number}",
                    "Confirm work is ready for inspection (wiring complete, accessible)",
                    "Request morning slot (8am-12pm) if preferred",
                    "Note: 24-48 hours advance notice typically required",
                ],
                contact_info={
                    "phone": "311",
                    "hours": "24/7",
                    "alternative": "https://www.ladbs.org/inspections",
                },
                documents_needed=[],
            ),
            on_complete=OnCompletePrompt(
                prompt="Once scheduled, please tell me the inspection date and confirmation number",
                expected_info=["scheduled_date", "confirmation_number", "time_window"],
            ),
        )
