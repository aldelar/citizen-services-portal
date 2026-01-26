"""Business logic and external service integration for LADBS."""

import logging
import os
import random
import string
from datetime import datetime, timedelta, timezone
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

logger = logging.getLogger(__name__)

# Check if CosmosDB is configured
_cosmos_enabled = bool(os.environ.get("COSMOS_ENDPOINT"))

# Check if Azure AI Search is configured
_search_enabled = bool(os.environ.get("AZURE_SEARCH_ENDPOINT"))

# Search configuration
_SEARCH_INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME", "ladbs-kb")
_SEARCH_SEMANTIC_CONFIG = os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIG", "ladbs-semantic-config")
_SEARCH_SELECT_FIELDS = ["chunk", "source_file", "title", "header_1", "header_2"]
_MAX_RERANKER_SCORE = 4.0  # Azure AI Search semantic reranker score typically ranges 0-4


def _get_repositories():
    """Get repository instances if CosmosDB is enabled."""
    if not _cosmos_enabled:
        return None, None
    
    try:
        from .repositories import PermitRepository, InspectionRepository
        return PermitRepository(), InspectionRepository()
    except Exception as e:
        logger.warning(f"Failed to initialize CosmosDB repositories: {e}")
        return None, None


class LADBSService:
    """Service layer for LADBS operations."""

    def __init__(self):
        """Initialize LADBS service."""
        self.api_endpoint = settings.ladbs_api_endpoint
        self.api_key = settings.ladbs_api_key
        self._permit_repo, self._inspection_repo = _get_repositories()
        self._search_client = self._init_search_client()

    def _init_search_client(self):
        """Initialize Azure AI Search client if configured."""
        if not _search_enabled:
            return None
        
        try:
            from azure.identity import DefaultAzureCredential
            from azure.search.documents import SearchClient
            
            return SearchClient(
                endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
                index_name=_SEARCH_INDEX_NAME,
                credential=DefaultAzureCredential()
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Azure AI Search client: {e}")
            return None

    @property
    def cosmos_enabled(self) -> bool:
        """Check if CosmosDB is enabled."""
        return self._permit_repo is not None
    
    @property
    def search_enabled(self) -> bool:
        """Check if Azure AI Search is enabled."""
        return self._search_client is not None

    def _generate_id(self, prefix: str = "ID") -> str:
        """Generate a random ID."""
        random_suffix = "".join(random.choices(string.digits, k=6))
        return f"{prefix}-2026-{random_suffix}"

    async def query_knowledge_base(self, query: str, top: int = 5) -> KnowledgeResult:
        """
        Query the LADBS knowledge base using Azure AI Search.

        Uses semantic search with the ladbs-kb index when configured,
        otherwise returns mock data.
        """
        # Use Azure AI Search if available
        if self._search_client:
            try:
                results = self._search_client.search(
                    search_text=query,
                    query_type="semantic",
                    semantic_configuration_name=_SEARCH_SEMANTIC_CONFIG,
                    top=top,
                    select=_SEARCH_SELECT_FIELDS
                )
                
                chunks = []
                for result in results:
                    # Normalize reranker score to 0-1 range
                    relevance_score = result.get("@search.reranker_score", 0) / _MAX_RERANKER_SCORE
                    relevance_score = max(0.0, min(1.0, relevance_score))
                    
                    chunks.append(DocumentChunk(
                        content=result["chunk"],
                        source=result["source_file"],
                        relevance_score=relevance_score
                    ))
                
                return KnowledgeResult(
                    query=query,
                    results=chunks,
                    total_results=len(chunks)
                )
            except Exception as e:
                logger.error(f"Error querying Azure AI Search: {e}")
                # Fall through to mock data

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
        user_id: Optional[str] = None,
        address: Optional[str] = None,
        permit_number: Optional[str] = None,
    ) -> PermitSearchResult:
        """
        Search for permits by address or permit number.

        Uses CosmosDB if configured, otherwise returns mock data.
        
        Args:
            user_id: Optional user ID for optimized partition-aware query
            address: Optional address to search by
            permit_number: Optional permit number to search by
        """
        # Use CosmosDB if available
        if self._permit_repo:
            try:
                permits = []
                if permit_number:
                    permit = await self._permit_repo.get_by_permit_number(
                        permit_number, user_id=user_id
                    )
                    if permit:
                        permits = [permit]
                elif address:
                    permits = await self._permit_repo.search_by_address(
                        address, user_id=user_id
                    )
                elif user_id:
                    permits = await self._permit_repo.list_by_user(user_id)
                return PermitSearchResult(permits=permits, total_count=len(permits))
            except Exception as e:
                logger.error(f"Error searching permits in CosmosDB: {e}")
                # Fall through to mock data

        # Mock implementation for local development
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
        user_id: str,
        permit_type: PermitType,
        address: str,
        applicant: Applicant,
        work_description: str,
        estimated_cost: float,
        documents: List[str],
    ) -> PermitSubmitResult:
        """
        Submit a new permit application.

        Uses CosmosDB if configured, otherwise returns mock data.
        
        Args:
            user_id: User ID (required for CosmosDB partition key)
            permit_type: Type of permit
            address: Property address
            applicant: Applicant information
            work_description: Description of work
            estimated_cost: Estimated cost
            documents: List of document names
        """
        # Use CosmosDB if available
        if self._permit_repo:
            try:
                permit = await self._permit_repo.create_permit(
                    user_id=user_id,
                    permit_type=permit_type,
                    address=address,
                    work_description=work_description,
                    estimated_cost=estimated_cost,
                    applicant=applicant,
                    documents=documents,
                )
                return PermitSubmitResult(
                    success=True,
                    permit_number=permit.permit_number,
                    status=permit.status,
                    submitted_at=permit.submitted_at,
                    fees=permit.fees or PermitFees(plan_check=0, permit_fee=0, other_fees=0, total=0),
                    estimated_review_time="4-6 weeks",
                    next_steps=permit.next_steps or "You'll receive email updates on review progress.",
                )
            except Exception as e:
                logger.error(f"Error creating permit in CosmosDB: {e}")
                # Fall through to mock data

        # Mock implementation for local development
        permit_number = self._generate_id("PERMIT")

        # Calculate fees based on estimated cost
        plan_check = round(estimated_cost * 0.018, 2)  # ~1.8% of project cost
        permit_fee = round(estimated_cost * 0.032, 2)  # ~3.2% of project cost
        total = round(plan_check + permit_fee, 2)

        return PermitSubmitResult(
            success=True,
            permit_number=permit_number,
            status=PermitStatus.SUBMITTED,
            submitted_at=datetime.now(timezone.utc),
            fees=PermitFees(plan_check=plan_check, permit_fee=permit_fee, other_fees=0, total=total),
            estimated_review_time="4-6 weeks",
            next_steps="You'll receive email updates on review progress. Plan check fees are due within 30 days.",
        )

    async def get_permit_status(
        self, permit_number: str, user_id: Optional[str] = None
    ) -> Optional[Permit]:
        """
        Get the current status of a permit.

        Uses CosmosDB if configured, otherwise returns mock data.
        
        Args:
            permit_number: Permit number to look up
            user_id: Optional user ID for optimized partition-aware query
        """
        # Use CosmosDB if available
        if self._permit_repo:
            try:
                permit = await self._permit_repo.get_by_permit_number(
                    permit_number, user_id=user_id
                )
                if permit:
                    return permit
            except Exception as e:
                logger.error(f"Error getting permit status from CosmosDB: {e}")
                # Fall through to mock data

        # Mock response for local development
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
        user_id: Optional[str] = None,
        permit_number: Optional[str] = None,
        address: Optional[str] = None,
    ) -> InspectionListResult:
        """
        Get scheduled inspections for a permit or address.

        Uses CosmosDB if configured, otherwise returns mock data.
        
        Args:
            user_id: Optional user ID for optimized queries
            permit_number: Optional permit number to filter by
            address: Optional address to filter by
        """
        # Use CosmosDB if available
        if self._inspection_repo:
            try:
                inspections = []
                if permit_number:
                    inspections = await self._inspection_repo.list_by_permit(permit_number)
                elif address:
                    inspections = await self._inspection_repo.list_by_address(address)
                elif user_id:
                    inspections = await self._inspection_repo.list_by_user(user_id)
                return InspectionListResult(inspections=inspections, total_count=len(inspections))
            except Exception as e:
                logger.error(f"Error getting inspections from CosmosDB: {e}")
                # Fall through to mock data

        # Mock implementation for local development
        inspections = []
        if permit_number or address:
            inspections = [
                Inspection(
                    inspection_id=self._generate_id("INS"),
                    permit_number=permit_number or "PERMIT-2026-001234",
                    inspection_type=InspectionType.ROUGH_ELECTRICAL,
                    status=InspectionStatus.SCHEDULED,
                    scheduled_date=datetime.now(timezone.utc) + timedelta(days=3),
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
