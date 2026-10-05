"""Unit tests for BudgetManager service and spending alert evaluations."""

from decimal import Decimal
import pytest

from models.exceptions import BudgetExceededError
from models.transaction import Transaction
from services.budget_manager import BudgetManager
from services.storage import StorageService


@pytest.fixture
def budget_manager(tmp_path):
    storage = StorageService(base_data_dir=tmp_path)
    b_file = tmp_path / "budgets.csv"
    return BudgetManager(storage_service=storage, budgets_file=b_file)


def test_set_and_get_budget(budget_manager):
    b1 = budget_manager.set_budget("Food", 10000.0, month=3, year=2026)
    assert b1.monthly_limit == Decimal("10000.00")

    found = budget_manager.get_budget("food", 3, 2026)
    assert found is not None
    assert found.budget_id == b1.budget_id

    # Update existing budget
    updated = budget_manager.set_budget("Food", 12500.0, month=3, year=2026)
    assert updated.monthly_limit == Decimal("12500.00")
    assert len(budget_manager.list_budgets()) == 1


def test_delete_budget(budget_manager):
    b = budget_manager.set_budget("Travel", 15000.0, month=4, year=2026)
    assert len(budget_manager.list_budgets()) == 1

    deleted = budget_manager.delete_budget(b.budget_id)
    assert deleted is True
    assert len(budget_manager.list_budgets()) == 0


def test_evaluate_budget_spending(budget_manager):
    budget_manager.set_budget("Dining", 5000.0, month=3, year=2026)

    txs = [
        Transaction("TX-1", 3000.0, "Dining", "Dinner", "2026-03-02", "expense", "HDFC"),
        Transaction("TX-2", 1500.0, "Dining", "Lunch", "2026-03-10", "expense", "HDFC"),
    ]

    # Current spent: 4500. Adding 1000 will exceed 5000 limit
    new_tx = Transaction("TX-3", 1000.0, "Dining", "Snacks", "2026-03-15", "expense", "HDFC")

    # Non-strict mode returns warning
    is_ok, warn_msg = budget_manager.evaluate_transaction(new_tx, txs, strict_mode=False)
    assert is_ok is False
    assert warn_msg is not None
    assert "will reach ₹5,500.00" in warn_msg

    # Strict mode raises BudgetExceededError
    with pytest.raises(BudgetExceededError):
        budget_manager.evaluate_transaction(new_tx, txs, strict_mode=True)


def test_all_budget_statuses(budget_manager):
    budget_manager.set_budget("Groceries", 10000.0, month=3, year=2026)
    txs = [
        Transaction("TX-1", 6000.0, "Groceries", "Supermarket", "2026-03-05", "expense", "HDFC")
    ]
    statuses = budget_manager.get_all_budget_statuses(txs)
    assert len(statuses) == 1
    assert statuses[0]["category"] == "Groceries"
    assert statuses[0]["current_spending"] == 6000.0
    assert statuses[0]["remaining"] == 4000.0
    assert statuses[0]["percentage_utilized"] == 60.0
    assert statuses[0]["is_exceeded"] is False
