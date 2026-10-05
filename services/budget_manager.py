"""Budget management service for budget tracking, status analysis, and alerts."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from models.budget import Budget
from models.exceptions import BudgetExceededError, InvalidTransactionError
from models.transaction import Transaction
from services.dsa_utils import build_budget_index
from services.storage import StorageService


class BudgetManager:
    """Coordinates monthly category budgets and spending enforcement."""

    def __init__(
        self,
        storage_service: StorageService | None = None,
        budgets_file: Path | str = "data/budgets.csv",
    ) -> None:
        self.storage = storage_service or StorageService()
        self.file_path = Path(budgets_file)
        self._budgets: list[Budget] = []
        self._budget_index: dict[tuple[str, int, int], Budget] = {}
        self.load()

    def load(self) -> None:
        """Load budgets from CSV storage and build index."""
        self._budgets = self.storage.load_budgets(self.file_path)
        self._rebuild_index()

    def save(self) -> None:
        """Persist current budgets to CSV storage."""
        self.storage.save_budgets(self._budgets, self.file_path)

    def _rebuild_index(self) -> None:
        """Rebuild composite-key hash map index for O(1) lookups."""
        self._budget_index = build_budget_index(self._budgets)

    def list_budgets(self) -> list[Budget]:
        """Return list of all configured budgets."""
        return list(self._budgets)

    def get_budget(self, category: str, month: int, year: int) -> Budget | None:
        """O(1) hash map lookup for a budget by category, month, and year."""
        key = (category.strip().lower(), int(month), int(year))
        return self._budget_index.get(key)

    def set_budget(
        self,
        category: str,
        monthly_limit: Any,
        month: int,
        year: int,
        budget_id: str | None = None,
    ) -> Budget:
        """Create or update a monthly category budget."""
        existing = self.get_budget(category, month, year)
        if existing:
            # Update existing
            existing_idx = self._budgets.index(existing)
            updated = Budget(
                budget_id=existing.budget_id,
                category=category,
                monthly_limit=monthly_limit,
                month=month,
                year=year,
            )
            self._budgets[existing_idx] = updated
            self._rebuild_index()
            self.save()
            return updated
        else:
            bid = budget_id or f"B-{year}{month:02d}-{len(self._budgets) + 1:03d}"
            new_budget = Budget(
                budget_id=bid,
                category=category,
                monthly_limit=monthly_limit,
                month=month,
                year=year,
            )
            self._budgets.append(new_budget)
            self._rebuild_index()
            self.save()
            return new_budget

    def delete_budget(self, budget_id: str) -> bool:
        """Delete budget by budget ID. Returns True if deleted."""
        target = next((b for b in self._budgets if b.budget_id == budget_id), None)
        if target:
            self._budgets.remove(target)
            self._rebuild_index()
            self.save()
            return True
        return False

    @staticmethod
    def calculate_category_spending(
        transactions: list[Transaction], category: str, month: int, year: int
    ) -> Decimal:
        """Calculate total expense for a specific category in given month/year."""
        cat_lower = category.strip().lower()
        prefix = f"{year:04d}-{month:02d}"
        total = Decimal("0.00")
        for tx in transactions:
            if (
                tx.is_expense
                and tx.category.strip().lower() == cat_lower
                and tx.transaction_date.startswith(prefix)
            ):
                total += tx.amount
        return total

    def evaluate_transaction(
        self,
        transaction: Transaction,
        all_transactions: list[Transaction],
        strict_mode: bool = False,
    ) -> tuple[bool, str | None]:
        """Check if an expense transaction would cause a budget overrun.

        Returns:
            (is_ok, warning_message_or_none)
        """
        if not transaction.is_expense:
            return True, None

        # Parse year and month from transaction_date
        y, m, _ = [int(p) for p in transaction.transaction_date.split("-")]
        budget = self.get_budget(transaction.category, m, y)
        if not budget:
            return True, None

        current_spent = self.calculate_category_spending(
            all_transactions, transaction.category, m, y
        )
        new_spent = current_spent + transaction.amount

        if new_spent > budget.monthly_limit:
            msg = (
                f"Budget Warning: Spending for '{transaction.category}' will reach "
                f"₹{new_spent:,.2f} exceeding monthly limit of ₹{budget.monthly_limit:,.2f}."
            )
            if strict_mode:
                raise BudgetExceededError(
                    category=transaction.category,
                    current_spent=float(new_spent),
                    monthly_limit=float(budget.monthly_limit),
                )
            return False, msg

        return True, None

    def get_all_budget_statuses(
        self, transactions: list[Transaction]
    ) -> list[dict[str, Any]]:
        """Compute status reports for all configured budgets."""
        reports = []
        for budget in self._budgets:
            spent = self.calculate_category_spending(
                transactions, budget.category, budget.month, budget.year
            )
            reports.append(budget.generate_status_report(spent))
        return reports
