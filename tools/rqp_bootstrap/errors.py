"""Verification errors and assertion helpers for RQP bootstrap fixtures."""

from __future__ import annotations

from typing import Any


class VerificationError(Exception):
    """Raised when a bootstrap fixture check fails."""


def fail(message: str) -> None:
    raise VerificationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        fail(f"{label}: expected {expected!r}, got {actual!r}")


def require_unique(items: list[str], label: str) -> None:
    duplicates = sorted({item for item in items if items.count(item) > 1})
    require(not duplicates, f"{label}: duplicate values {duplicates}")
