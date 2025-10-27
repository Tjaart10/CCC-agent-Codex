"""End-to-end orchestration for the Auckland Council automation."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional, Sequence

import typer

from .document_management import ensure_all_documents_valid
from .enums import ApplicationType
from .input_collection import collect_user_input
from .portal_automation import run_in_browser

LOGGER = logging.getLogger(__name__)


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def _pause(message: str) -> None:
    typer.secho(f"\n{message}", fg=typer.colors.YELLOW)
    typer.prompt("Press ENTER to continue", default="")


def run_workflow(
    application_type: ApplicationType,
    documents: Sequence[Path],
    data_file: Optional[Path] = None,
    *,
    verbose: bool = False,
) -> None:
    """Validate inputs, launch the browser automation and orchestrate the flow."""

    _configure_logging(verbose)

    typer.secho("\nValidating documents", fg=typer.colors.GREEN)
    ensure_all_documents_valid(documents)

    typer.secho("\nCollecting application data", fg=typer.colors.GREEN)
    data = collect_user_input(application_type, data_file=data_file)

    typer.secho("\nLaunching browser automation", fg=typer.colors.GREEN)
    try:
        asyncio.run(run_in_browser(data, documents, _pause))
    except KeyboardInterrupt:  # pragma: no cover - user controlled
        typer.secho("Automation interrupted by user", fg=typer.colors.RED)


__all__ = ["run_workflow"]
