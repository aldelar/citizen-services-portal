"""MCP tools for LADWP services."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    Account,
    EquipmentType,
    Interconnection,
    InterconnectionStatus,
    KnowledgeResult,
    PlansListResult,
    RatePlan,
    RebateApplication,
    RebateApplyResult,
    RebatesFiledResult,
    TOUEnrollmentResult,
    UserActionResponse,
)
from .services import LADWPService


class LADWPTools:
    """LADWP MCP tools implementation."""

    def __init__(self):
        """Initialize LADWP tools with service layer."""
        self.service = LADWPService()

    async def queryKB(
        self,
        query: str,
        top: int = 5,
    ) -> Dict[str, Any]:
        """
        Search LADWP knowledge base for rate plans, rebates, solar programs.

        Args:
            query: Natural language query
            top: Number of results to return (default 5)

        Returns:
            KnowledgeResult with matching document chunks
        """
        result = await self.service.query_knowledge_base(query, top)
        return result.model_dump(mode="json")

    async def account_show(
        self,
        account_number: str,
    ) -> Dict[str, Any]:
        """
        Get current account information including rate plan and pending requests.

        Args:
            account_number: The utility account number

        Returns:
            Account information with rate plan, meter type, and pending requests
        """
        result = await self.service.get_account(account_number)
        return result.model_dump(mode="json")

    async def plans_list(
        self,
        account_number: str,
    ) -> Dict[str, Any]:
        """
        List available LADWP rate plans.

        Args:
            account_number: The utility account number

        Returns:
            PlansListResult with available plans and recommendation
        """
        result = await self.service.list_rate_plans(account_number)
        return result.model_dump(mode="json")

    async def tou_enroll(
        self,
        account_number: str,
        rate_plan: str,
    ) -> Dict[str, Any]:
        """
        Enroll in a Time-of-Use rate plan.

        Args:
            account_number: The utility account number
            rate_plan: Rate plan to enroll in (TOU-D-A, TOU-D-B, TOU-D-PRIME)

        Returns:
            TOUEnrollmentResult with confirmation and effective date
        """
        result = await self.service.enroll_tou(account_number, RatePlan(rate_plan))
        return result.model_dump(mode="json")

    async def interconnection_submit(
        self,
        address: str,
        system_size_kw: float,
        applicant_name: str,
        applicant_email: str,
        battery_size_kwh: Optional[float] = None,
        inverter: Optional[str] = None,
        panels: Optional[str] = None,
        battery: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepare solar interconnection application (requires user action - email submission).

        Args:
            address: Service address
            system_size_kw: Solar system size in kW
            applicant_name: Applicant's name
            applicant_email: Applicant's email
            battery_size_kwh: Battery size in kWh (optional)
            inverter: Inverter model (optional)
            panels: Panel specifications (optional)
            battery: Battery model (optional)

        Returns:
            UserActionResponse with email draft and checklist
        """
        equipment_specs = {}
        if inverter:
            equipment_specs["inverter"] = inverter
        if panels:
            equipment_specs["panels"] = panels
        if battery:
            equipment_specs["battery"] = battery

        result = await self.service.prepare_interconnection_submission(
            address=address,
            system_size_kw=system_size_kw,
            battery_size_kwh=battery_size_kwh,
            equipment_specs=equipment_specs,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
        )
        return result.model_dump(mode="json")

    async def interconnection_getStatus(
        self,
        application_id: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check interconnection application status.

        Args:
            application_id: Interconnection application ID
            address: Service address (alternative to application_id)

        Returns:
            Interconnection status with next steps
        """
        result = await self.service.get_interconnection_status(
            application_id=application_id,
            address=address,
        )
        return result.model_dump(mode="json")

    async def rebates_filed(
        self,
        account_number: str,
    ) -> Dict[str, Any]:
        """
        List all rebate applications for an account.

        Args:
            account_number: The utility account number

        Returns:
            RebatesFiledResult with all applications and their status
        """
        result = await self.service.get_filed_rebates(account_number)
        return result.model_dump(mode="json")

    async def rebates_apply(
        self,
        account_number: str,
        equipment_type: str,
        equipment_details: str,
        purchase_date: str,
        invoice_total: float,
        ahri_certificate: str,
        ladbs_permit_number: str,
    ) -> Dict[str, Any]:
        """
        Submit a rebate application.

        Args:
            account_number: The utility account number
            equipment_type: Type of equipment (heat_pump_hvac, heat_pump_water_heater, smart_thermostat)
            equipment_details: Equipment make, model, specs
            purchase_date: Date of purchase (YYYY-MM-DD)
            invoice_total: Total invoice amount
            ahri_certificate: AHRI certificate number
            ladbs_permit_number: LADBS permit number

        Returns:
            RebateApplyResult with application ID and estimated rebate
        """
        result = await self.service.apply_for_rebate(
            account_number=account_number,
            equipment_type=EquipmentType(equipment_type),
            equipment_details=equipment_details,
            purchase_date=datetime.fromisoformat(purchase_date),
            invoice_total=invoice_total,
            ahri_certificate=ahri_certificate,
            ladbs_permit_number=ladbs_permit_number,
        )
        return result.model_dump(mode="json")

    async def rebates_getStatus(
        self,
        application_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed status of a specific rebate application.

        Args:
            application_id: The rebate application ID

        Returns:
            RebateApplication with detailed status
        """
        result = await self.service.get_rebate_status(application_id)
        return result.model_dump(mode="json")
