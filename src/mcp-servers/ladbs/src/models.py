"""Data models for LADBS MCP server."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PermitApplication(BaseModel):
    """Building permit application."""

    application_id: Optional[str] = Field(default=None, description="Application ID (generated)")
    applicant_name: str = Field(description="Name of the applicant")
    property_address: str = Field(description="Property address")
    work_description: str = Field(description="Description of proposed work")
    estimated_cost: float = Field(description="Estimated cost of work", gt=0)
    submitted_at: Optional[datetime] = Field(default=None, description="Submission timestamp")


class PermitStatus(BaseModel):
    """Permit status information."""

    permit_number: str = Field(description="Permit number")
    status: str = Field(description="Current status (pending, approved, rejected, etc.)")
    submitted_date: datetime = Field(description="Date submitted")
    updated_date: datetime = Field(description="Last update date")
    assigned_inspector: Optional[str] = Field(default=None, description="Assigned inspector name")
    notes: Optional[str] = Field(default=None, description="Status notes")


class InspectionRequest(BaseModel):
    """Inspection scheduling request."""

    permit_number: str = Field(description="Permit number")
    inspection_type: str = Field(description="Type of inspection (foundation, framing, final, etc.)")
    requested_date: datetime = Field(description="Requested inspection date")
    contact_name: str = Field(description="Contact person name")
    contact_phone: str = Field(description="Contact phone number")


class ViolationReport(BaseModel):
    """Code violation report."""

    report_id: Optional[str] = Field(default=None, description="Report ID (generated)")
    property_address: str = Field(description="Address of violation")
    violation_type: str = Field(description="Type of violation")
    description: str = Field(description="Detailed description")
    reporter_name: Optional[str] = Field(default=None, description="Reporter name (optional)")
    reporter_contact: Optional[str] = Field(default=None, description="Reporter contact (optional)")
    reported_at: Optional[datetime] = Field(default=None, description="Report timestamp")
