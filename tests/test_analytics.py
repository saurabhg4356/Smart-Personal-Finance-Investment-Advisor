"""Unit tests for FinancialAnalytics using pandas and NumPy."""

import pytest

from models.transaction import Transaction
from services.analytics import FinancialAnalytics


@pytest.fixture
def test_transactions():
    return [
        Transaction("TX-1", 100000.0, "Salary", "Paycheck", "2026-01-01", "income", "HDFC"),
        Transaction("TX-2", 25000.0, "Housing", "Rent", "2026-01-02", "expense", "HDFC"),
        Transaction("TX-3", 5000.0, "Food", "Groceries", "2026-01-10", "expense", "HDFC"),
        Transaction("TX-4", 6000.0, "Food", "Dining", "2026-01-15", "expense", "HDFC"),
        Transaction("TX-5", 100000.0, "Salary", "Paycheck", "2026-02-01", "income", "HDFC"),
        Transaction("TX-6", 25000.0, "Housing", "Rent", "2026-02-02", "expense", "HDFC"),
        Transaction("TX-7", 5500.0, "Food", "Groceries", "2026-02-12", "expense", "HDFC"),
        Transaction("TX-8", 45000.0, "Food", "Luxury Banquet", "2026-02-20", "expense", "HDFC"),  # Anomaly
    ]


def test_empty_analytics():
    analytics = FinancialAnalytics([])
    summary = analytics.generate_summary()
    assert summary["total_transactions"] == 0
    assert summary["total_income"] == 0.0
    assert summary["savings_rate_pct"] == 0.0
    assert analytics.monthly_spending_analysis().empty is True
    assert analytics.category_breakdown().empty is True
    assert analytics.detect_anomalies() == []


def test_financial_summary_metrics(test_transactions):
    analytics = FinancialAnalytics(test_transactions)
    summary = analytics.generate_summary()

    # Total income = 200,000; total expenses = 25000+5000+6000+25000+5500+45000 = 111,500
    assert summary["total_income"] == 200000.0
    assert summary["total_expenses"] == 111500.0
    assert summary["net_savings"] == 88500.0
    # Savings rate: (88500 / 200000) * 100 = 44.25%
    assert summary["savings_rate_pct"] == 44.25
    assert summary["income_count"] == 2
    assert summary["expense_count"] == 6
    assert summary["largest_expense"]["amount"] == 45000.0
    assert summary["largest_expense"]["category"] == "Food"


def test_monthly_spending_analysis(test_transactions):
    analytics = FinancialAnalytics(test_transactions)
    monthly = analytics.monthly_spending_analysis()

    assert len(monthly) == 2
    # Month 1 (2026-01): Expenses = 25000 + 5000 + 6000 = 36000
    # Month 2 (2026-02): Expenses = 25000 + 5500 + 45000 = 75500
    m1 = monthly.iloc[0]
    m2 = monthly.iloc[1]
    assert m1["expenses"] == 36000.0
    assert m2["expenses"] == 75500.0
    # MoM change for month 2 = 75500 - 36000 = 39500
    assert m2["mom_expense_change"] == 39500.0


def test_category_breakdown(test_transactions):
    analytics = FinancialAnalytics(test_transactions)
    cat_df = analytics.category_breakdown()

    # Categories: Food (5000+6000+5500+45000 = 61500), Housing (50000)
    assert len(cat_df) == 2
    assert cat_df.iloc[0]["category"] == "Food"
    assert cat_df.iloc[0]["total_amount"] == 61500.0
    assert cat_df.iloc[1]["category"] == "Housing"
    assert cat_df.iloc[1]["total_amount"] == 50000.0


def test_statistical_anomaly_detection(test_transactions):
    analytics = FinancialAnalytics(test_transactions)
    anomalies = analytics.detect_anomalies(z_score_threshold=1.5, min_category_samples=3)

    # 45000 in Food is vastly higher than 5000, 6000, 5500
    assert len(anomalies) >= 1
    top_anomaly = anomalies[0]
    assert top_anomaly["transaction_id"] == "TX-8"
    assert top_anomaly["amount"] == 45000.0
    assert top_anomaly["category"] == "Food"
    assert top_anomaly["z_score"] >= 1.5
    assert "explanation" in top_anomaly
