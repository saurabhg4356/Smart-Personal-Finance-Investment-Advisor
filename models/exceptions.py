"""Custom exception hierarchy for Smart Personal Finance & Investment Advisor."""


class FinanceAdvisorError(Exception):
    """Base exception for all financial advisor application errors."""

    def __init__(self, message: str, resolution_hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.resolution_hint = resolution_hint

    def __str__(self) -> str:
        if self.resolution_hint:
            return f"{self.message} (Tip: {self.resolution_hint})"
        return self.message


class InvalidAmountError(FinanceAdvisorError):
    """Raised when a monetary amount is invalid (e.g., negative, zero, non-numeric, or NaN/infinite)."""

    def __init__(
        self,
        message: str = "Invalid amount provided.",
        resolution_hint: str = "Enter a positive numeric amount greater than zero.",
    ) -> None:
        super().__init__(message, resolution_hint)


class InvalidTransactionError(FinanceAdvisorError):
    """Raised when a transaction payload has invalid fields or parameters."""

    def __init__(
        self,
        message: str = "Invalid transaction parameters.",
        resolution_hint: str = "Ensure valid date (YYYY-MM-DD), type ('income' or 'expense'), category, and account.",
    ) -> None:
        super().__init__(message, resolution_hint)


class InsufficientFundsError(FinanceAdvisorError):
    """Raised when a withdrawal or expense exceeds available account funds."""

    def __init__(
        self,
        account_name: str,
        current_balance: float,
        requested_amount: float,
        resolution_hint: str = "Deposit additional funds or choose an account with a sufficient balance.",
    ) -> None:
        message = (
            f"Insufficient funds in account '{account_name}'. "
            f"Available: ₹{current_balance:,.2f}, Requested: ₹{requested_amount:,.2f}."
        )
        super().__init__(message, resolution_hint)
        self.account_name = account_name
        self.current_balance = current_balance
        self.requested_amount = requested_amount


class TransactionNotFoundError(FinanceAdvisorError):
    """Raised when a requested transaction ID does not exist."""

    def __init__(
        self,
        transaction_id: str,
        resolution_hint: str = "Verify the transaction ID using 'View Transactions' or search.",
    ) -> None:
        super().__init__(f"Transaction '{transaction_id}' was not found.", resolution_hint)
        self.transaction_id = transaction_id


class AccountNotFoundError(FinanceAdvisorError):
    """Raised when a specified account name or ID cannot be found."""

    def __init__(
        self,
        account_name: str,
        resolution_hint: str = "Check active account names under 'View Accounts' or create the account first.",
    ) -> None:
        super().__init__(f"Account '{account_name}' was not found.", resolution_hint)
        self.account_name = account_name


class BudgetExceededError(FinanceAdvisorError):
    """Raised when an expense causes a budget limit to be exceeded (when strict mode is enabled)."""

    def __init__(
        self,
        category: str,
        current_spent: float,
        monthly_limit: float,
        resolution_hint: str = "Adjust budget limit under 'Manage Budgets' or categorize under another valid bucket.",
    ) -> None:
        message = (
            f"Budget exceeded for category '{category}'! "
            f"Current spent: ₹{current_spent:,.2f}, Limit: ₹{monthly_limit:,.2f}."
        )
        super().__init__(message, resolution_hint)
        self.category = category
        self.current_spent = current_spent
        self.monthly_limit = monthly_limit


class InvestmentValidationError(FinanceAdvisorError):
    """Raised when investment asset name, quantity, purchase price, or current price are invalid."""

    def __init__(
        self,
        message: str = "Invalid investment holding values.",
        resolution_hint: str = "Quantity must be > 0 and prices must be non-negative numbers.",
    ) -> None:
        super().__init__(message, resolution_hint)


class StorageError(FinanceAdvisorError):
    """Raised when reading or writing persistent CSV files encounters errors."""

    def __init__(
        self,
        message: str,
        resolution_hint: str = "Ensure data files exist, have proper read/write permissions, and contain correct headers.",
    ) -> None:
        super().__init__(message, resolution_hint)


class NotEnoughDataError(FinanceAdvisorError):
    """Raised when there is insufficient historical data for analytics or machine learning predictions."""

    def __init__(
        self,
        required_records: int,
        actual_records: int,
        context: str = "operation",
        resolution_hint: str = "Record more monthly transactions or load demo sample data to enable this model.",
    ) -> None:
        message = (
            f"Insufficient historical data for {context}. "
            f"Required at least {required_records} records/months, but only found {actual_records}."
        )
        super().__init__(message, resolution_hint)
        self.required_records = required_records
        self.actual_records = actual_records
