"""Helper utilities including currency formatting, date parsing, and safe conversions."""

from datetime import date, datetime
from decimal import Decimal
import math
from typing import Any


def format_inr(amount: float | Decimal | int | None) -> str:
    """Format a monetary amount in Indian Rupee format with ₹ symbol and 2 decimal places.

    Example:
        1234567.89 -> '₹12,34,567.89'
        -45000.00 -> '-₹45,000.00'
        0 -> '₹0.00'
    """
    if amount is None:
        return "₹0.00"

    try:
        val = float(amount)
    except (ValueError, TypeError):
        return "₹0.00"

    if math.isnan(val) or math.isinf(val):
        return "₹0.00"

    sign = "-" if val < 0 else ""
    abs_val = abs(val)

    # Format to 2 decimal places
    parts = f"{abs_val:.2f}".split(".")
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last3 = integer_part[-3:]
        remaining = integer_part[:-3]
        pairs = []
        while len(remaining) > 2:
            pairs.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            pairs.insert(0, remaining)
        formatted_int = ",".join(pairs) + "," + last3

    return f"{sign}₹{formatted_int}.{decimal_part}"


def parse_iso_date(date_str: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD) into a datetime.date object."""
    return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float, returning default if conversion fails."""
    if value is None:
        return default
    try:
        val = float(value)
        return default if (math.isnan(val) or math.isinf(val)) else val
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 30) -> str:
    """Truncate a string to max_length adding an ellipsis if exceeded."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
