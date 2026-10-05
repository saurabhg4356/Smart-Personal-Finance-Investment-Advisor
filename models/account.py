"""Account models demonstrating encapsulation, inheritance, and polymorphism."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from models.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    InvalidTransactionError,
)
from models.transaction import Transaction
from utils.helpers import format_inr
from utils.validators import (
    validate_amount,
    validate_non_empty_string,
    validate_price,
)


class Account:
    """Base class for all financial accounts demonstrating encapsulation."""

    def __init__(
        self,
        account_id: str,
        account_name: str,
        opening_balance: Any = 0.0,
        current_balance: Any | None = None,
        account_type: str = "Standard",
    ) -> None:
        self.account_id = validate_non_empty_string(account_id, "Account ID")
        self.account_name = validate_non_empty_string(account_name, "Account Name")
        self.account_type = validate_non_empty_string(account_type, "Account Type")

        opening = validate_price(opening_balance, "Opening balance")
        self._opening_balance = Decimal(f"{opening:.2f}")

        if current_balance is not None:
            curr = validate_price(current_balance, "Current balance")
            self._current_balance = Decimal(f"{curr:.2f}")
        else:
            self._current_balance = self._opening_balance

    @property
    def opening_balance(self) -> Decimal:
        """Read-only access to opening balance."""
        return self._opening_balance

    @property
    def current_balance(self) -> Decimal:
        """Encapsulated current balance."""
        return self._current_balance

    def get_balance(self) -> Decimal:
        """Get the current balance."""
        return self._current_balance

    def deposit(self, amount: Any) -> None:
        """Deposit funds into account."""
        valid_amt = validate_amount(amount)
        self._current_balance += valid_amt

    def withdraw(self, amount: Any) -> None:
        """Withdraw funds from account with insufficient funds check."""
        valid_amt = validate_amount(amount)
        if valid_amt > self._current_balance:
            raise InsufficientFundsError(
                account_name=self.account_name,
                current_balance=float(self._current_balance),
                requested_amount=float(valid_amt),
            )
        self._current_balance -= valid_amt

    def apply_transaction(self, transaction: Transaction) -> None:
        """Apply an income or expense transaction to this account balance."""
        if transaction.account_name.strip().lower() != self.account_name.strip().lower():
            raise InvalidTransactionError(
                f"Transaction account '{transaction.account_name}' does not match '{self.account_name}'."
            )

        if transaction.is_income:
            self.deposit(transaction.amount)
        elif transaction.is_expense:
            self.withdraw(transaction.amount)

    def reverse_transaction(self, transaction: Transaction) -> None:
        """Reverse a previously applied transaction (used for undo operations)."""
        if transaction.account_name.strip().lower() != self.account_name.strip().lower():
            raise InvalidTransactionError(
                f"Transaction account '{transaction.account_name}' does not match '{self.account_name}'."
            )

        if transaction.is_income:
            # Reversing income means taking away the deposited funds
            if transaction.amount > self._current_balance:
                raise InsufficientFundsError(
                    account_name=self.account_name,
                    current_balance=float(self._current_balance),
                    requested_amount=float(transaction.amount),
                    resolution_hint="Cannot reverse income because funds have already been spent.",
                )
            self._current_balance -= transaction.amount
        elif transaction.is_expense:
            # Reversing expense restores the spent funds
            self._current_balance += transaction.amount

    def calculate_value(self) -> Decimal:
        """Polymorphic method returning the total net value of this account."""
        return self._current_balance

    def generate_summary(self) -> dict[str, Any]:
        """Generate structured account summary dictionary (polymorphic)."""
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "account_type": self.account_type,
            "opening_balance": float(self._opening_balance),
            "current_balance": float(self._current_balance),
            "total_value": float(self.calculate_value()),
            "formatted_balance": format_inr(self._current_balance),
        }

    def to_dict(self) -> dict[str, str]:
        """Serialize account to dictionary for CSV storage."""
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "opening_balance": f"{self._opening_balance:.2f}",
            "current_balance": f"{self._current_balance:.2f}",
            "account_type": self.account_type,
            "extra_info": "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Account:
        """Factory method deserializing appropriate Account subclass."""
        account_type = str(data.get("account_type", "Standard")).strip()
        acc_id = str(data["account_id"])
        name = str(data["account_name"])
        opening = data["opening_balance"]
        current = data.get("current_balance", opening)
        extra = str(data.get("extra_info", ""))

        if account_type.lower() == "savings":
            interest_rate = 4.0
            if extra:
                try:
                    interest_rate = float(extra)
                except ValueError:
                    pass
            return SavingsAccount(
                account_id=acc_id,
                account_name=name,
                opening_balance=opening,
                current_balance=current,
                interest_rate_percent=interest_rate,
            )
        elif account_type.lower() == "investment":
            return InvestmentAccount(
                account_id=acc_id,
                account_name=name,
                opening_balance=opening,
                current_balance=current,
            )
        else:
            return cls(
                account_id=acc_id,
                account_name=name,
                opening_balance=opening,
                current_balance=current,
                account_type=account_type,
            )

    def __str__(self) -> str:
        return (
            f"Account({self.account_id}): {self.account_name} "
            f"[{self.account_type}] - Balance: {format_inr(self._current_balance)}"
        )

    def __repr__(self) -> str:
        return (
            f"Account(id={self.account_id!r}, name={self.account_name!r}, "
            f"type={self.account_type!r}, balance={self._current_balance})"
        )


class SavingsAccount(Account):
    """Subclass representing a savings account with interest calculation."""

    def __init__(
        self,
        account_id: str,
        account_name: str,
        opening_balance: Any = 0.0,
        current_balance: Any | None = None,
        interest_rate_percent: float = 4.0,
    ) -> None:
        super().__init__(
            account_id=account_id,
            account_name=account_name,
            opening_balance=opening_balance,
            current_balance=current_balance,
            account_type="Savings",
        )
        if interest_rate_percent < 0:
            raise InvalidAmountError("Interest rate cannot be negative.")
        self.interest_rate_percent = float(interest_rate_percent)

    def calculate_interest(self, months: int = 1) -> Decimal:
        """Calculate simple interest on the current balance for given number of months."""
        if months <= 0:
            return Decimal("0.00")
        # Formula: P * R * T / 100 where T is years (months / 12)
        rate = Decimal(str(self.interest_rate_percent))
        time_years = Decimal(str(months)) / Decimal("12")
        interest = (self._current_balance * rate * time_years) / Decimal("100")
        return interest.quantize(Decimal("0.01"))

    def generate_summary(self) -> dict[str, Any]:
        """Override to include savings-specific details."""
        summary = super().generate_summary()
        est_monthly_interest = self.calculate_interest(1)
        est_annual_interest = self.calculate_interest(12)
        summary.update(
            {
                "interest_rate_percent": self.interest_rate_percent,
                "projected_monthly_interest": float(est_monthly_interest),
                "projected_annual_interest": float(est_annual_interest),
                "formatted_monthly_interest": format_inr(est_monthly_interest),
            }
        )
        return summary

    def to_dict(self) -> dict[str, str]:
        data = super().to_dict()
        data["extra_info"] = str(self.interest_rate_percent)
        return data


class InvestmentAccount(Account):
    """Subclass representing an investment account linked to simulated holdings."""

    def __init__(
        self,
        account_id: str,
        account_name: str,
        opening_balance: Any = 0.0,
        current_balance: Any | None = None,
    ) -> None:
        super().__init__(
            account_id=account_id,
            account_name=account_name,
            opening_balance=opening_balance,
            current_balance=current_balance,
            account_type="Investment",
        )
        self._portfolio_holdings_value = Decimal("0.00")

    def set_holdings_value(self, holdings_value: Any) -> None:
        """Update the aggregate estimated value of simulated portfolio holdings."""
        val = validate_price(holdings_value, "Portfolio holdings value")
        self._portfolio_holdings_value = Decimal(f"{val:.2f}")

    def calculate_value(self) -> Decimal:
        """Polymorphic override: Total value = Cash balance + Holdings estimated value."""
        return self._current_balance + self._portfolio_holdings_value

    def generate_summary(self) -> dict[str, Any]:
        """Override to include cash + simulated investments value."""
        summary = super().generate_summary()
        summary.update(
            {
                "cash_balance": float(self._current_balance),
                "holdings_value": float(self._portfolio_holdings_value),
                "total_portfolio_value": float(self.calculate_value()),
                "formatted_total_value": format_inr(self.calculate_value()),
            }
        )
        return summary
