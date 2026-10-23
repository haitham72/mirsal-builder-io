"""Collection sale prices: exact decimal strings, independent of generation credits."""
from __future__ import annotations

import re

UNSET = object()


def normalize_price(value: str | None) -> str | None:
    """None omits the price; zero is explicitly free. Never convert through float."""
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value.strip()):
        raise ValueError("Price must be a non-negative decimal string, such as 2.50 or 0 (free), or null to leave it unset")
    whole, _, fraction = value.strip().partition(".")
    whole = whole.lstrip("0") or "0"
    fraction = fraction.rstrip("0")
    return whole + ("." + fraction if fraction else "")
