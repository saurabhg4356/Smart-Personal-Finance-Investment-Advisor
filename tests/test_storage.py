"""Unit tests for StorageService CSV round-tripping, schema validation, and edge cases."""

from decimal import Decimal
from pathlib import Path
import pytest

from models.account import Account, SavingsAccount
from models.budget import Budget
from models.exceptions import StorageError
from models.investment import Investment
from models.transaction import Transaction
from services.storage import StorageService


@pytest.fixture
def storage(tmp_path):
    return StorageService(base_data_dir=tmp_path)


def test_transactions_round_trip(storage, tmp_path):
    file_path = tmp_path / "test_txs.csv"
    txs = [
        Transaction("TX-1", 1500.0, "Food", "Dinner", "2026-03-01", "expense", "HDFC"),
        Transaction("TX-2", 50000.0, "Salary", "Paycheck", "2026-03-01", "income", "HDFC"),
    ]
    storage.save_transactions(txs, file_path)
    assert file_path.exists()

    loaded = storage.load_transactions(file_path)
    assert len(loaded) == 2
    assert loaded[0].transaction_id == "TX-1"
    assert loaded[0].amount == Decimal("1500.00")
    assert loaded[1].transaction_type == "income"


def test_missing_and_empty_file_handling(storage, tmp_path):
    missing_file = tmp_path / "non_existent.csv"
    assert storage.load_transactions(missing_file) == []

    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    assert storage.load_transactions(empty_file) == []


def test_malformed_csv_headers(storage, tmp_path):
    bad_file = tmp_path / "bad_headers.csv"
    bad_file.write_text("wrong_col1,wrong_col2\n1,2\n", encoding="utf-8")
    with pytest.raises(StorageError) as exc_info:
        storage.load_transactions(bad_file)
    assert "missing required columns" in str(exc_info.value).lower()


def test_malformed_transaction_row(storage, tmp_path):
    bad_row_file = tmp_path / "bad_row.csv"
    # Negative amount in CSV row
    content = (
        "transaction_id,amount,category,description,transaction_date,transaction_type,account_name\n"
        "TX-1,-500,Food,Lunch,2026-01-01,expense,HDFC\n"
    )
    bad_row_file.write_text(content, encoding="utf-8")
    with pytest.raises(StorageError) as exc_info:
        storage.load_transactions(bad_row_file)
    assert "Malformed transaction" in str(exc_info.value)


def test_accounts_round_trip(storage, tmp_path):
    file_path = tmp_path / "test_accounts.csv"
    accs = [
        Account("ACC-1", "Standard Bank", 10000.0),
        SavingsAccount("ACC-2", "High Yield Savings", 20000.0, interest_rate_percent=5.5),
    ]
    storage.save_accounts(accs, file_path)
    loaded = storage.load_accounts(file_path)
    assert len(loaded) == 2
    assert isinstance(loaded[1], SavingsAccount)
    assert loaded[1].interest_rate_percent == 5.5


def test_budgets_round_trip(storage, tmp_path):
    file_path = tmp_path / "test_budgets.csv"
    budgets = [Budget("B-1", "Food", 10000.0, 3, 2026)]
    storage.save_budgets(budgets, file_path)
    loaded = storage.load_budgets(file_path)
    assert len(loaded) == 1
    assert loaded[0].monthly_limit == Decimal("10000.00")


def test_investments_round_trip(storage, tmp_path):
    file_path = tmp_path / "test_investments.csv"
    invs = [Investment("INV-1", "Nifty ETF", "Index", 10.0, 200.0, 220.0)]
    storage.save_investments(invs, file_path)
    loaded = storage.load_investments(file_path)
    assert len(loaded) == 1
    assert loaded[0].quantity == 10.0
    assert loaded[0].purchase_price == 200.0
