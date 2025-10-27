from enum import Enum


class ApplicationType(str, Enum):
    """Supported Auckland Council application types."""

    CPU = "cpu"
    CCC = "ccc"

    def __str__(self) -> str:  # pragma: no cover - trivial string representation
        return self.value
