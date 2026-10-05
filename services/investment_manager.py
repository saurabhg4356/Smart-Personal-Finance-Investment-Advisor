"""Investment management service for simulated portfolio tracking and valuation."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from models.exceptions import InvestmentValidationError
from models.investment import Investment
from services.storage import StorageService
from utils.helpers import format_inr
from utils.validators import validate_price, validate_quantity


class InvestmentManager:
    """Manages simulated investment holdings, valuation, and asset allocation."""

    DISCLAIMER = (
        "EDUCATIONAL SIMULATION NOTICE: All holdings, valuations, profits, and returns "
        "are simulated estimates based on user-entered or sample prices. "
        "This application does not connect to live exchanges and does not provide financial advice."
    )

    def __init__(
        self,
        storage_service: StorageService | None = None,
        investments_file: Path | str = "data/investments.csv",
    ) -> None:
        self.storage = storage_service or StorageService()
        self.file_path = Path(investments_file)
        self._investments: list[Investment] = []
        self.load()

    def load(self) -> None:
        """Load simulated holdings from CSV."""
        self._investments = self.storage.load_investments(self.file_path)

    def save(self) -> None:
        """Persist simulated holdings to CSV."""
        self.storage.save_investments(self._investments, self.file_path)

    def list_investments(self) -> list[Investment]:
        """Return list of all current simulated holdings."""
        return list(self._investments)

    def get_investment(self, investment_id: str) -> Investment | None:
        """Find an investment by ID."""
        for inv in self._investments:
            if inv.investment_id.strip().lower() == investment_id.strip().lower():
                return inv
        return None

    def add_investment(
        self,
        asset_name: str,
        asset_type: str,
        quantity: Any,
        purchase_price: Any,
        current_price: Any | None = None,
        investment_id: str | None = None,
    ) -> Investment:
        """Add a new simulated holding or accumulate into an existing one."""
        cleaned_name = asset_name.strip()
        curr_price = purchase_price if current_price is None else current_price

        # Check if asset with same name and type already exists
        existing = next(
            (
                inv
                for inv in self._investments
                if inv.asset_name.lower() == cleaned_name.lower()
                and inv.asset_type.lower() == asset_type.strip().lower()
            ),
            None,
        )

        if existing:
            existing.add_shares(quantity, purchase_price)
            if current_price is not None:
                existing.update_current_price(curr_price)
            self.save()
            return existing

        inv_id = investment_id or f"INV-{len(self._investments) + 1:03d}"
        inv = Investment(
            investment_id=inv_id,
            asset_name=cleaned_name,
            asset_type=asset_type.strip(),
            quantity=quantity,
            purchase_price=purchase_price,
            current_price=curr_price,
        )
        self._investments.append(inv)
        self.save()
        return inv

    def remove_investment(self, investment_id: str) -> bool:
        """Delete an investment holding completely."""
        target = self.get_investment(investment_id)
        if target:
            self._investments.remove(target)
            self.save()
            return True
        return False

    def sell_shares(self, investment_id: str, quantity_to_sell: Any) -> Investment:
        """Partially sell shares from an existing holding."""
        target = self.get_investment(investment_id)
        if not target:
            raise InvestmentValidationError(f"Investment holding '{investment_id}' not found.")
        target.remove_shares(quantity_to_sell)
        self.save()
        return target

    def update_price(self, investment_id: str, new_price: Any) -> Investment:
        """Update estimated market price for an asset."""
        target = self.get_investment(investment_id)
        if not target:
            raise InvestmentValidationError(f"Investment holding '{investment_id}' not found.")
        target.update_current_price(new_price)
        self.save()
        return target

    def calculate_portfolio_totals(self) -> dict[str, Any]:
        """Calculate aggregate portfolio totals, P&L, and asset allocations."""
        total_invested = sum(inv.invested_amount for inv in self._investments)
        total_value = sum(inv.current_estimated_value for inv in self._investments)
        total_pnl = round(total_value - total_invested, 2)
        total_roi = (
            round((total_pnl / total_invested) * 100.0, 2) if total_invested > 0 else 0.0
        )

        # Allocation by asset type
        type_allocation: dict[str, float] = defaultdict(float)
        for inv in self._investments:
            type_allocation[inv.asset_type] += inv.current_estimated_value

        type_pcts = {}
        for a_type, val in type_allocation.items():
            pct = round((val / total_value) * 100.0, 2) if total_value > 0 else 0.0
            type_pcts[a_type] = {"value": round(val, 2), "percentage": pct}

        return {
            "total_holdings_count": len(self._investments),
            "total_invested": round(total_invested, 2),
            "total_estimated_value": round(total_value, 2),
            "total_profit_loss": total_pnl,
            "total_return_percentage": total_roi,
            "formatted_invested": format_inr(total_invested),
            "formatted_value": format_inr(total_value),
            "formatted_pnl": format_inr(total_pnl),
            "asset_type_allocation": type_pcts,
            "disclaimer": self.DISCLAIMER,
        }
