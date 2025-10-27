"""Typed models describing CPU/CCC application payloads."""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from .enums import ApplicationType


class ContactDetails(BaseModel):
    """Represents a person or organisation involved in the application."""

    name: str = Field(..., description="Full name of the contact")
    contact_person: Optional[str] = Field(
        None, description="Contact person if the entity is an organisation"
    )
    mailing_address: str = Field(..., description="Mailing address")
    street_address: str = Field(..., description="Street or physical address")
    phone_number: str = Field(..., description="Primary contact phone number")
    email: EmailStr = Field(..., description="Email address")


class AgentDetails(ContactDetails):
    """Extends :class:`ContactDetails` with agent specific metadata."""

    relationship_to_owner: str = Field(
        ..., description="Summary of the relationship to the owner"
    )
    has_written_authority: bool = Field(
        False, description="Whether a written authority document is supplied"
    )


class LBPDetails(BaseModel):
    """Details for Licensed Building Practitioners or supervising personnel."""

    name: str
    company: Optional[str] = None
    registration_number: str = Field(..., description="LBP or registration number")
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None


class SpecifiedSystem(BaseModel):
    """Systems installed, altered or removed as part of the work."""

    description: str = Field(..., description="Name/description of the specified system")
    performance_standard: str = Field(
        ..., description="Performance standard the system must meet"
    )
    is_new: bool = Field(
        True, description="Indicates if the system is newly installed (vs altered/removed)"
    )


class BaseApplicationData(BaseModel):
    """Fields shared by CPU and CCC applications."""

    application_type: ApplicationType
    property_address: str = Field(..., description="Street address of the property")
    premises_description: str = Field(
        ..., description="Description of the part of premises involved"
    )
    owner: ContactDetails
    applicant: AgentDetails
    building_work_description: str

    class Config:
        anystr_strip_whitespace = True
        min_anystr_length = 1
        extra = "forbid"


class CPUApplicationData(BaseApplicationData):
    """Additional data required for CPU applications."""

    public_access_safety: str = Field(
        ..., description="Explanation of how public access will remain safe"
    )
    safety_systems_in_place: Optional[str] = Field(
        None,
        description="Supplementary notes on systems/mitigation to keep the public safe",
    )


class CCCApplicationData(BaseApplicationData):
    """Additional data required for CCC applications."""

    building_consent_number: str
    building_consent_granted_date: date
    building_description: str
    current_use: str
    building_work_completion_date: date
    lbps: List[LBPDetails] = Field(default_factory=list)
    specified_systems: List[SpecifiedSystem] = Field(default_factory=list)

    @validator("building_work_completion_date")
    def validate_completion_date(
        cls, value: date, values: dict[str, object]
    ) -> date:
        granted = values.get("building_consent_granted_date")
        if isinstance(granted, date) and value < granted:
            raise ValueError(
                "Completion date cannot be earlier than the consent granted date"
            )
        return value


ApplicationData = CPUApplicationData | CCCApplicationData
