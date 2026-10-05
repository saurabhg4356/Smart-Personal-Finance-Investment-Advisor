"""CSV data persistence service with atomic writes and schema validation."""

from __future__ import annotations

import csv
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

from models.account import Account
from models.budget import Budget
from models.exceptions import StorageError
from models.investment import Investment
from models.transaction import Transaction

TRANSACTION_HEADERS = [
    "transaction_id",
    "amount",
    "category",
    "description",
    "transaction_date",
    "transaction_type",
    "account_name",
]

ACCOUNT_HEADERS = [
    "account_id",
    "account_name",
    "opening_balance",
    "current_balance",
    "account_type",
    "extra_info",
]

BUDGET_HEADERS = [
    "budget_id",
    "category",
    "monthly_limit",
    "month",
    "year",
]

INVESTMENT_HEADERS = [
    "investment_id",
    "asset_name",
    "asset_type",
    "quantity",
    "purchase_price",
    "current_price",
]


class StorageService:
    """Manages CSV persistence for all financial entities using atomic file replacement."""

    def __init__(self, base_data_dir: Path | str = "data") -> None:
        self.base_dir = Path(base_data_dir)
        self.ensure_directory(self.base_dir)

    @staticmethod
    def ensure_directory(path: Path | str) -> None:
        """Create directory and parents if not already present."""
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_headers(
        actual_headers: list[str] | None, expected_headers: list[str], file_path: Path
    ) -> None:
        if not actual_headers:
            raise StorageError(
                f"CSV file '{file_path.name}' is empty or missing headers.",
                f"Expected columns: {', '.join(expected_headers)}",
            )
        # Strip whitespace and lowercase compare
        cleaned_actual = [h.strip() for h in actual_headers]
        missing = [h for h in expected_headers if h not in cleaned_actual]
        if missing:
            raise StorageError(
                f"File '{file_path.name}' is missing required columns: {', '.join(missing)}.",
                f"File must include headers: {', '.join(expected_headers)}",
            )

    @staticmethod
    def _atomic_write_csv(
        file_path: Path, headers: list[str], rows: Iterable[dict[str, Any]]
    ) -> None:
        """Safely write CSV using a temporary file in the same directory followed by atomic rename."""
        file_path = Path(file_path)
        StorageService.ensure_directory(file_path.parent)

        temp_file = None
        try:
            # Create temp file in same directory to ensure same filesystem for atomic replace
            fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent, prefix=f".{file_path.stem}_", suffix=".tmp"
            )
            temp_file = Path(temp_path)
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

            # Atomic replace
            temp_file.replace(file_path)
        except Exception as exc:
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise StorageError(
                f"Failed to atomically save file '{file_path}': {exc}",
                "Check disk space and write permissions.",
            ) from exc

    # ==================== TRANSACTIONS ====================

    def load_transactions(self, file_path: Path | str) -> list[Transaction]:
        """Load and validate transactions from CSV."""
        path = Path(file_path)
        if not path.exists():
            return []

        transactions: list[Transaction] = []
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    return []
                self._validate_headers(reader.fieldnames, TRANSACTION_HEADERS, path)

                for row_idx, row in enumerate(reader, start=2):
                    try:
                        tx = Transaction.from_dict(row)
                        transactions.append(tx)
                    except Exception as exc:
                        raise StorageError(
                            f"Malformed transaction at line {row_idx} in '{path.name}': {exc}",
                            "Ensure all fields (amount, date, type, account) are valid.",
                        ) from exc
        except OSError as exc:
            raise StorageError(f"Could not read transaction file '{path}': {exc}") from exc

        return transactions

    def save_transactions(
        self, transactions: list[Transaction], file_path: Path | str
    ) -> None:
        """Save list of transactions to CSV atomically."""
        rows = [tx.to_dict() for tx in transactions]
        self._atomic_write_csv(Path(file_path), TRANSACTION_HEADERS, rows)

    # ==================== ACCOUNTS ====================

    def load_accounts(self, file_path: Path | str) -> list[Account]:
        """Load and validate accounts from CSV."""
        path = Path(file_path)
        if not path.exists():
            return []

        accounts: list[Account] = []
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    return []
                self._validate_headers(reader.fieldnames, ACCOUNT_HEADERS, path)

                for row_idx, row in enumerate(reader, start=2):
                    try:
                        acc = Account.from_dict(row)
                        accounts.append(acc)
                    except Exception as exc:
                        raise StorageError(
                            f"Malformed account at line {row_idx} in '{path.name}': {exc}",
                            "Verify account numbers, opening balances, and account types.",
                        ) from exc
        except OSError as exc:
            raise StorageError(f"Could not read account file '{path}': {exc}") from exc

        return accounts

    def save_accounts(self, accounts: list[Account], file_path: Path | str) -> None:
        """Save accounts to CSV atomically."""
        rows = [acc.to_dict() for acc in accounts]
        self._atomic_write_csv(Path(file_path), ACCOUNT_HEADERS, rows)

    # ==================== BUDGETS ====================

    def load_budgets(self, file_path: Path | str) -> list[Budget]:
        """Load and validate budgets from CSV."""
        path = Path(file_path)
        if not path.exists():
            return []

        budgets: list[Budget] = []
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    return []
                self._validate_headers(reader.fieldnames, BUDGET_HEADERS, path)

                for row_idx, row in enumerate(reader, start=2):
                    try:
                        b = Budget.from_dict(row)
                        budgets.append(b)
                    except Exception as exc:
                        raise StorageError(
                            f"Malformed budget at line {row_idx} in '{path.name}': {exc}",
                            "Check limit amounts, month (1-12), and year.",
                        ) from exc
        except OSError as exc:
            raise StorageError(f"Could not read budget file '{path}': {exc}") from exc

        return budgets

    def save_budgets(self, budgets: list[Budget], file_path: Path | str) -> None:
        """Save budgets to CSV atomically."""
        rows = [b.to_dict() for b in budgets]
        self._atomic_write_csv(Path(file_path), BUDGET_HEADERS, rows)

    # ==================== INVESTMENTS ====================

    def load_investments(self, file_path: Path | str) -> list[Investment]:
        """Load and validate simulated investment holdings from CSV."""
        path = Path(file_path)
        if not path.exists():
            return []

        investments: list[Investment] = []
        try:
            with open(path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames is None:
                    return []
                self._validate_headers(reader.fieldnames, INVESTMENT_HEADERS, path)

                for row_idx, row in enumerate(reader, start=2):
                    try:
                        inv = Investment.from_dict(row)
                        investments.append(inv)
                    except Exception as exc:
                        raise StorageError(
                            f"Malformed investment at line {row_idx} in '{path.name}': {exc}",
                            "Check quantities and price numbers.",
                        ) from exc
        except OSError as exc:
            raise StorageError(f"Could not read investment file '{path}': {exc}") from exc

        return investments

    def save_investments(self, investments: list[Investment], file_path: Path | str) -> None:
        """Save investments to CSV atomically."""
        rows = [inv.to_dict() for inv in investments]
        self._atomic_write_csv(Path(file_path), INVESTMENT_HEADERS, rows)
