"""Finance manager orchestrating transactions, accounts, undo stack, and persistence."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from models.account import Account, InvestmentAccount, SavingsAccount
from models.exceptions import (
    AccountNotFoundError,
    FinanceAdvisorError,
    InsufficientFundsError,
    InvalidTransactionError,
    TransactionNotFoundError,
)
from models.transaction import Transaction
from services.dsa_utils import (
    UndoAction,
    UndoStack,
    build_account_index,
    build_transaction_index,
    filter_transactions_by_date_range,
    get_top_expenses,
)
from services.storage import StorageService


class FinanceManager:
    """Core financial management service coordinating accounts, transactions, and DSA operations."""

    def __init__(
        self,
        storage_service: StorageService | None = None,
        transactions_file: Path | str = "data/transactions.csv",
        accounts_file: Path | str = "data/accounts.csv",
    ) -> None:
        self.storage = storage_service or StorageService()
        self.tx_file = Path(transactions_file)
        self.acc_file = Path(accounts_file)

        self._transactions: list[Transaction] = []
        self._tx_index: dict[str, Transaction] = {}

        self._accounts: list[Account] = []
        self._acc_index: dict[str, Account] = {}

        self.undo_stack = UndoStack()

        self.load_data()

    def load_data(self) -> None:
        """Load accounts and transactions from CSV files and rebuild lookup indexes."""
        self._accounts = self.storage.load_accounts(self.acc_file)
        self._rebuild_account_index()

        self._transactions = self.storage.load_transactions(self.tx_file)
        # Ensure transactions remain sorted chronologically
        self._transactions.sort()
        self._rebuild_transaction_index()

    def save_data(self) -> None:
        """Persist accounts and transactions atomically to disk."""
        self.storage.save_accounts(self._accounts, self.acc_file)
        self.storage.save_transactions(self._transactions, self.tx_file)

    def _rebuild_transaction_index(self) -> None:
        """Rebuild O(1) hash map index for transaction lookups."""
        self._tx_index = build_transaction_index(self._transactions)

    def _rebuild_account_index(self) -> None:
        """Rebuild O(1) hash map index for account lookups."""
        self._acc_index = build_account_index(self._accounts)

    # ==================== ACCOUNT OPERATIONS ====================

    def list_accounts(self) -> list[Account]:
        """List all registered accounts."""
        return list(self._accounts)

    def get_account(self, account_name: str) -> Account:
        """Get an account by name using O(1) hash map lookup.

        Raises:
            AccountNotFoundError: If account does not exist.
        """
        key = account_name.strip().lower()
        acc = self._acc_index.get(key)
        if not acc:
            raise AccountNotFoundError(account_name)
        return acc

    def add_account(
        self,
        account_name: str,
        opening_balance: Any = 0.0,
        account_type: str = "Standard",
        account_id: str | None = None,
        interest_rate: float = 4.0,
    ) -> Account:
        """Add a new account to the manager."""
        key = account_name.strip().lower()
        if key in self._acc_index:
            raise InvalidTransactionError(f"Account '{account_name}' already exists.")

        acc_id = account_id or f"ACC-{len(self._accounts) + 1:03d}"
        if account_type.lower() == "savings":
            acc = SavingsAccount(
                account_id=acc_id,
                account_name=account_name,
                opening_balance=opening_balance,
                interest_rate_percent=interest_rate,
            )
        elif account_type.lower() == "investment":
            acc = InvestmentAccount(
                account_id=acc_id,
                account_name=account_name,
                opening_balance=opening_balance,
            )
        else:
            acc = Account(
                account_id=acc_id,
                account_name=account_name,
                opening_balance=opening_balance,
                account_type=account_type,
            )

        self._accounts.append(acc)
        self._rebuild_account_index()
        self.storage.save_accounts(self._accounts, self.acc_file)
        return acc

    def calculate_total_liquidity(self) -> Decimal:
        """Calculate total cash balance across all liquid accounts."""
        return sum((acc.get_balance() for acc in self._accounts), Decimal("0.00"))

    def calculate_net_worth(self) -> Decimal:
        """Calculate aggregate net worth across all accounts (including portfolio values)."""
        return sum((acc.calculate_value() for acc in self._accounts), Decimal("0.00"))

    # ==================== TRANSACTION OPERATIONS ====================

    def list_transactions(self) -> list[Transaction]:
        """List all transactions sorted chronologically."""
        return list(self._transactions)

    def get_transaction_by_id(self, transaction_id: str) -> Transaction:
        """Retrieve a transaction by ID in average O(1) time using hash map."""
        tx = self._tx_index.get(transaction_id.strip())
        if not tx:
            raise TransactionNotFoundError(transaction_id)
        return tx

    def search_transactions(
        self,
        query: str = "",
        category: str = "",
        account_name: str = "",
        tx_type: str = "",
    ) -> list[Transaction]:
        """Search transactions with multi-criteria filtering."""
        q_lower = query.strip().lower()
        cat_lower = category.strip().lower()
        acc_lower = account_name.strip().lower()
        type_lower = tx_type.strip().lower()

        results = []
        for tx in self._transactions:
            if q_lower and (
                q_lower not in tx.description.lower() and q_lower not in tx.transaction_id.lower()
            ):
                continue
            if cat_lower and tx.category.lower() != cat_lower:
                continue
            if acc_lower and tx.account_name.lower() != acc_lower:
                continue
            if type_lower and tx.transaction_type.lower() != type_lower:
                continue
            results.append(tx)
        return results

    def filter_by_date_range(self, start_date: str, end_date: str) -> list[Transaction]:
        """Binary search range query to filter transactions between dates inclusive."""
        return filter_transactions_by_date_range(self._transactions, start_date, end_date)

    def _generate_transaction_id(self) -> str:
        """Generate next sequential unique transaction ID."""
        return f"TX-{len(self._transactions) + 1:05d}"

    def add_transaction(
        self,
        amount: Any,
        category: str,
        description: str,
        transaction_date: str,
        transaction_type: str,
        account_name: str,
        transaction_id: str | None = None,
        record_undo: bool = True,
    ) -> Transaction:
        """Create and apply a new transaction, updating account balance and undo history."""
        account = self.get_account(account_name)
        tx_id = transaction_id or self._generate_transaction_id()

        if tx_id in self._tx_index:
            raise InvalidTransactionError(f"Transaction ID '{tx_id}' already exists.")

        tx = Transaction(
            transaction_id=tx_id,
            amount=amount,
            category=category,
            description=description,
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            account_name=account.account_name,
        )

        # Apply transaction to account (will raise InsufficientFundsError on expense if funds lacking)
        account.apply_transaction(tx)

        # Insert into sorted list and rebuild index
        self._transactions.append(tx)
        self._transactions.sort()
        self._rebuild_transaction_index()

        # Push to UndoStack
        if record_undo:
            self.undo_stack.push(
                UndoAction(
                    action_type="ADD",
                    previous_transaction=None,
                    current_transaction=tx,
                    account_name=account.account_name,
                    description=f"Added {tx.transaction_type} {tx.transaction_id}",
                )
            )

        self.save_data()
        return tx

    def delete_transaction(
        self, transaction_id: str, record_undo: bool = True
    ) -> Transaction:
        """Delete an existing transaction and reverse its balance impact."""
        tx = self.get_transaction_by_id(transaction_id)
        account = self.get_account(tx.account_name)

        # Reverse impact on account
        account.reverse_transaction(tx)

        # Remove from transaction list
        self._transactions.remove(tx)
        self._rebuild_transaction_index()

        if record_undo:
            self.undo_stack.push(
                UndoAction(
                    action_type="DELETE",
                    previous_transaction=tx,
                    current_transaction=None,
                    account_name=account.account_name,
                    description=f"Deleted {tx.transaction_type} {tx.transaction_id}",
                )
            )

        self.save_data()
        return tx

    def edit_transaction(
        self,
        transaction_id: str,
        new_amount: Any | None = None,
        new_category: str | None = None,
        new_description: str | None = None,
        new_date: str | None = None,
        new_account_name: str | None = None,
        record_undo: bool = True,
    ) -> Transaction:
        """Edit fields of a transaction with balance reconciliation."""
        old_tx = self.get_transaction_by_id(transaction_id)
        old_account = self.get_account(old_tx.account_name)

        target_acc_name = new_account_name or old_tx.account_name
        new_account = self.get_account(target_acc_name)

        updated_amount = new_amount if new_amount is not None else old_tx.amount
        updated_cat = new_category if new_category is not None else old_tx.category
        updated_desc = (
            new_description if new_description is not None else old_tx.description
        )
        updated_date = new_date if new_date is not None else old_tx.transaction_date

        new_tx = Transaction(
            transaction_id=old_tx.transaction_id,
            amount=updated_amount,
            category=updated_cat,
            description=updated_desc,
            transaction_date=updated_date,
            transaction_type=old_tx.transaction_type,
            account_name=new_account.account_name,
        )

        # Step 1: Revert old transaction effect on old account
        old_account.reverse_transaction(old_tx)

        # Step 2: Apply new transaction effect on new account
        try:
            new_account.apply_transaction(new_tx)
        except Exception:
            # Rollback old account reverse if applying new fails
            old_account.apply_transaction(old_tx)
            raise

        # Update in list
        idx = self._transactions.index(old_tx)
        self._transactions[idx] = new_tx
        self._transactions.sort()
        self._rebuild_transaction_index()

        if record_undo:
            self.undo_stack.push(
                UndoAction(
                    action_type="EDIT",
                    previous_transaction=old_tx,
                    current_transaction=new_tx,
                    account_name=new_account.account_name,
                    description=f"Edited transaction {transaction_id}",
                )
            )

        self.save_data()
        return new_tx

    def undo_last_operation(self) -> str:
        """Revert the most recent ADD, DELETE, or EDIT transaction operation."""
        action = self.undo_stack.pop()
        if not action:
            return "No operations to undo."

        if action.action_type == "ADD":
            # Undoing an ADD means deleting the created transaction
            tx = action.current_transaction
            if not tx:
                return "Failed to undo: transaction reference missing."
            acc = self.get_account(tx.account_name)
            acc.reverse_transaction(tx)
            self._transactions.remove(tx)
            self._rebuild_transaction_index()
            self.save_data()
            return f"Undid ADD: Removed transaction {tx.transaction_id}."

        elif action.action_type == "DELETE":
            # Undoing a DELETE means re-inserting the removed transaction
            tx = action.previous_transaction
            if not tx:
                return "Failed to undo: transaction reference missing."
            acc = self.get_account(tx.account_name)
            acc.apply_transaction(tx)
            self._transactions.append(tx)
            self._transactions.sort()
            self._rebuild_transaction_index()
            self.save_data()
            return f"Undid DELETE: Restored transaction {tx.transaction_id}."

        elif action.action_type == "EDIT":
            # Undoing an EDIT means restoring previous_transaction
            old_tx = action.previous_transaction
            curr_tx = action.current_transaction
            if not old_tx or not curr_tx:
                return "Failed to undo: transaction reference missing."

            curr_acc = self.get_account(curr_tx.account_name)
            old_acc = self.get_account(old_tx.account_name)

            curr_acc.reverse_transaction(curr_tx)
            old_acc.apply_transaction(old_tx)

            idx = self._transactions.index(curr_tx)
            self._transactions[idx] = old_tx
            self._transactions.sort()
            self._rebuild_transaction_index()
            self.save_data()
            return f"Undid EDIT: Restored original state of transaction {old_tx.transaction_id}."

        return f"Unknown undo action type: {action.action_type}"

    # ==================== SUMMARY & DSA WRAPPERS ====================

    def get_total_income(self) -> Decimal:
        """Calculate total income across all transactions."""
        return sum(
            (tx.amount for tx in self._transactions if tx.is_income),
            Decimal("0.00"),
        )

    def get_total_expenses(self) -> Decimal:
        """Calculate total expenses across all transactions."""
        return sum(
            (tx.amount for tx in self._transactions if tx.is_expense),
            Decimal("0.00"),
        )

    def get_net_savings(self) -> Decimal:
        """Calculate total income minus total expenses."""
        return self.get_total_income() - self.get_total_expenses()

    def get_top_n_expenses(self, limit: int = 5) -> list[Transaction]:
        """Retrieve top N expenses using O(N log K) min-heap."""
        return get_top_expenses(self._transactions, limit=limit)
