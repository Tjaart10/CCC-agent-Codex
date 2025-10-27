"""Interactive collection of CPU/CCC data using Typer prompts."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from pydantic import ValidationError

from .data_models import (
    CCCApplicationData,
    CPUApplicationData,
    ContactDetails,
    AgentDetails,
    LBPDetails,
    SpecifiedSystem,
    ApplicationData,
)
from .enums import ApplicationType


def _prompt_date(message: str) -> date:
    """Prompt the user for a date in ISO format."""

    while True:
        value = typer.prompt(f"{message} (YYYY-MM-DD)")
        try:
            return date.fromisoformat(value)
        except ValueError:
            typer.secho("Invalid date format. Please use YYYY-MM-DD.", fg=typer.colors.RED)


def _prompt_contact(role: str) -> ContactDetails:
    """Prompt for generic contact details."""

    typer.secho(f"\nEnter {role} details", fg=typer.colors.CYAN)
    return ContactDetails(
        name=typer.prompt("Full name"),
        contact_person=typer.prompt(
            "Contact person (blank if same as full name)", default=""
        )
        or None,
        mailing_address=typer.prompt("Mailing address"),
        street_address=typer.prompt("Street address"),
        phone_number=typer.prompt("Phone number"),
        email=typer.prompt("Email"),
    )


def _prompt_agent() -> AgentDetails:
    """Prompt for agent/applicant details."""

    base = _prompt_contact("applicant/agent")
    relationship = typer.prompt("Relationship to owner")
    has_authority = typer.confirm(
        "Do you have a signed written authority from the owner?",
        default=True,
    )
    return AgentDetails(
        **base.dict(),
        relationship_to_owner=relationship,
        has_written_authority=has_authority,
    )


def _prompt_lbps() -> list[LBPDetails]:
    """Collect LBP details until the user stops."""

    lbps: list[LBPDetails] = []
    typer.secho("\nEnter Licensed Building Practitioner details", fg=typer.colors.CYAN)
    while typer.confirm("Add an LBP?", default=bool(not lbps)):
        lbps.append(
            LBPDetails(
                name=typer.prompt("Name"),
                company=typer.prompt("Company (blank if not applicable)", default="")
                or None,
                registration_number=typer.prompt("LBP/registration number"),
                phone_number=typer.prompt("Phone number (optional)", default="") or None,
                email=typer.prompt("Email (optional)", default="") or None,
            )
        )
    return lbps


def _prompt_specified_systems() -> list[SpecifiedSystem]:
    """Collect specified systems for CCC applications."""

    systems: list[SpecifiedSystem] = []
    typer.secho("\nEnter specified systems", fg=typer.colors.CYAN)
    while typer.confirm("Add a specified system?", default=bool(not systems)):
        description = typer.prompt("System description")
        performance = typer.prompt("Performance standard")
        is_new = typer.confirm("Is this a new system?", default=True)
        systems.append(
            SpecifiedSystem(
                description=description,
                performance_standard=performance,
                is_new=is_new,
            )
        )
    return systems


def collect_user_input(
    application_type: ApplicationType,
    data_file: Optional[Path] = None,
) -> ApplicationData:
    """Collect all required data for the chosen application type."""

    if data_file:
        payload: Dict[str, Any] = json.loads(data_file.read_text())
        payload.setdefault("application_type", application_type.value)
        model = CCCApplicationData if application_type is ApplicationType.CCC else CPUApplicationData
        try:
            return model.parse_obj(payload)
        except ValidationError as exc:  # pragma: no cover - thin wrapper around pydantic
            raise typer.BadParameter(str(exc)) from exc

    typer.secho("\nCollecting data for the application", fg=typer.colors.GREEN)

    owner = _prompt_contact("owner")
    applicant = _prompt_agent()

    common_kwargs = dict(
        application_type=application_type,
        property_address=typer.prompt("Property address"),
        premises_description=typer.prompt("Describe the part of premises involved"),
        owner=owner,
        applicant=applicant,
        building_work_description=typer.prompt("Describe the building work"),
    )

    if application_type is ApplicationType.CPU:
        return CPUApplicationData(
            **common_kwargs,
            public_access_safety=typer.prompt(
                "Describe how the public will access the premises safely"
            ),
            safety_systems_in_place=typer.prompt(
                "Safety systems/mitigation in place (optional)", default=""
            )
            or None,
        )

    # CCC flow
    lbps = _prompt_lbps()
    systems = _prompt_specified_systems()

    return CCCApplicationData(
        **common_kwargs,
        building_consent_number=typer.prompt("Building consent number"),
        building_consent_granted_date=_prompt_date("Consent granted date"),
        building_description=typer.prompt("Description of the building"),
        current_use=typer.prompt("Current use"),
        building_work_completion_date=_prompt_date("Date building work completed"),
        lbps=lbps,
        specified_systems=systems,
    )


__all__ = ["collect_user_input"]
