"""Unit tests for FinanceManager service, transactions, accounts, and undo behavior."""

from decimal import Decimal
import pytest

from models.account import Account
from models.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
    TransactionNotFoundError,
)
from services.finance_manager import FinanceManager
from services.storage import StorageService


@pytest.fixture
def finance_manager(tmp_path):
    storage = StorageService(base_data_dir=tmp_path)
    tx_file = tmp_path / "transactions.csv"
    acc_file = tmp_path / "accounts.csv"

    # Seed initial account
    initial_acc = Account("ACC-01", "HDFC Salary", 20000.0)
    storage.save_accounts([initial_acc], acc_file)

    return FinanceManager(
        storage_service=storage,
        transactions_file=tx_file,
        accounts_file=acc_file,
    )


def test_add_income_and_expense(finance_manager):
    # Initial balance is 20000
    tx1 = finance_manager.add_transaction(
        amount=10000.0,
        category="Salary",
        description="Bonus",
        transaction_date="2026-03-01",
        transaction_type="income",
        account_name="HDFC Salary",
    )
    acc = finance_manager.get_account("HDFC Salary")
    assert acc.current_balance == Decimal("30000.00")

    tx2 = finance_manager.add_transaction(
        amount=5000.0,
        category="Shopping",
        description="Smartphone",
        transaction_date="2026-03-02",
        transaction_type="expense",
        account_name="HDFC Salary",
    )
    acc = finance_manager.get_account("HDFC Salary")
    assert acc.current_balance == Decimal("25000.00")
    assert len(finance_manager.list_transactions()) == 2


def test_add_expense_insufficient_funds(finance_manager):
    # Account has 20000; attempting to spend 50000 should raise InsufficientFundsError
    with pytest.raises(InsufficientFundsError):
        finance_manager.add_transaction(
            amount=50000.0,
            category="Luxury",
            description="Diamond ring",
            transaction_date="2026-03-01",
            transaction_type="expense",
            account_name="HDFC Salary",
        )
    # Balance must remain intact
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("20000.00")


def test_undo_add_transaction(finance_manager):
    finance_manager.add_transaction(
        amount=3000.0,
        category="Food",
        description="Party dinner",
        transaction_date="2026-03-05",
        transaction_type="expense",
        account_name="HDFC Salary",
    )
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("17000.00")

    result = finance_manager.undo_last_operation()
    assert "Undid ADD" in result
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("20000.00")
    assert len(finance_manager.list_transactions()) == 0


def test_delete_transaction_and_undo(finance_manager):
    tx = finance_manager.add_transaction(
        amount=4000.0,
        category="Utilities",
        description="Electric bill",
        transaction_date="2026-03-01",
        transaction_type="expense",
        account_name="HDFC Salary",
    )
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("16000.00")

    # Delete transaction
    finance_manager.delete_transaction(tx.transaction_id)
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("20000.00")
    assert len(finance_manager.list_transactions()) == 0

    # Undo delete restores transaction and deducts expense again
    undo_res = finance_manager.undo_last_operation()
    assert "Undid DELETE" in undo_res
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("16000.00")
    assert len(finance_manager.list_transactions()) == 1


def test_edit_transaction_and_undo(finance_manager):
    tx = finance_manager.add_transaction(
        amount=2000.0,
        category="Groceries",
        description="Market",
        transaction_date="2026-03-01",
        transaction_type="expense",
        account_name="HDFC Salary",
    )
    # Balance: 20000 - 2000 = 18000
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("18000.00")

    # Edit amount to 3500
    updated = finance_manager.edit_transaction(tx.transaction_id, new_amount=3500.0)
    assert updated.amount == Decimal("3500.00")
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("16500.00")

    # Undo edit
    finance_manager.undo_last_operation()
    assert finance_manager.get_account("HDFC Salary").current_balance == Decimal("18000.00")
    restored = finance_manager.get_transaction_by_id(tx.transaction_id)
    assert restored.amount == Decimal("2000.00")


def test_search_and_top_expenses(finance_manager):
    finance_manager.add_transaction(1000.0, "Food", "Biryani lunch", "2026-02-01", "expense", "HDFC Salary")
    finance_manager.add_transaction(8000.0, "Travel", "Flight ticket", "2026-02-05", "expense", "HDFC Salary")
    finance_manager.add_transaction(3000.0, "Food", "Family dinner", "2026-02-10", "expense", "HDFC Salary")

    results = finance_manager.search_transactions(query="dinner")
    assert len(results) == 1
    assert results[0].amount == Decimal("3000.00")

    top2 = finance_manager.get_top_n_expenses(limit=2)
    assert len(top2) == 2
    assert top2[0].amount == Decimal("8000.00")
    assert top2[1].amount == Decimal("3000.00")


def test_account_and_transaction_not_found(finance_manager):
    with pytest.raises(TransactionNotFoundError):
        finance_manager.get_transaction_by_id("TX-UNKNOWN")

    with pytest.raises(AccountNotFoundError):
        finance_manager.get_account("NonExistentBank")
