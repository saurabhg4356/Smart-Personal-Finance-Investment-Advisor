"""Data Structures & Algorithms utilities for financial management.

Demonstrates:
1. Hash Maps: Average O(1) key-based lookups and group aggregations.
2. Heap / Priority Queue: O(N log K) top-K largest expense retrieval via heapq.
3. Binary Search: O(log N + M) range queries on date-sorted transactions via bisect.
4. Stack (LIFO): O(1) undo history tracking for state rollback and balance restoration.
"""

from __future__ import annotations

import bisect
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
import heapq
from typing import Any, Callable

from models.account import Account
from models.budget import Budget
from models.exceptions import InvalidTransactionError
from models.transaction import Transaction
from utils.validators import validate_date_string


# ============================================================================
# 1. HASH MAPS (Dictionary lookups & Category Aggregations)
# ============================================================================


def build_transaction_index(transactions: list[Transaction]) -> dict[str, Transaction]:
    """Build a hash map index from transaction_id to Transaction.

    Complexity:
        Time: O(N) to construct, average O(1) lookup by ID.
        Space: O(N).
    """
    return {tx.transaction_id: tx for tx in transactions}


def build_account_index(accounts: list[Account]) -> dict[str, Account]:
    """Build a hash map index for accounts keyed by lowercase account name.

    Complexity:
        Time: O(M) to construct, average O(1) lookup.
        Space: O(M).
    """
    return {acc.account_name.strip().lower(): acc for acc in accounts}


def build_budget_index(budgets: list[Budget]) -> dict[tuple[str, int, int], Budget]:
    """Build a composite-key hash map index for budgets: (category_lower, month, year).

    Complexity:
        Time: O(B) to construct, average O(1) lookup.
        Space: O(B).
    """
    return {(b.category.strip().lower(), b.month, b.year): b for b in budgets}


def aggregate_expenses_by_category(transactions: list[Transaction]) -> dict[str, Decimal]:
    """Aggregate total expense amounts by category using a hash map (dict).

    Complexity:
        Time: O(N) where N is number of transactions.
        Space: O(C) where C is the number of unique expense categories.
    """
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for tx in transactions:
        if tx.is_expense:
            totals[tx.category] += tx.amount
    return dict(totals)


# ============================================================================
# 2. HEAP / PRIORITY QUEUE (Top-K Expenses)
# ============================================================================


def get_top_expenses(transactions: list[Transaction], limit: int = 5) -> list[Transaction]:
    """Retrieve the top-K largest expense transactions using Python's heapq.

    Ignores income transactions.
    Avoids sorting the entire dataset O(N log N). Uses heapq.nlargest which maintains
    a min-heap of size K, yielding O(N log K) time complexity.

    Determinism:
        When amounts are equal, secondary sort compares transaction_date (descending)
        and then transaction_id.

    Args:
        transactions: List of transactions.
        limit: Number of top expenses to return. If <= 0 or empty input, returns [].

    Returns:
        List of up to K highest expense transactions in descending order of amount.
    """
    if limit <= 0 or not transactions:
        return []

    expense_txs = [tx for tx in transactions if tx.is_expense]
    if not expense_txs:
        return []

    # Sort key: (amount, date, id) for deterministic tie-breaking
    def heap_key(tx: Transaction) -> tuple[Decimal, str, str]:
        return (tx.amount, tx.transaction_date, tx.transaction_id)

    return heapq.nlargest(min(limit, len(expense_txs)), expense_txs, key=heap_key)


# ============================================================================
# 3. BINARY SEARCH (Date Range Filtering via Bisect)
# ============================================================================


def filter_transactions_by_date_range(
    sorted_transactions: list[Transaction],
    start_date: str,
    end_date: str,
) -> list[Transaction]:
    """Filter transactions within [start_date, end_date] inclusive using binary search (bisect).

    Assumptions:
        `sorted_transactions` MUST already be sorted in ascending order of `transaction_date`.

    Complexity:
        Time: O(log N + M) where N = len(sorted_transactions), M = matching slice size.
        This is significantly faster than an O(N) linear filter on large historical datasets.
        Space: O(M) for the returned slice.

    Args:
        sorted_transactions: Pre-sorted list of transactions.
        start_date: ISO date string 'YYYY-MM-DD'.
        end_date: ISO date string 'YYYY-MM-DD'.

    Returns:
        Transactions occurring between start_date and end_date, inclusive.

    Raises:
        InvalidTransactionError: If start_date > end_date or dates are invalid.
    """
    valid_start = validate_date_string(start_date)
    valid_end = validate_date_string(end_date)

    if valid_start > valid_end:
        raise InvalidTransactionError(
            f"Start date '{start_date}' cannot be after end date '{end_date}'.",
            "Ensure start_date <= end_date.",
        )

    if not sorted_transactions:
        return []

    # Extract dates for bisect search
    dates = [tx.transaction_date for tx in sorted_transactions]

    # bisect_left finds first transaction with date >= valid_start
    left_idx = bisect.bisect_left(dates, valid_start)

    # bisect_right finds first transaction with date > valid_end
    right_idx = bisect.bisect_right(dates, valid_end)

    return sorted_transactions[left_idx:right_idx]


# ============================================================================
# 4. STACK / LIFO (Undo Management)
# ============================================================================


@dataclass(slots=True)
class UndoAction:
    """Represents a reversible transaction state change."""

    action_type: str  # 'ADD', 'DELETE', 'EDIT'
    previous_transaction: Transaction | None
    current_transaction: Transaction | None
    account_name: str
    description: str


class UndoStack:
    """LIFO (Last-In-First-Out) stack for undoing supported transaction operations.

    Operations supported:
        - ADD_TRANSACTION (undo deletes the added transaction and reverses balance)
        - DELETE_TRANSACTION (undo re-inserts the deleted transaction and reapplies balance)
        - EDIT_TRANSACTION (undo reverts transaction fields and adjusts balance difference)

    Complexity:
        Push: O(1)
        Pop: O(1)
        Peek: O(1)
        Space: O(U) where U is the number of undoable operations stored.
    """

    def __init__(self, max_depth: int = 100) -> None:
        self._stack: list[UndoAction] = []
        self.max_depth = max_depth

    def push(self, action: UndoAction) -> None:
        """Push a reversible action onto the stack."""
        if len(self._stack) >= self.max_depth:
            self._stack.pop(0)  # Evict oldest action if max depth exceeded
        self._stack.append(action)

    def pop(self) -> UndoAction | None:
        """Pop the most recent action from the stack. Returns None if empty."""
        if not self._stack:
            return None
        return self._stack.pop()

    def peek(self) -> UndoAction | None:
        """Inspect the top action without removing it."""
        if not self._stack:
            return None
        return self._stack[-1]

    def is_empty(self) -> bool:
        """Check if stack is empty."""
        return len(self._stack) == 0

    def size(self) -> int:
        """Number of undoable actions in the stack."""
        return len(self._stack)

    def clear(self) -> None:
        """Clear all undo history."""
        self._stack.clear()
