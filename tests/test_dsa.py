"""Unit tests for Data Structures and Algorithms (Hash maps, Heap, Bisect, UndoStack)."""

from decimal import Decimal
import pytest

from models.account import Account
from models.budget import Budget
from models.exceptions import InvalidTransactionError
from models.transaction import Transaction
from services.dsa_utils import (
    UndoAction,
    UndoStack,
    aggregate_expenses_by_category,
    build_account_index,
    build_budget_index,
    build_transaction_index,
    filter_transactions_by_date_range,
    get_top_expenses,
)


@pytest.fixture
def sample_transactions():
    return [
        Transaction("TX-1", 1200.0, "Food", "Lunch", "2026-01-05", "expense", "HDFC"),
        Transaction("TX-2", 45000.0, "Salary", "Salary credit", "2026-01-05", "income", "HDFC"),
        Transaction("TX-3", 3500.0, "Shopping", "Shoes", "2026-01-10", "expense", "HDFC"),
        Transaction("TX-4", 800.0, "Food", "Coffee", "2026-01-15", "expense", "HDFC"),
        Transaction("TX-5", 7200.0, "Utilities", "Electricity", "2026-01-20", "expense", "HDFC"),
        Transaction("TX-6", 3500.0, "Transport", "Train ticket", "2026-01-25", "expense", "HDFC"),
    ]


# ==================== HASH MAP TESTS ====================


def test_hash_map_transaction_index(sample_transactions):
    index = build_transaction_index(sample_transactions)
    assert len(index) == 6
    assert index["TX-3"].amount == Decimal("3500.00")
    assert "TX-999" not in index


def test_hash_map_account_index():
    accounts = [
        Account("ACC-1", "HDFC Salary", 10000.0),
        Account("ACC-2", "ICICI Savings", 20000.0),
    ]
    index = build_account_index(accounts)
    assert "hdfc salary" in index
    assert index["hdfc salary"].account_id == "ACC-1"


def test_hash_map_budget_index():
    budgets = [
        Budget("B-1", "Food", 5000.0, 1, 2026),
        Budget("B-2", "Utilities", 3000.0, 1, 2026),
    ]
    index = build_budget_index(budgets)
    key = ("food", 1, 2026)
    assert key in index
    assert index[key].budget_id == "B-1"


def test_hash_map_category_aggregation(sample_transactions):
    totals = aggregate_expenses_by_category(sample_transactions)
    # Food: 1200 + 800 = 2000
    assert totals["Food"] == Decimal("2000.00")
    # Salary is income, should not be in expense totals
    assert "Salary" not in totals
    assert totals["Utilities"] == Decimal("7200.00")


# ==================== HEAP / PRIORITY QUEUE TESTS ====================


def test_heap_top_expenses(sample_transactions):
    # Expenses: 7200 (TX-5), 3500 (TX-3, TX-6), 1200 (TX-1), 800 (TX-4)
    # Income 45000 (TX-2) must be excluded
    top3 = get_top_expenses(sample_transactions, limit=3)
    assert len(top3) == 3
    assert top3[0].amount == Decimal("7200.00")
    assert top3[1].amount == Decimal("3500.00")
    assert top3[2].amount == Decimal("3500.00")


def test_heap_edge_cases():
    assert get_top_expenses([], limit=5) == []
    assert get_top_expenses([], limit=0) == []
    assert get_top_expenses([], limit=-2) == []

    income_only = [
        Transaction("TX-1", 5000, "Salary", "Bonus", "2026-01-01", "income", "HDFC")
    ]
    assert get_top_expenses(income_only, limit=3) == []


# ==================== BINARY SEARCH TESTS ====================


def test_binary_search_date_filtering(sample_transactions):
    # sample_transactions are already sorted: dates 01-05, 01-05, 01-10, 01-15, 01-20, 01-25
    filtered = filter_transactions_by_date_range(
        sample_transactions, "2026-01-08", "2026-01-20"
    )
    # Should include: TX-3 (01-10), TX-4 (01-15), TX-5 (01-20)
    assert len(filtered) == 3
    assert [tx.transaction_id for tx in filtered] == ["TX-3", "TX-4", "TX-5"]


def test_binary_search_exact_and_duplicate_dates(sample_transactions):
    # Query exact single day with duplicate records: 2026-01-05 (TX-1 and TX-2)
    filtered = filter_transactions_by_date_range(
        sample_transactions, "2026-01-05", "2026-01-05"
    )
    assert len(filtered) == 2
    assert [tx.transaction_id for tx in filtered] == ["TX-1", "TX-2"]


def test_binary_search_invalid_range():
    with pytest.raises(InvalidTransactionError):
        filter_transactions_by_date_range([], "2026-02-10", "2026-02-01")


# ==================== UNDO STACK (LIFO) TESTS ====================


def test_undo_stack_operations():
    stack = UndoStack(max_depth=3)
    assert stack.is_empty() is True
    assert stack.pop() is None

    action1 = UndoAction("ADD", None, None, "HDFC", "Add 1")
    action2 = UndoAction("EDIT", None, None, "HDFC", "Edit 2")
    action3 = UndoAction("DELETE", None, None, "HDFC", "Delete 3")

    stack.push(action1)
    stack.push(action2)
    assert stack.size() == 2
    assert stack.peek() == action2

    popped = stack.pop()
    assert popped == action2
    assert stack.size() == 1

    # Max depth test
    stack.push(action2)
    stack.push(action3)
    action4 = UndoAction("ADD", None, None, "HDFC", "Add 4")
    stack.push(action4)  # Exceeds depth 3, action1 evicted
    assert stack.size() == 3

    pop_top = stack.pop()
    assert pop_top == action4
