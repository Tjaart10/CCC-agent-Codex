"""High level helpers that automate the myAUCKLAND portal via Playwright."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Sequence

from playwright.async_api import Browser, Page, async_playwright

from .data_models import ApplicationData, CCCApplicationData, CPUApplicationData
from .enums import ApplicationType

LOGGER = logging.getLogger(__name__)

PauseCallback = Callable[[str], None]


async def _fill_text_field(page: Page, label: str, value: str) -> None:
    """Fill an input field identified by its accessible label."""

    if not value:
        return

    try:
        locator = page.get_by_label(label)
        await locator.fill(value)
        await locator.blur()
        LOGGER.debug("Filled field '%s'", label)
    except Exception as exc:  # pragma: no cover - depends on remote DOM
        LOGGER.warning("Could not fill field '%s': %s", label, exc)


async def login_to_portal(page: Page, pause_callback: PauseCallback) -> None:
    """Navigate to the myAUCKLAND login page and pause for user credentials."""

    LOGGER.info("Navigating to myAUCKLAND login portal")
    await page.goto("https://onlineservices.aucklandcouncil.govt.nz/en")
    pause_callback(
        "Please complete the myAUCKLAND login (including MFA/CAPTCHA) manually.\n"
        "Press ENTER once the dashboard is visible."
    )


async def _navigate_to_application(page: Page, application_type: ApplicationType) -> None:
    """Navigate through the dashboard to the selected application form."""

    LOGGER.info("Navigating to %s application wizard", application_type.value.upper())
    # The navigation pattern relies on accessible roles/text which are stable across updates.
    try:
        await page.get_by_role("link", name="Online applications, bookings and payments").click()
        await page.get_by_role("link", name="Building consents").click()
        await page.get_by_role("button", name="View all").click()
        if application_type is ApplicationType.CPU:
            await page.get_by_role("link", name="Certificate for public use").click()
        else:
            await page.get_by_role("link", name="Code compliance certificate").click()
        await page.get_by_role("button", name="Apply online").click()
    except Exception as exc:  # pragma: no cover - remote DOM variability
        LOGGER.warning("Automatic navigation failed: %s", exc)
        raise


async def _fill_common_sections(page: Page, data: ApplicationData) -> None:
    """Populate form sections shared by both CPU and CCC."""

    LOGGER.info("Populating property and contact sections")
    await _fill_text_field(page, "Property address", data.property_address)
    await _fill_text_field(page, "Describe the part of the premises involved", data.premises_description)
    await _fill_text_field(page, "Describe the building work", data.building_work_description)

    owner = data.owner
    await _fill_text_field(page, "Owner name", owner.name)
    if owner.contact_person:
        await _fill_text_field(page, "Owner contact person", owner.contact_person)
    await _fill_text_field(page, "Owner mailing address", owner.mailing_address)
    await _fill_text_field(page, "Owner street address", owner.street_address)
    await _fill_text_field(page, "Owner phone", owner.phone_number)
    await _fill_text_field(page, "Owner email", owner.email)

    applicant = data.applicant
    await _fill_text_field(page, "Applicant name", applicant.name)
    if applicant.contact_person:
        await _fill_text_field(page, "Applicant contact person", applicant.contact_person)
    await _fill_text_field(page, "Applicant mailing address", applicant.mailing_address)
    await _fill_text_field(page, "Applicant street address", applicant.street_address)
    await _fill_text_field(page, "Applicant phone", applicant.phone_number)
    await _fill_text_field(page, "Applicant email", applicant.email)
    await _fill_text_field(page, "Relationship to owner", applicant.relationship_to_owner)


async def _fill_cpu_specific(page: Page, data: CPUApplicationData) -> None:
    LOGGER.info("Adding CPU specific information")
    await _fill_text_field(page, "Public access and safety", data.public_access_safety)
    if data.safety_systems_in_place:
        await _fill_text_field(page, "Safety systems in place", data.safety_systems_in_place)


async def _fill_ccc_specific(page: Page, data: CCCApplicationData) -> None:
    LOGGER.info("Adding CCC specific information")
    await _fill_text_field(page, "Building consent number", data.building_consent_number)
    await _fill_text_field(
        page,
        "Date consent granted",
        data.building_consent_granted_date.isoformat(),
    )
    await _fill_text_field(page, "Building description", data.building_description)
    await _fill_text_field(page, "Current use", data.current_use)
    await _fill_text_field(
        page,
        "Date building work completed",
        data.building_work_completion_date.isoformat(),
    )

    for index, lbp in enumerate(data.lbps, start=1):
        LOGGER.info("Entering LBP %s", index)
        await _fill_text_field(page, f"LBP name {index}", lbp.name)
        if lbp.company:
            await _fill_text_field(page, f"LBP company {index}", lbp.company)
        await _fill_text_field(page, f"LBP registration {index}", lbp.registration_number)
        if lbp.phone_number:
            await _fill_text_field(page, f"LBP phone {index}", lbp.phone_number)
        if lbp.email:
            await _fill_text_field(page, f"LBP email {index}", lbp.email)

    for index, system in enumerate(data.specified_systems, start=1):
        LOGGER.info("Entering specified system %s", index)
        await _fill_text_field(page, f"Specified system {index}", system.description)
        await _fill_text_field(page, f"System performance standard {index}", system.performance_standard)
        await _fill_text_field(
            page,
            f"System status {index}",
            "New" if system.is_new else "Existing",
        )


async def fill_form(page: Page, data: ApplicationData) -> None:
    """Populate the online form with validated data."""

    await _fill_common_sections(page, data)
    if isinstance(data, CPUApplicationData):
        await _fill_cpu_specific(page, data)
    else:
        await _fill_ccc_specific(page, data)


async def upload_files(page: Page, files: Sequence[Path]) -> None:
    """Upload PDF attachments via the portal."""

    LOGGER.info("Uploading %s documents", len(files))
    for file_path in files:
        LOGGER.info("Uploading %s", file_path)
        try:
            upload_control = page.locator("input[type=file]").first
            await upload_control.set_input_files(str(file_path))
            await page.wait_for_timeout(1000)
        except Exception as exc:  # pragma: no cover - depends on remote DOM
            LOGGER.warning("Failed to upload %s: %s", file_path, exc)
            raise


async def submit_application(page: Page, pause_callback: PauseCallback) -> None:
    """Tick declarations, add the application to the cart and pause for payment."""

    LOGGER.info("Preparing to submit application")
    try:
        await page.get_by_label("I agree to the terms and conditions").check()
    except Exception:  # pragma: no cover - depends on DOM
        LOGGER.debug("Terms checkbox not automatically located; please ensure it's ticked manually")
    try:
        await page.get_by_role("button", name="Add to cart").click()
    except Exception as exc:
        LOGGER.warning("Could not add application to cart automatically: %s", exc)
    pause_callback(
        "Review the order summary and complete payment manually.\n"
        "Press ENTER once the confirmation screen is displayed."
    )
    LOGGER.info("Application submitted (user confirmed)")


async def run_in_browser(
    data: ApplicationData,
    files: Sequence[Path],
    pause_callback: PauseCallback,
) -> None:
    """Open a Playwright browser session and orchestrate the automation."""

    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=False)
        page: Page = await browser.new_page()

        await login_to_portal(page, pause_callback)
        try:
            await _navigate_to_application(page, data.application_type)
        except Exception:
            pause_callback(
                "Navigation automation failed. Please open the desired application manually,"
                " then press ENTER to continue with form population."
            )
        await fill_form(page, data)
        await upload_files(page, files)
        await submit_application(page, pause_callback)

        await browser.close()


__all__ = [
    "run_in_browser",
    "fill_form",
    "login_to_portal",
    "upload_files",
    "submit_application",
]
