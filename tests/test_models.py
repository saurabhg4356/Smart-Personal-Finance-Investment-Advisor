"""Unit tests for domain models (Transaction, Account, Budget, Investment)."""

from decimal import Decimal
import pytest

from models.account import Account, InvestmentAccount, SavingsAccount
from models.budget import Budget
from models.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    InvalidTransactionError,
    InvestmentValidationError,
)
from models.investment import Investment
from models.transaction import Transaction


# ==================== TRANSACTION TESTS ====================


def test_valid_transaction_creation():
    tx = Transaction(
        transaction_id="TX-001",
        amount=1500.50,
        category="Groceries",
        description="Supermarket groceries",
        transaction_date="2026-03-15",
        transaction_type="expense",
        account_name="HDFC Salary",
    )
    assert tx.transaction_id == "TX-001"
    assert tx.amount == Decimal("1500.50")
    assert tx.amount_float == 1500.50
    assert tx.category == "Groceries"
    assert tx.is_expense is True
    assert tx.is_income is False
    assert "TX-001" in str(tx)
    assert "Transaction(id='TX-001'" in repr(tx)


def test_transaction_invalid_amounts():
    with pytest.raises(InvalidAmountError):
        Transaction("TX-1", -50.0, "Food", "Dinner", "2026-03-01", "expense", "HDFC")
    with pytest.raises(InvalidAmountError):
        Transaction("TX-1", 0, "Food", "Dinner", "2026-03-01", "expense", "HDFC")
    with pytest.raises(InvalidAmountError):
        Transaction("TX-1", "abc", "Food", "Dinner", "2026-03-01", "expense", "HDFC")
    with pytest.raises(InvalidAmountError):
        Transaction("TX-1", float("nan"), "Food", "Dinner", "2026-03-01", "expense", "HDFC")


def test_transaction_invalid_dates():
    with pytest.raises(InvalidTransactionError):
        Transaction("TX-1", 100, "Food", "Dinner", "invalid-date", "expense", "HDFC")
    with pytest.raises(InvalidTransactionError):
        Transaction("TX-1", 100, "Food", "Dinner", "2026-02-30", "expense", "HDFC")


def test_transaction_invalid_type():
    with pytest.raises(InvalidTransactionError):
        Transaction("TX-1", 100, "Food", "Dinner", "2026-03-01", "transfer", "HDFC")


def test_transaction_serialization_roundtrip():
    tx = Transaction(
        transaction_id="TX-100",
        amount="4500.75",
        category="shopping",
        description="Shoes purchase",
        transaction_date="2026-02-20",
        transaction_type="expense",
        account_name="SBI",
    )
    data = tx.to_dict()
    restored = Transaction.from_dict(data)
    assert restored.transaction_id == tx.transaction_id
    assert restored.amount == tx.amount
    assert restored.category == "Shopping"
    assert restored.description == tx.description
    assert restored.transaction_date == tx.transaction_date
    assert restored.account_name == tx.account_name


def test_transaction_comparison():
    tx1 = Transaction("TX-1", 100, "Food", "Lunch", "2026-01-05", "expense", "Bank")
    tx2 = Transaction("TX-2", 200, "Food", "Dinner", "2026-01-06", "expense", "Bank")
    assert tx1 < tx2


# ==================== ACCOUNT TESTS ====================


def test_base_account_deposit_and_withdraw():
    acc = Account(
        account_id="ACC-01",
        account_name="Main Checking",
        opening_balance=5000.0,
    )
    assert acc.current_balance == Decimal("5000.00")
    assert acc.get_balance() == Decimal("5000.00")

    acc.deposit(2500.0)
    assert acc.current_balance == Decimal("7500.00")

    acc.withdraw(1500.0)
    assert acc.current_balance == Decimal("6000.00")


def test_account_withdraw_insufficient_funds():
    acc = Account("ACC-01", "Checking", 1000.0)
    with pytest.raises(InsufficientFundsError) as exc_info:
        acc.withdraw(2000.0)
    assert exc_info.value.current_balance == 1000.0
    assert exc_info.value.requested_amount == 2000.0


