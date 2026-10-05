"""Unit tests for FinancialVisualizer charts generation."""

from pathlib import Path
import pytest

from models.investment import Investment
from models.transaction import Transaction
from services.visualizer import FinancialVisualizer


@pytest.fixture
def visualizer(tmp_path):
    charts_dir = tmp_path / "charts"
    return FinancialVisualizer(charts_dir=charts_dir)


@pytest.fixture
def mock_transactions():
    return [
        Transaction("TX-1", 50000.0, "Salary", "Paycheck", "2025-10-01", "income", "HDFC"),
        Transaction("TX-2", 15000.0, "Housing", "Rent", "2025-10-03", "expense", "HDFC"),
        Transaction("TX-3", 5000.0, "Food", "Groceries", "2025-10-15", "expense", "HDFC"),
        Transaction("TX-4", 50000.0, "Salary", "Paycheck", "2025-11-01", "income", "HDFC"),
        Transaction("TX-5", 15000.0, "Housing", "Rent", "2025-11-03", "expense", "HDFC"),
        Transaction("TX-6", 6000.0, "Food", "Groceries", "2025-11-15", "expense", "HDFC"),
        Transaction("TX-7", 50000.0, "Salary", "Paycheck", "2025-12-01", "income", "HDFC"),
        Transaction("TX-8", 15000.0, "Housing", "Rent", "2025-12-03", "expense", "HDFC"),
        Transaction("TX-9", 7000.0, "Food", "Groceries", "2025-12-15", "expense", "HDFC"),
    ]


@pytest.fixture
def mock_investments():
    return [
        Investment("INV-1", "Nifty Index", "Mutual Fund", 50.0, 100.0, 120.0),
        Investment("INV-2", "Gold ETF", "Gold", 10.0, 50.0, 60.0),
    ]


def test_visualizer_empty_data(visualizer):
    assert visualizer.plot_expense_distribution([]) is None
    assert visualizer.plot_income_vs_expenses([]) is None
    assert visualizer.plot_spending_trend([]) is None
    assert visualizer.plot_actual_vs_predicted([]) is None
    assert visualizer.plot_portfolio_allocation([]) is None


def test_visualizer_full_charts_generation(visualizer, mock_transactions, mock_investments):
    chart_paths = visualizer.generate_all_charts(mock_transactions, mock_investments)

    assert chart_paths["expense_distribution"] is not None
    assert chart_paths["expense_distribution"].exists()

    assert chart_paths["income_vs_expenses"] is not None
    assert chart_paths["income_vs_expenses"].exists()

    assert chart_paths["spending_trend"] is not None
    assert chart_paths["spending_trend"].exists()

    assert chart_paths["actual_vs_predicted"] is not None
    assert chart_paths["actual_vs_predicted"].exists()

    assert chart_paths["portfolio_allocation"] is not None
    assert chart_paths["portfolio_allocation"].exists()
