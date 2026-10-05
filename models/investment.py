"""Simulated investment portfolio holding model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.exceptions import InvestmentValidationError
from utils.helpers import format_inr
from utils.validators import (
    validate_non_empty_string,
    validate_price,
    validate_quantity,
)


@dataclass(slots=True)
class Investment:
    """Represents a simulated asset holding in a simulated investment portfolio.

    DISCLAIMER: All calculations represent educational simulations based on user-entered
    or sample prices. No live market feeds or trade executions are performed.
    """

    investment_id: str
    asset_name: str
    asset_type: str
    quantity: float
    purchase_price: float
    current_price: float

    def __init__(
        self,
        investment_id: str,
        asset_name: str,
        asset_type: str,
        quantity: Any,
        purchase_price: Any,
        current_price: Any,
    ) -> None:
        object.__setattr__(
            self,
            "investment_id",
            validate_non_empty_string(investment_id, "Investment ID"),
        )
        object.__setattr__(
            self,
            "asset_name",
            validate_non_empty_string(asset_name, "Asset Name"),
        )
        object.__setattr__(
            self,
            "asset_type",
            validate_non_empty_string(asset_type, "Asset Type"),
        )
        object.__setattr__(self, "quantity", validate_quantity(quantity))
        object.__setattr__(
            self,
            "purchase_price",
            validate_price(purchase_price, "Purchase Price"),
        )
        object.__setattr__(
            self,
            "current_price",
            validate_price(current_price, "Current Price"),
        )

    @property
    def invested_amount(self) -> float:
        """Total capital invested: quantity * purchase_price."""
        return round(self.quantity * self.purchase_price, 2)

    @property
    def current_estimated_value(self) -> float:
        """Estimated current value based on user-entered or sample price."""
        return round(self.quantity * self.current_price, 2)

    @property
    def profit_loss(self) -> float:
        """Estimated absolute profit (+) or loss (-)."""
        return round(self.current_estimated_value - self.invested_amount, 2)

    @property
    def percentage_return(self) -> float:
        """Estimated percentage return (ROI). Handles zero cost safely."""
        if self.invested_amount <= 0:
            return 0.0
        return round((self.profit_loss / self.invested_amount) * 100.0, 2)

    def update_current_price(self, new_price: Any) -> None:
        """Update current estimated market price."""
        valid_price = validate_price(new_price, "Current Price")
        object.__setattr__(self, "current_price", valid_price)

    def add_shares(self, additional_qty: Any, buy_price: Any) -> None:
        """Add holdings and recompute weighted average purchase price."""
        qty = validate_quantity(additional_qty)
        price = validate_price(buy_price, "Buy Price")

        new_total_qty = self.quantity + qty
        new_total_cost = self.invested_amount + (qty * price)
        new_avg_price = round(new_total_cost / new_total_qty, 2)

        object.__setattr__(self, "quantity", round(new_total_qty, 4))
        object.__setattr__(self, "purchase_price", new_avg_price)

    def remove_shares(self, reduce_qty: Any) -> None:
        """Reduce holding quantity (simulated sale)."""
        qty = validate_quantity(reduce_qty)
        if qty > self.quantity:
            raise InvestmentValidationError(
                f"Cannot sell {qty} units. Current holding is only {self.quantity} units.",
                "Enter a quantity less than or equal to current holding.",
            )

        new_qty = round(self.quantity - qty, 4)
        if new_qty <= 0:
            raise InvestmentValidationError(
                "Resulting quantity would be zero. Delete the holding instead.",
                "Use delete holding option to completely remove an asset.",
            )
        object.__setattr__(self, "quantity", new_qty)

    def generate_summary(self) -> dict[str, Any]:
        """Generate structured performance dictionary."""
        pnl = self.profit_loss
        roi = self.percentage_return
        return {
            "investment_id": self.investment_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "quantity": self.quantity,
            "purchase_price": self.purchase_price,
            "current_price": self.current_price,
            "invested_amount": self.invested_amount,
            "current_estimated_value": self.current_estimated_value,
            "profit_loss": pnl,
            "percentage_return": roi,
            "formatted_invested": format_inr(self.invested_amount),
            "formatted_value": format_inr(self.current_estimated_value),
            "formatted_pnl": format_inr(pnl),
            "status": "PROFIT" if pnl > 0 else ("LOSS" if pnl < 0 else "BREAK-EVEN"),
        }

    def to_dict(self) -> dict[str, str]:
        """Serialize investment holding to dictionary for CSV storage."""
        return {
            "investment_id": self.investment_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "quantity": f"{self.quantity:.4f}",
            "purchase_price": f"{self.purchase_price:.2f}",
            "current_price": f"{self.current_price:.2f}",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Investment:
        """Deserialize investment from dictionary."""
        return cls(
            investment_id=str(data["investment_id"]),
            asset_name=str(data["asset_name"]),
            asset_type=str(data["asset_type"]),
            quantity=data["quantity"],
            purchase_price=data["purchase_price"],
            current_price=data["current_price"],
        )

    def __str__(self) -> str:
        return (
            f"[{self.asset_type}] {self.asset_name} ({self.quantity} units @ {format_inr(self.purchase_price)}) | "
            f"Est. Value: {format_inr(self.current_estimated_value)} | Return: {self.percentage_return:+.2f}%"
        )
