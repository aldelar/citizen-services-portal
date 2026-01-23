"""Data models for LADWP MCP server."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class UtilityType(str, Enum):
    """Type of utility service."""

    ELECTRICITY = "electricity"
    WATER = "water"


class OutageType(str, Enum):
    """Type of outage."""

    POWER = "power"
    WATER = "water"


class PaymentMethod(str, Enum):
    """Payment method."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_ACCOUNT = "bank_account"
    CHECK = "check"


class UtilityAccount(BaseModel):
    """Utility account information."""

    account_number: str = Field(description="Unique account number")
    account_holder_name: str = Field(description="Name of the account holder")
    service_address: str = Field(description="Service address")
    electricity_balance: float = Field(default=0.0, description="Current electricity balance")
    water_balance: float = Field(default=0.0, description="Current water balance")
    total_balance: float = Field(default=0.0, description="Total balance due")
    due_date: Optional[datetime] = Field(default=None, description="Payment due date")
    status: str = Field(default="active", description="Account status")


class Bill(BaseModel):
    """Utility bill information."""

    bill_id: str = Field(description="Unique bill identifier")
    account_number: str = Field(description="Account number")
    billing_period_start: datetime = Field(description="Billing period start date")
    billing_period_end: datetime = Field(description="Billing period end date")
    electricity_usage_kwh: float = Field(default=0.0, description="Electricity usage in kWh")
    electricity_charges: float = Field(default=0.0, description="Electricity charges")
    water_usage_gallons: float = Field(default=0.0, description="Water usage in gallons")
    water_charges: float = Field(default=0.0, description="Water charges")
    total_amount: float = Field(description="Total bill amount")
    due_date: datetime = Field(description="Payment due date")
    paid: bool = Field(default=False, description="Whether the bill has been paid")


class Payment(BaseModel):
    """Payment record."""

    payment_id: Optional[str] = Field(default=None, description="Payment ID (generated)")
    account_number: str = Field(description="Account number")
    amount: float = Field(description="Payment amount", gt=0)
    payment_method: str = Field(description="Payment method")
    payment_date: Optional[datetime] = Field(default=None, description="Payment date")
    confirmation_number: Optional[str] = Field(default=None, description="Confirmation number")
    status: str = Field(default="pending", description="Payment status")


class OutageReport(BaseModel):
    """Outage report."""

    report_id: Optional[str] = Field(default=None, description="Report ID (generated)")
    address: str = Field(description="Address where outage is occurring")
    outage_type: str = Field(description="Type of outage (power or water)")
    description: str = Field(description="Description of the outage")
    reported_at: Optional[datetime] = Field(default=None, description="Report timestamp")
    status: str = Field(default="reported", description="Report status")


class OutageStatus(BaseModel):
    """Outage status information."""

    outage_id: str = Field(description="Outage report ID")
    address: str = Field(description="Affected address")
    outage_type: str = Field(description="Type of outage")
    status: str = Field(description="Current status")
    reported_at: datetime = Field(description="When the outage was reported")
    estimated_restoration: Optional[datetime] = Field(default=None, description="Estimated restoration time")
    crew_assigned: bool = Field(default=False, description="Whether a crew has been assigned")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class ServiceRequest(BaseModel):
    """Service start/stop request."""

    request_id: Optional[str] = Field(default=None, description="Request ID (generated)")
    request_type: str = Field(description="Request type (start or stop)")
    address: str = Field(description="Service address")
    account_number: Optional[str] = Field(default=None, description="Account number (for stop requests)")
    service_date: datetime = Field(description="Requested service date")
    service_types: List[str] = Field(description="Service types requested (electricity, water)")
    contact_name: Optional[str] = Field(default=None, description="Contact name")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone")
    status: str = Field(default="pending", description="Request status")


class UsageRecord(BaseModel):
    """Usage record for a billing period."""

    period_start: datetime = Field(description="Period start date")
    period_end: datetime = Field(description="Period end date")
    utility_type: str = Field(description="Type of utility (electricity or water)")
    usage_amount: float = Field(description="Usage amount")
    usage_unit: str = Field(description="Usage unit (kWh or gallons)")
    cost: float = Field(description="Cost for this period")
