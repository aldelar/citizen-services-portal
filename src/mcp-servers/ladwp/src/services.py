"""Business logic and external service integration for LADWP."""

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .config import settings
from .models import (
    Account,
    DocumentChunk,
    EquipmentType,
    Interconnection,
    InterconnectionStatus,
    KnowledgeResult,
    MeterType,
    OnCompletePrompt,
    PlansListResult,
    PreparedMaterials,
    RatePlan,
    RatePlanInfo,
    RateSchedule,
    RebateApplication,
    RebateApplyResult,
    RebatesFiledResult,
    RebateStatus,
    TOUEnrollmentResult,
    UserActionResponse,
)


class LADWPService:
    """Service layer for LADWP operations."""

    def __init__(self):
        """Initialize LADWP service."""
        self.api_endpoint = settings.ladwp_api_endpoint
        self.api_key = settings.ladwp_api_key

    def _generate_id(self, prefix: str = "ID") -> str:
        """Generate a random ID."""
        random_suffix = "".join(random.choices(string.digits, k=6))
        return f"{prefix}-2026-{random_suffix}"

    async def query_knowledge_base(self, query: str, top: int = 5) -> KnowledgeResult:
        """
        Query the LADWP knowledge base (AI Search).

        This is a mock implementation.
        """
        # TODO: Replace with actual Azure AI Search call

        mock_chunks = [
            DocumentChunk(
                content="TOU-D-PRIME is LADWP's Time-of-Use rate designed for solar customers. Off-peak hours are 8pm-4pm weekdays and all weekend at $0.15/kWh. On-peak hours are 4pm-9pm weekdays at $0.45/kWh. This rate maximizes savings when combined with battery storage.",
                source="ladwp-rate-plans-2026.pdf",
                relevance_score=0.95,
            ),
            DocumentChunk(
                content="LADWP Clean Replacement Program offers rebates for heat pump HVAC systems: $2,500 per ton for ducted systems (max 5 tons), $2,000 per ton for ductless mini-splits. AHRI certification and LADBS permit required. Processing takes 8-12 weeks.",
                source="ladwp-rebate-guide.pdf",
                relevance_score=0.88,
            ),
            DocumentChunk(
                content="Solar interconnection process: 1) Submit application to SolarCoordinator@ladwp.com with single-line diagram, equipment specs, and site plan. 2) Engineering review takes 4-6 weeks. 3) After installation, request PTO (Permission to Operate) inspection.",
                source="ladwp-solar-interconnection.pdf",
                relevance_score=0.82,
            ),
        ]

        return KnowledgeResult(
            query=query,
            results=mock_chunks[:top],
            total_results=len(mock_chunks),
        )

    async def get_account(self, account_number: str) -> Account:
        """
        Get account information.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADWP API call

        return Account(
            account_number=account_number,
            account_holder="John Smith",
            service_address="123 Main St, Los Angeles, CA 90012",
            current_rate_plan=RatePlan.STANDARD,
            meter_type=MeterType.STANDARD,
            pending_requests=[],
            has_solar=False,
            has_battery=False,
        )

    async def list_rate_plans(self, account_number: str) -> PlansListResult:
        """
        List available rate plans for an account.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADWP API call

        available_plans = [
            RatePlanInfo(
                plan_code=RatePlan.STANDARD,
                plan_name="Standard Residential",
                description="Flat rate pricing for all hours",
                rates=RateSchedule(off_peak_rate=0.25),
                eligibility="All residential customers",
                best_for="Customers with consistent usage throughout the day",
            ),
            RatePlanInfo(
                plan_code=RatePlan.TOU_D_A,
                plan_name="TOU-D-A",
                description="Time-of-Use rate with moderate peak pricing",
                rates=RateSchedule(
                    off_peak_rate=0.18,
                    mid_peak_rate=0.25,
                    on_peak_rate=0.35,
                    off_peak_hours="9pm-10am weekdays, all weekend",
                    on_peak_hours="5pm-8pm weekdays",
                ),
                eligibility="All residential customers",
                best_for="Customers who can shift usage to off-peak hours",
            ),
            RatePlanInfo(
                plan_code=RatePlan.TOU_D_PRIME,
                plan_name="TOU-D-PRIME",
                description="Time-of-Use rate optimized for solar customers",
                rates=RateSchedule(
                    off_peak_rate=0.15,
                    mid_peak_rate=0.28,
                    on_peak_rate=0.45,
                    off_peak_hours="8pm-4pm weekdays, all weekend",
                    on_peak_hours="4pm-9pm weekdays",
                ),
                eligibility="Customers with solar PV systems",
                best_for="Solar customers with battery storage",
            ),
        ]

        return PlansListResult(
            current_plan=RatePlan.STANDARD,
            available_plans=available_plans,
            recommended_plan=RatePlan.TOU_D_PRIME,
            recommendation_reason="With your planned solar installation, TOU-D-PRIME could save 30-50% on electricity costs",
        )

    async def enroll_tou(self, account_number: str, rate_plan: RatePlan) -> TOUEnrollmentResult:
        """
        Enroll in a TOU rate plan.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADWP API call

        effective_date = datetime.now() + timedelta(days=14)
        meter_swap_date = effective_date - timedelta(days=3)

        return TOUEnrollmentResult(
            success=True,
            confirmation_number=self._generate_id("TOU"),
            rate_plan=rate_plan,
            effective_date=effective_date,
            meter_swap_required=True,
            meter_swap_date=meter_swap_date,
            next_steps=f"A technician will install your TOU meter on {meter_swap_date.strftime('%b %d')}. Your new rate takes effect {effective_date.strftime('%b %d')}.",
        )

    async def prepare_interconnection_submission(
        self,
        address: str,
        system_size_kw: float,
        battery_size_kwh: Optional[float],
        equipment_specs: Dict[str, str],
        applicant_name: str,
        applicant_email: str,
    ) -> UserActionResponse:
        """
        Prepare materials for interconnection application (requires user email).
        """
        battery_text = f"\nBattery Storage: {battery_size_kwh} kWh ({equipment_specs.get('battery', 'TBD')})" if battery_size_kwh else ""
        inverter_text = equipment_specs.get("inverter", "[Inverter model]")

        email_draft = f"""Subject: Interconnection Application - {address}

