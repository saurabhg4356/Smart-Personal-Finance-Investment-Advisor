"""Services package for Smart Personal Finance & Investment Advisor."""

from services.analytics import FinancialAnalytics
from services.budget_manager import BudgetManager
from services.categorizer import TransactionCategorizer
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
from services.finance_manager import FinanceManager
from services.investment_manager import InvestmentManager
from services.predictor import SpendingPredictor
from services.storage import StorageService
from services.visualizer import FinancialVisualizer

__all__ = [
    "BudgetManager",
    "FinancialAnalytics",
    "FinancialVisualizer",
    "FinanceManager",
    "InvestmentManager",
    "SpendingPredictor",
    "StorageService",
    "TransactionCategorizer",
    "UndoAction",
    "UndoStack",
    "aggregate_expenses_by_category",
    "build_account_index",
    "build_budget_index",
    "build_transaction_index",
    "filter_transactions_by_date_range",
    "get_top_expenses",
]
