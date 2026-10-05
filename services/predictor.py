"""Monthly expense forecasting using scikit-learn Linear Regression."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

from models.exceptions import NotEnoughDataError
from models.transaction import Transaction
from utils.helpers import format_inr


class SpendingPredictor:
    """Predicts next month's aggregate spending using Linear Regression on historical monthly expenses."""

    DISCLAIMER = (
        "STATISTICAL ESTIMATE DISCLAIMER: This projection is generated via a basic linear "
        "regression model on historical monthly expenses for educational purposes. "
        "It does not guarantee future financial outcomes and should not be used as sole financial advice."
    )

    def __init__(self, min_months: int = 3) -> None:
        self.min_months = min_months
        self.model: LinearRegression | None = None

    @staticmethod
    def _prepare_monthly_expenses(transactions: list[Transaction]) -> pd.DataFrame:
        """Aggregate expenses by continuous calendar month."""
        expense_txs = [tx for tx in transactions if tx.is_expense]
        if not expense_txs:
            return pd.DataFrame(columns=["year_month", "expenses"])

        records = [
            {"date": tx.transaction_date, "amount": float(tx.amount)}
            for tx in expense_txs
        ]
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        df["year_month"] = df["date"].dt.to_period("M")

        monthly = df.groupby("year_month")["amount"].sum().reset_index()
        monthly.rename(columns={"amount": "expenses"}, inplace=True)
        monthly.sort_values(by="year_month", inplace=True)

        # Build complete continuous monthly range between min and max month to handle gaps
        if not monthly.empty:
            full_range = pd.period_range(
                start=monthly["year_month"].min(),
                end=monthly["year_month"].max(),
                freq="M",
            )
            full_df = pd.DataFrame({"year_month": full_range})
            monthly = full_df.merge(monthly, on="year_month", how="left").fillna(
                {"expenses": 0.0}
            )

        monthly["month_index"] = np.arange(len(monthly))
        monthly["year_month_str"] = monthly["year_month"].astype(str)
        return monthly

    def predict_next_month(self, transactions: list[Transaction]) -> dict[str, Any]:
        """Train linear regression on historical expenses and predict next month's spending.

        Raises:
            NotEnoughDataError: If fewer than min_months of expense data are available.
        """
        monthly = self._prepare_monthly_expenses(transactions)
        num_months = len(monthly)

        if num_months < self.min_months:
            raise NotEnoughDataError(
                required_records=self.min_months,
                actual_records=num_months,
                context="Spending Prediction (Linear Regression)",
                resolution_hint=f"Record expenses across at least {self.min_months} distinct months or run demo mode.",
            )

        # Feature matrix X: 2D array of month indices [[0], [1], [2], ...]
        X = monthly[["month_index"]].to_numpy()
        y = monthly["expenses"].to_numpy()

        # Fit model on historical data
        self.model = LinearRegression()
        self.model.fit(X, y)

        # In-sample predictions and metrics
        y_pred_in_sample = self.model.predict(X)
        in_sample_mae = float(mean_absolute_error(y, y_pred_in_sample))

        # R^2 score
        r2 = float(r2_score(y, y_pred_in_sample)) if num_months > 1 else 0.0

        # Chronological holdout evaluation (train on months 0..N-2, test on month N-1)
        backtest_mae = None
        if num_months >= 4:
            X_train, y_train = X[:-1], y[:-1]
            X_test, y_test = X[-1:], y[-1:]
            eval_model = LinearRegression().fit(X_train, y_train)
            y_holdout_pred = eval_model.predict(X_test)
            backtest_mae = float(mean_absolute_error(y_test, y_holdout_pred))

        # Predict next month (month_index = num_months)
        next_index = np.array([[num_months]])
        raw_prediction = float(self.model.predict(next_index)[0])
        # Monetary expenses cannot be negative
        predicted_spending = max(0.0, round(raw_prediction, 2))

        # Calculate target month string (e.g. '2026-04')
        last_period = monthly["year_month"].iloc[-1]
        next_period = last_period + 1
        target_month_str = str(next_period)

        slope = float(self.model.coef_[0])
        intercept = float(self.model.intercept_)

        trend_direction = "increasing" if slope > 50 else ("decreasing" if slope < -50 else "stable")

        return {
            "predicted_amount": predicted_spending,
            "target_month": target_month_str,
            "historical_months_count": num_months,
            "slope_per_month": round(slope, 2),
            "intercept": round(intercept, 2),
            "trend_direction": trend_direction,
            "in_sample_mae": round(in_sample_mae, 2),
            "backtest_mae": round(backtest_mae, 2) if backtest_mae is not None else None,
            "r2_score": round(r2, 4),
            "formatted_predicted": format_inr(predicted_spending),
            "historical_monthly_data": monthly[["year_month_str", "expenses"]].to_dict(
                orient="records"
            ),
            "disclaimer": self.DISCLAIMER,
        }