Dear LADWP Solar Coordinator,

I am submitting an interconnection application for a solar PV system{"with battery storage" if battery_size_kwh else ""} at:

Address: {address}
System Size: {system_size_kw} kW DC{battery_text}
Inverter: {inverter_text}

Please find attached:
1. Completed Interconnection Application Form
2. Single-line electrical diagram
3. Equipment specification sheets
4. Site plan

Applicant: {applicant_name}
Email: {applicant_email}
LADBS Electrical Permit: [Include permit number when approved]

Thank you,
{applicant_name}"""

        return UserActionResponse(
            requires_user_action=True,
            action_type="email",
            target="SolarCoordinator@ladwp.com",
            reason="Interconnection agreements require signed documents and engineering review",
            prepared_materials=PreparedMaterials(
                email_draft=email_draft,
                checklist=[
                    "Complete LADWP Interconnection Application Form (download from ladwp.com/nem)",
                    "Attach single-line electrical diagram",
                    "Attach equipment spec sheets (inverter, panels, battery)",
                    "Attach site plan showing equipment locations",
                    "Include LADBS electrical permit number",
                ],
                contact_info={
                    "email": "SolarCoordinator@ladwp.com",
                    "phone": "213-367-6163",
                    "department": "PV/BESS Service Design Group",
                },
                documents_needed=[
                    "Interconnection Application Form",
                    "Single-line diagram",
                    "Equipment specs",
                    "Site plan",
                    "LADBS permit (when approved)",
                ],
            ),
            on_complete=OnCompletePrompt(
                prompt="Once you've emailed the application, let me know and I'll help track the status",
                expected_info=["submission_date", "confirmation_email_received"],
            ),
        )

    async def get_interconnection_status(
        self,
        application_id: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Interconnection:
        """
        Get interconnection application status.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADWP API call

        return Interconnection(
            application_id=application_id or self._generate_id("IA"),
            address=address or "123 Main St, Los Angeles, CA 90012",
            system_size_kw=8.5,
            battery_size_kwh=13.5,
            status=InterconnectionStatus.APPROVED,
            submitted_at=datetime(2026, 1, 20),
            approved_at=datetime(2026, 2, 15),
            pto_date=None,
            next_steps="Complete installation and pass LADBS final inspection, then request PTO inspection",
        )

    async def get_filed_rebates(self, account_number: str) -> RebatesFiledResult:
        """
        Get all rebate applications for an account.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADWP API call

        # Return empty list for demo - applications added as user submits them
        return RebatesFiledResult(applications=[], total_count=0)

    async def apply_for_rebate(
        self,
        account_number: str,
        equipment_type: EquipmentType,
        equipment_details: str,
        purchase_date: datetime,
        invoice_total: float,
        ahri_certificate: str,
        ladbs_permit_number: str,
    ) -> RebateApplyResult:
        """
        Submit a rebate application.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADWP API call

        # Calculate estimated rebate based on equipment type
        if equipment_type == EquipmentType.HEAT_PUMP_HVAC:
            # Assume 3 tons at $2,500/ton
            estimated_rebate = 7500.00
        elif equipment_type == EquipmentType.HEAT_PUMP_WATER_HEATER:
            estimated_rebate = 3000.00
        else:  # smart thermostat
            estimated_rebate = 150.00

        return RebateApplyResult(
            success=True,
            application_id=self._generate_id("CRP"),
            estimated_rebate=estimated_rebate,
            processing_time="8-12 weeks",
            next_steps="Your application is submitted. LADWP may schedule a verification inspection. Rebate check will be mailed upon approval.",
        )

    async def get_rebate_status(self, application_id: str) -> RebateApplication:
        """
        Get status of a specific rebate application.

        This is a mock implementation.
        """
        # TODO: Replace with actual LADWP API call

        return RebateApplication(
            application_id=application_id,
            account_number="1234567890",
            equipment_type=EquipmentType.HEAT_PUMP_HVAC,
            status=RebateStatus.UNDER_REVIEW,
            submitted_at=datetime.now() - timedelta(days=14),
            equipment_details="Mitsubishi 3-zone ductless heat pump, 3 tons",
            estimated_rebate=7500.00,
        )
