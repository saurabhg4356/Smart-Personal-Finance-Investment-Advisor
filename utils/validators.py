"""Input validation utilities for financial models and services."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import math
from typing import Any

from models.exceptions import (
    InvalidAmountError,
    InvalidTransactionError,
    InvestmentValidationError,
)

VALID_TRANSACTION_TYPES = {"income", "expense"}


def validate_amount(amount: Any) -> Decimal:
    """Validate and convert an input amount to a positive Decimal rounded to 2 decimal places.

    Raises:
        InvalidAmountError: If amount is non-numeric, <= 0, NaN, or infinite.
    """
    if amount is None:
        raise InvalidAmountError("Amount cannot be None.", "Provide a positive number.")

    try:
        # Check float-specific NaN/inf first if already float
        if isinstance(amount, float):
            if math.isnan(amount) or math.isinf(amount):
                raise InvalidAmountError("Amount cannot be NaN or infinite.")

        # Convert through string representation to prevent binary float inaccuracies
        dec = Decimal(str(amount).strip())
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InvalidAmountError(
            f"Invalid numeric amount '{amount}'.",
            "Please enter a valid numeric value such as 1500 or 250.50.",
        ) from exc

    if dec.is_nan() or dec.is_infinite():
        raise InvalidAmountError("Amount cannot be NaN or infinite.")

    if dec <= 0:
        raise InvalidAmountError(
            f"Amount must be strictly greater than zero, got {dec}.",
            "Enter a positive amount greater than zero.",
        )

    # Quantize to 2 decimal places
    return dec.quantize(Decimal("0.01"))


def validate_date_string(date_str: str) -> str:
    """Validate that a date string is in strict ISO YYYY-MM-DD format and is a valid calendar date.

    Returns:
        Canonical YYYY-MM-DD string.

    Raises:
        InvalidTransactionError: If format is incorrect or date is invalid.
    """
    if not isinstance(date_str, str) or not date_str.strip():
        raise InvalidTransactionError(
            "Transaction date cannot be empty.",
            "Use YYYY-MM-DD format (e.g., 2026-03-15).",
        )

    cleaned = date_str.strip()
    try:
        parsed = datetime.strptime(cleaned, "%Y-%m-%d").date()
        return parsed.isoformat()
    except ValueError as exc:
        raise InvalidTransactionError(
            f"Invalid date format or non-existent date '{date_str}'.",
            "Expected format is YYYY-MM-DD (e.g., 2026-01-31).",
        ) from exc


def validate_transaction_type(tx_type: str) -> str:
    """Validate transaction type ('income' or 'expense').

    Raises:
        InvalidTransactionError: If type is not 'income' or 'expense'.
    """
    if not isinstance(tx_type, str):
        raise InvalidTransactionError(
            "Transaction type must be a string.",
            "Specify either 'income' or 'expense'.",
        )

    normalized = tx_type.strip().lower()
    if normalized not in VALID_TRANSACTION_TYPES:
        raise InvalidTransactionError(
            f"Invalid transaction type '{tx_type}'.",
            "Transaction type must be exactly 'income' or 'expense'.",
        )
    return normalized


def validate_non_empty_string(value: Any, field_name: str) -> str:
    """Validate that string value is non-empty after stripping.

    Raises:
        InvalidTransactionError: If value is not a valid non-empty string.
    """
    if not isinstance(value, str) or not value.strip():
        raise InvalidTransactionError(
            f"{field_name} cannot be empty.",
            f"Please provide a valid descriptive {field_name.lower()}.",
        )
    return value.strip()


def validate_quantity(quantity: Any) -> float:
    """Validate investment quantity (must be numeric and strictly > 0).

    Raises:
        InvestmentValidationError: If quantity is invalid.
    """
    try:
        qty = float(quantity)
    except (ValueError, TypeError) as exc:
        raise InvestmentValidationError(
            f"Invalid quantity '{quantity}'. Quantity must be a number.",
            "Enter a positive number (e.g., 10 or 2.5).",
        ) from exc

    if math.isnan(qty) or math.isinf(qty) or qty <= 0:
        raise InvestmentValidationError(
            f"Quantity must be strictly greater than zero, got {qty}.",
            "Enter a positive holding quantity.",
        )
    return round(qty, 4)


def validate_price(price: Any, field_name: str = "Price") -> float:
    """Validate investment price (must be numeric and >= 0).

    Raises:
        InvestmentValidationError: If price is invalid.
    """
    try:
        pr = float(price)
    except (ValueError, TypeError) as exc:
        raise InvestmentValidationError(
            f"Invalid {field_name} '{price}'. Price must be a number.",
            "Enter a non-negative number (e.g., 1500.00).",
        ) from exc

    if math.isnan(pr) or math.isinf(pr) or pr < 0:
        raise InvestmentValidationError(
            f"{field_name} must be greater than or equal to zero, got {pr}.",
            "Enter a non-negative price.",
        )
    return round(pr, 2)
