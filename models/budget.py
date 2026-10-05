"""Budget model for setting and monitoring category spending limits."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from utils.helpers import format_inr
from utils.validators import (
    validate_amount,
    validate_non_empty_string,
)


@dataclass(slots=True)
class Budget:
    """Represents a category spending budget for a specific month and year."""

    budget_id: str
    category: str
    monthly_limit: Decimal
    month: int
    year: int

    def __init__(
        self,
        budget_id: str,
        category: str,
        monthly_limit: Any,
        month: int,
        year: int,
    ) -> None:
        object.__setattr__(
            self,
            "budget_id",
            validate_non_empty_string(budget_id, "Budget ID"),
        )
        object.__setattr__(
            self,
            "category",
            validate_non_empty_string(category, "Category").capitalize(),
        )
        object.__setattr__(
            self,
            "monthly_limit",
            validate_amount(monthly_limit),
        )

        try:
            m = int(month)
            if not 1 <= m <= 12:
                raise ValueError
        except (ValueError, TypeError) as exc:
            from models.exceptions import InvalidTransactionError

            raise InvalidTransactionError(
                f"Invalid budget month '{month}'.",
                "Month must be an integer between 1 and 12.",
            ) from exc
        object.__setattr__(self, "month", m)

        try:
            y = int(year)
            if not 2000 <= y <= 2100:
                raise ValueError
        except (ValueError, TypeError) as exc:
            from models.exceptions import InvalidTransactionError

            raise InvalidTransactionError(
                f"Invalid budget year '{year}'.",
                "Year must be between 2000 and 2100.",
            ) from exc
        object.__setattr__(self, "year", y)

    @property
    def limit_float(self) -> float:
        """Monthly limit as float."""
        return float(self.monthly_limit)

    def calculate_remaining(self, current_spending: Decimal | float) -> Decimal:
        """Calculate remaining budget. Positive means under budget, negative means exceeded."""
        spent = Decimal(f"{float(current_spending):.2f}")
        return self.monthly_limit - spent

    def calculate_percentage_utilized(self, current_spending: Decimal | float) -> float:
        """Calculate percentage of budget spent (0.0% to >100.0%)."""
        spent = float(current_spending)
        limit = float(self.monthly_limit)
        if limit <= 0:
            return 0.0
        return round((spent / limit) * 100.0, 2)

    def is_exceeded(self, current_spending: Decimal | float) -> bool:
        """Return True if spending has strictly exceeded the monthly limit."""
        spent = Decimal(f"{float(current_spending):.2f}")
        return spent > self.monthly_limit

    def generate_status_report(self, current_spending: Decimal | float) -> dict[str, Any]:
        """Generate structured status dictionary for CLI and reporting."""
        spent_dec = Decimal(f"{float(current_spending):.2f}")
        remaining_dec = self.calculate_remaining(spent_dec)
        pct = self.calculate_percentage_utilized(spent_dec)
        exceeded = self.is_exceeded(spent_dec)

        status_text = "EXCEEDED" if exceeded else ("CRITICAL (>90%)" if pct >= 90 else "ON TRACK")

        return {
            "budget_id": self.budget_id,
            "category": self.category,
            "month": self.month,
            "year": self.year,
            "monthly_limit": float(self.monthly_limit),
            "current_spending": float(spent_dec),
            "remaining": float(remaining_dec),
            "percentage_utilized": pct,
            "is_exceeded": exceeded,
            "status_text": status_text,
            "formatted_limit": format_inr(self.monthly_limit),
            "formatted_spent": format_inr(spent_dec),
            "formatted_remaining": format_inr(remaining_dec),
        }

    def to_dict(self) -> dict[str, str]:
        """Serialize budget to dictionary for CSV storage."""
        return {
            "budget_id": self.budget_id,
            "category": self.category,
            "monthly_limit": f"{self.monthly_limit:.2f}",
            "month": str(self.month),
            "year": str(self.year),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Budget:
        """Deserialize budget from a dictionary."""
        return cls(
            budget_id=str(data["budget_id"]),
            category=str(data["category"]),
            monthly_limit=data["monthly_limit"],
            month=int(data["month"]),
            year=int(data["year"]),
        )

    def __str__(self) -> str:
        return (
            f"Budget({self.budget_id}) [{self.year}-{self.month:02d}] "
            f"{self.category}: Limit {format_inr(self.monthly_limit)}"
        )
