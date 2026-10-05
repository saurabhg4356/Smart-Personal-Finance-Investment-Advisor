"""Unit tests for the custom exception hierarchy."""

import pytest

from models.exceptions import (
    AccountNotFoundError,
    BudgetExceededError,
    FinanceAdvisorError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidTransactionError,
    InvestmentValidationError,
    NotEnoughDataError,
    StorageError,
    TransactionNotFoundError,
)


def test_base_finance_advisor_error():
    err = FinanceAdvisorError("Base error", resolution_hint="Try again")
    assert "Base error" in str(err)
    assert "Try again" in str(err)
    assert isinstance(err, Exception)


def test_invalid_amount_error():
    err = InvalidAmountError("Amount must be positive.")
    assert isinstance(err, FinanceAdvisorError)
    assert "Amount must be positive." in str(err)


def test_invalid_transaction_error():
    err = InvalidTransactionError("Invalid date format.")
    assert isinstance(err, FinanceAdvisorError)
    assert "Invalid date format." in str(err)


def test_insufficient_funds_error():
    err = InsufficientFundsError(
        account_name="HDFC", current_balance=100.0, requested_amount=500.0
    )
    assert isinstance(err, FinanceAdvisorError)
    assert "HDFC" in str(err)
    assert err.current_balance == 100.0
    assert err.requested_amount == 500.0


def test_transaction_not_found_error():
    err = TransactionNotFoundError("TX-999")
    assert isinstance(err, FinanceAdvisorError)
    assert "TX-999" in str(err)
    assert err.transaction_id == "TX-999"


def test_account_not_found_error():
    err = AccountNotFoundError("MyBank")
    assert isinstance(err, FinanceAdvisorError)
    assert "MyBank" in str(err)
    assert err.account_name == "MyBank"


def test_budget_exceeded_error():
    err = BudgetExceededError("Food", current_spent=12000.0, monthly_limit=10000.0)
    assert isinstance(err, FinanceAdvisorError)
    assert "Food" in str(err)
    assert err.current_spent == 12000.0
    assert err.monthly_limit == 10000.0


def test_investment_validation_error():
    err = InvestmentValidationError("Quantity cannot be negative.")
    assert isinstance(err, FinanceAdvisorError)
    assert "Quantity cannot be negative." in str(err)


def test_storage_error():
    err = StorageError("File corrupted.")
    assert isinstance(err, FinanceAdvisorError)
    assert "File corrupted." in str(err)


def test_not_enough_data_error():
    err = NotEnoughDataError(required_records=5, actual_records=2, context="testing")
    assert isinstance(err, FinanceAdvisorError)
    assert err.required_records == 5
    assert err.actual_records == 2
    assert "testing" in str(err)
