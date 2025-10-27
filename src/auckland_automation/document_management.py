"""Utilities for validating application documents prior to upload."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from PyPDF2 import PdfReader

MAX_FILE_SIZE_BYTES = 300 * 1024 * 1024  # 300 MB limit as per Council guidance


class DocumentValidationError(Exception):
    """Raised when document validation fails."""


@dataclass(slots=True)
class DocumentStatus:
    """Outcome of validating a single document."""

    path: Path
    is_valid: bool
    issues: List[str]

    def raise_for_status(self) -> None:
        """Raise a :class:`DocumentValidationError` if the document is invalid."""

        if not self.is_valid:
            details = "\n".join(self.issues)
            raise DocumentValidationError(f"Document '{self.path}' failed validation:\n{details}")


EXPECTED_SUFFIX = ".pdf"


def validate_document(path: Path) -> DocumentStatus:
    """Validate a single PDF according to Auckland Council rules."""

    issues: List[str] = []

    if not path.exists():
        issues.append("File does not exist")
    elif not path.is_file():
        issues.append("Path is not a file")

    if path.suffix.lower() != EXPECTED_SUFFIX:
        issues.append("File must be a PDF with a .pdf extension")

    if path.exists() and path.is_file():
        size = path.stat().st_size
        if size > MAX_FILE_SIZE_BYTES:
            issues.append("File exceeds the 300 MB size limit")

        try:
            reader = PdfReader(path)
            if reader.is_encrypted:
                issues.append("PDF is encrypted or password protected")
        except Exception as exc:  # pragma: no cover - PyPDF2 edge cases
            issues.append(f"Unable to open PDF: {exc}")

    return DocumentStatus(path=path, is_valid=not issues, issues=issues)


def validate_documents(paths: Iterable[Path]) -> List[DocumentStatus]:
    """Validate a batch of documents and return per-file status information."""

    return [validate_document(path) for path in paths]


def ensure_all_documents_valid(paths: Iterable[Path]) -> None:
    """Validate all documents raising at the first failure."""

    for status in validate_documents(paths):
        status.raise_for_status()


__all__ = [
    "DocumentStatus",
    "DocumentValidationError",
    "validate_document",
    "validate_documents",
    "ensure_all_documents_valid",
]
