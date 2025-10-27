"""Typer command line entrypoint for the automation toolkit."""

from __future__ import annotations

from pathlib import Path
from typing import List

import typer

from .enums import ApplicationType
from .workflow import run_workflow

app = typer.Typer(help="Automate Auckland Council CPU/CCC applications")


@app.command()
def run(
    application_type: ApplicationType = typer.Option(..., "--type", "-t", help="Application type: cpu or ccc"),
    document: List[Path] = typer.Option(
        ..., "--document", "-d", help="Path to a PDF document to upload (repeatable)"
    ),
    data_file: Path = typer.Option(
        None,
        "--data-file",
        "-f",
        help="Optional JSON file with pre-filled application data",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
) -> None:
    """Run the full automation workflow."""

    run_workflow(application_type, document, data_file=data_file, verbose=verbose)


if __name__ == "__main__":
    app()
