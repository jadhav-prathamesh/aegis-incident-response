"""Shared utility functions."""

from __future__ import annotations

from typing import Any


def enum_val(v: Any) -> str:
    """Return the string value of an enum or the string itself.

    Handles the ``use_enum_values=True`` pattern in Pydantic models where
    enum fields are stored as plain strings rather than enum instances.
    """
    return v.value if hasattr(v, "value") else str(v)


def safe_float(value: Any) -> float | None:
    """Convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
