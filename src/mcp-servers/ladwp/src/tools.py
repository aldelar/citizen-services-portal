"""MCP tools for LADWP services."""

from datetime import datetime
from typing import Any, Dict, List

from .models import OutageReport, Payment, ServiceRequest
from .services import LADWPService


class LADWPTools:
    """LADWP MCP tools implementation."""

    def __init__(self):
        """Initialize LADWP tools with service layer."""
        self.service = LADWPService()

    async def get_account_balance(self, account_number: str) -> Dict[str, Any]:
        """
        Get account balance information.

        Args:
            account_number: The utility account number

        Returns:
            Account balance information
        """
        account = await self.service.get_account_balance(account_number)
        return account.model_dump()

    async def get_bill_history(self, account_number: str, months: int = 12) -> Dict[str, Any]:
        """
        Get billing history for an account.

        Args:
            account_number: The utility account number
            months: Number of months of history to retrieve

        Returns:
            List of bills
        """
        bills = await self.service.get_bill_history(account_number, months)
        return {
            "account_number": account_number,
            "months_requested": months,
            "bills": [bill.model_dump() for bill in bills],
        }

    async def make_payment(
        self,
        account_number: str,
        amount: float,
        payment_method: str,
    ) -> Dict[str, Any]:
        """
        Submit a payment.

        Args:
            account_number: The utility account number
            amount: Payment amount
            payment_method: Payment method (credit_card, debit_card, bank_account, check)

        Returns:
            Payment confirmation
        """
        payment = Payment(
            account_number=account_number,
            amount=amount,
            payment_method=payment_method,
            payment_date=datetime.now(),
        )
        result = await self.service.make_payment(payment)
        return result

    async def report_outage(
        self,
        address: str,
        outage_type: str,
        description: str,
    ) -> Dict[str, Any]:
        """
        Report a power or water outage.

        Args:
            address: Address where the outage is occurring
            outage_type: Type of outage (power or water)
            description: Description of the outage

        Returns:
            Outage report confirmation
        """
        report = OutageReport(
            address=address,
            outage_type=outage_type,
            description=description,
            reported_at=datetime.now(),
        )
        result = await self.service.report_outage(report)
        return result

    async def check_outage_status(self, outage_id: str) -> Dict[str, Any]:
        """
        Check the status of a reported outage.

        Args:
            outage_id: The outage report ID

        Returns:
            Current outage status information
        """
        status = await self.service.check_outage_status(outage_id)
        return status.model_dump() if status else {"error": "Outage report not found"}

    async def request_service_start(
        self,
        address: str,
        service_date: str,
        service_types: List[str],
    ) -> Dict[str, Any]:
        """
        Request to start utility service at an address.

        Args:
            address: Service address
            service_date: Requested service start date (YYYY-MM-DD)
            service_types: List of service types (electricity, water)

        Returns:
            Service start confirmation
        """
        try:
            parsed_date = datetime.fromisoformat(service_date)
        except ValueError:
            return {"error": f"Invalid date format: '{service_date}'. Please use YYYY-MM-DD format."}

        request = ServiceRequest(
            request_type="start",
            address=address,
            service_date=parsed_date,
            service_types=service_types,
        )
        result = await self.service.request_service_start(request)
        return result

    async def request_service_stop(
        self,
        account_number: str,
        stop_date: str,
    ) -> Dict[str, Any]:
        """
        Request to stop utility service.

        Args:
            account_number: The utility account number
            stop_date: Requested service stop date (YYYY-MM-DD)

        Returns:
            Service stop confirmation
        """
        try:
            parsed_date = datetime.fromisoformat(stop_date)
        except ValueError:
            return {"error": f"Invalid date format: '{stop_date}'. Please use YYYY-MM-DD format."}

        result = await self.service.request_service_stop(account_number, parsed_date)
        return result

    async def get_usage_history(
        self,
        account_number: str,
        utility_type: str,
        months: int = 12,
    ) -> Dict[str, Any]:
        """
        Get usage history for an account.

        Args:
            account_number: The utility account number
            utility_type: Type of utility (electricity or water)
            months: Number of months of history to retrieve

        Returns:
            Usage history records
        """
        records = await self.service.get_usage_history(account_number, utility_type, months)
        return {
            "account_number": account_number,
            "utility_type": utility_type,
            "months_requested": months,
            "usage_records": [record.model_dump() for record in records],
        }
