"""Transaction model representing income or expense entries."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from utils.helpers import format_inr
from utils.validators import (
    validate_amount,
    validate_date_string,
    validate_non_empty_string,
    validate_transaction_type,
)


@dataclass(slots=True)
class Transaction:
    """Represents a validated financial transaction."""

    transaction_id: str
    amount: Decimal
    category: str
    description: str
    transaction_date: str  # ISO format YYYY-MM-DD
    transaction_type: str  # 'income' or 'expense'
    account_name: str

    def __init__(
        self,
        transaction_id: str,
        amount: Any,
        category: str,
        description: str,
        transaction_date: str,
        transaction_type: str,
        account_name: str,
    ) -> None:
        object.__setattr__(
            self,
            "transaction_id",
            validate_non_empty_string(transaction_id, "Transaction ID"),
        )
        object.__setattr__(self, "amount", validate_amount(amount))
        object.__setattr__(
            self,
            "category",
            validate_non_empty_string(category, "Category").capitalize(),
        )
        object.__setattr__(
            self,
            "description",
            validate_non_empty_string(description, "Description"),
        )
        object.__setattr__(
            self,
            "transaction_date",
            validate_date_string(transaction_date),
        )
        object.__setattr__(
            self,
            "transaction_type",
            validate_transaction_type(transaction_type),
        )
        object.__setattr__(
            self,
            "account_name",
            validate_non_empty_string(account_name, "Account Name"),
        )

    @property
    def amount_float(self) -> float:
        """Return amount as a Python float for analytics and plotting."""
        return float(self.amount)

    @property
    def is_income(self) -> bool:
        """Check if transaction is income."""
        return self.transaction_type == "income"

    @property
    def is_expense(self) -> bool:
        """Check if transaction is an expense."""
        return self.transaction_type == "expense"

    def to_dict(self) -> dict[str, str]:
        """Serialize transaction to a string dictionary for CSV persistence."""
        return {
            "transaction_id": self.transaction_id,
            "amount": f"{self.amount:.2f}",
            "category": self.category,
            "description": self.description,
            "transaction_date": self.transaction_date,
            "transaction_type": self.transaction_type,
            "account_name": self.account_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Transaction:
        """Deserialize transaction from a dictionary."""
        required = [
            "transaction_id",
            "amount",
            "category",
            "description",
            "transaction_date",
            "transaction_type",
            "account_name",
        ]
        missing = [f for f in required if f not in data]
        if missing:
            from models.exceptions import InvalidTransactionError

            raise InvalidTransactionError(
                f"Missing required transaction fields: {', '.join(missing)}"
            )

        return cls(
            transaction_id=str(data["transaction_id"]),
            amount=data["amount"],
            category=str(data["category"]),
            description=str(data["description"]),
            transaction_date=str(data["transaction_date"]),
            transaction_type=str(data["transaction_type"]),
            account_name=str(data["account_name"]),
        )

    def __lt__(self, other: Transaction) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented
        # Order chronologically by date, then by amount, then ID
        if self.transaction_date != other.transaction_date:
            return self.transaction_date < other.transaction_date
        if self.amount != other.amount:
            return self.amount < other.amount
        return self.transaction_id < other.transaction_id

    def __str__(self) -> str:
        sign = "+" if self.is_income else "-"
        return (
            f"[{self.transaction_date}] {self.transaction_id} | "
            f"{sign}{format_inr(self.amount)} | {self.category} | "
            f"'{self.description}' ({self.account_name})"
        )

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.transaction_id!r}, amount={self.amount}, "
            f"type={self.transaction_type!r}, category={self.category!r}, "
            f"date={self.transaction_date!r}, account={self.account_name!r})"
        )