def test_account_apply_and_reverse_transaction():
    acc = Account("ACC-01", "HDFC", 10000.0)

    # Apply Expense
    exp_tx = Transaction("TX-1", 2000.0, "Food", "Dinner", "2026-01-01", "expense", "HDFC")
    acc.apply_transaction(exp_tx)
    assert acc.current_balance == Decimal("8000.00")

    # Reverse Expense
    acc.reverse_transaction(exp_tx)
    assert acc.current_balance == Decimal("10000.00")

    # Apply Income
    inc_tx = Transaction("TX-2", 5000.0, "Salary", "Bonus", "2026-01-02", "income", "HDFC")
    acc.apply_transaction(inc_tx)
    assert acc.current_balance == Decimal("15000.00")

    # Reverse Income
    acc.reverse_transaction(inc_tx)
    assert acc.current_balance == Decimal("10000.00")


def test_savings_account_interest():
    sav = SavingsAccount(
        account_id="ACC-SAV",
        account_name="Emergency Savings",
        opening_balance=100000.0,
        interest_rate_percent=6.0,
    )
    # Interest for 12 months = 100000 * 6 * 1 / 100 = 6000
    assert sav.calculate_interest(12) == Decimal("6000.00")
    # Interest for 1 month = 6000 / 12 = 500
    assert sav.calculate_interest(1) == Decimal("500.00")

    summary = sav.generate_summary()
    assert summary["interest_rate_percent"] == 6.0
    assert summary["projected_annual_interest"] == 6000.0


def test_investment_account_polymorphism():
    inv_acc = InvestmentAccount(
        account_id="ACC-INV",
        account_name="Trading Wallet",
        opening_balance=25000.0,
    )
    assert inv_acc.calculate_value() == Decimal("25000.00")

    inv_acc.set_holdings_value(75000.0)
    # Polymorphic calculate_value() combines cash + simulated holdings
    assert inv_acc.calculate_value() == Decimal("100000.00")

    summary = inv_acc.generate_summary()
    assert summary["cash_balance"] == 25000.0
    assert summary["holdings_value"] == 75000.0
    assert summary["total_portfolio_value"] == 100000.0


# ==================== BUDGET TESTS ====================


def test_budget_calculations():
    b = Budget(
        budget_id="B-001",
        category="Groceries",
        monthly_limit=15000.0,
        month=3,
        year=2026,
    )
    assert b.calculate_remaining(10000.0) == Decimal("5000.00")
    assert b.calculate_percentage_utilized(7500.0) == 50.0
    assert b.is_exceeded(14999.0) is False
    assert b.is_exceeded(16000.0) is True

    rep = b.generate_status_report(16500.0)
    assert rep["is_exceeded"] is True
    assert rep["status_text"] == "EXCEEDED"
    assert rep["remaining"] == -1500.0


def test_budget_invalid_month_year():
    with pytest.raises(InvalidTransactionError):
        Budget("B-01", "Food", 5000, month=13, year=2026)
    with pytest.raises(InvalidTransactionError):
        Budget("B-01", "Food", 5000, month=5, year=1990)


# ==================== INVESTMENT TESTS ====================


def test_investment_calculations():
    inv = Investment(
        investment_id="INV-01",
        asset_name="Tata Consultancy Services",
        asset_type="Equity",
        quantity=10.0,
        purchase_price=3000.0,
        current_price=3600.0,
    )
    assert inv.invested_amount == 30000.0
    assert inv.current_estimated_value == 36000.0
    assert inv.profit_loss == 6000.0
    assert inv.percentage_return == 20.0

    # Add more shares at different price (weighted average calculation)
    # 10 @ 3000 (cost 30000) + 10 @ 4000 (cost 40000) -> total 20 @ 3500 (cost 70000)
    inv.add_shares(10.0, 4000.0)
    assert inv.quantity == 20.0
    assert inv.purchase_price == 3500.0

    # Remove shares
    inv.remove_shares(5.0)
    assert inv.quantity == 15.0

    # Update price
    inv.update_current_price(4200.0)
    assert inv.current_price == 4200.0
    assert inv.current_estimated_value == 15.0 * 4200.0


def test_investment_validation():
    with pytest.raises(InvestmentValidationError):
        Investment("INV-1", "Gold", "Metal", -5, 100, 110)
    with pytest.raises(InvestmentValidationError):
        Investment("INV-1", "Gold", "Metal", 5, -100, 110)
