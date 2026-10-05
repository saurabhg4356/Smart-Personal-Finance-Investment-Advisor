"""Unit tests for SpendingPredictor using scikit-learn Linear Regression."""

import pytest

from models.exceptions import NotEnoughDataError
from models.transaction import Transaction
from services.predictor import SpendingPredictor


def test_predictor_insufficient_data():
    predictor = SpendingPredictor(min_months=3)
    # Empty
    with pytest.raises(NotEnoughDataError):
        predictor.predict_next_month([])

    # Only 2 months of data
    txs_2_months = [
        Transaction("TX-1", 10000.0, "Food", "Groceries", "2026-01-10", "expense", "HDFC"),
        Transaction("TX-2", 12000.0, "Food", "Groceries", "2026-02-10", "expense", "HDFC"),
    ]
    with pytest.raises(NotEnoughDataError) as exc_info:
        predictor.predict_next_month(txs_2_months)
    assert exc_info.value.required_records == 3
    assert exc_info.value.actual_records == 2


def test_predictor_successful_forecasting():
    predictor = SpendingPredictor(min_months=3)
    # 5 consecutive months of linearly increasing expenses: 20000, 22000, 24000, 26000, 28000
    txs = [
        Transaction("TX-1", 20000.0, "General", "Exp 1", "2025-10-05", "expense", "HDFC"),
        Transaction("TX-2", 22000.0, "General", "Exp 2", "2025-11-05", "expense", "HDFC"),
        Transaction("TX-3", 24000.0, "General", "Exp 3", "2025-12-05", "expense", "HDFC"),
        Transaction("TX-4", 26000.0, "General", "Exp 4", "2026-01-05", "expense", "HDFC"),
        Transaction("TX-5", 28000.0, "General", "Exp 5", "2026-02-05", "expense", "HDFC"),
    ]

    result = predictor.predict_next_month(txs)

    assert result["historical_months_count"] == 5
    assert result["target_month"] == "2026-03"
    # Linear trend slope is +2000/month; next prediction should be approximately 30000
    assert 29990.0 <= result["predicted_amount"] <= 30010.0
    assert result["trend_direction"] == "increasing"
    assert result["slope_per_month"] == pytest.approx(2000.0, abs=1.0)
    assert result["in_sample_mae"] == pytest.approx(0.0, abs=1.0)
    assert result["backtest_mae"] is not None
    assert result["r2_score"] == pytest.approx(1.0, abs=0.01)
    assert result["disclaimer"] is not None


def test_predictor_non_negative_clamp():
    predictor = SpendingPredictor(min_months=3)
    # Sharply decreasing expenses
    txs = [
        Transaction("TX-1", 50000.0, "General", "Exp 1", "2025-10-05", "expense", "HDFC"),
        Transaction("TX-2", 20000.0, "General", "Exp 2", "2025-11-05", "expense", "HDFC"),
        Transaction("TX-3", 5000.0, "General", "Exp 3", "2025-12-05", "expense", "HDFC"),
    ]
    result = predictor.predict_next_month(txs)
    # Negative predictions must be clamped to 0.0
    assert result["predicted_amount"] >= 0.0
