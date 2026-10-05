"""Financial analytics module powered by pandas and NumPy."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from models.transaction import Transaction
from utils.helpers import format_inr


class FinancialAnalytics:
    """Provides descriptive, monthly, categorical, and statistical anomaly analytics."""

    def __init__(self, transactions: list[Transaction] | None = None) -> None:
        self.df = self.transactions_to_dataframe(transactions or [])

    @staticmethod
    def transactions_to_dataframe(transactions: list[Transaction]) -> pd.DataFrame:
        """Convert a list of Transaction models into a typed pandas DataFrame."""
        if not transactions:
            return pd.DataFrame(
                columns=[
                    "transaction_id",
                    "amount",
                    "category",
                    "description",
                    "transaction_date",
                    "transaction_type",
                    "account_name",
                    "year_month",
                ]
            )

        records = []
        for tx in transactions:
            records.append(
                {
                    "transaction_id": tx.transaction_id,
                    "amount": float(tx.amount),
                    "category": tx.category,
                    "description": tx.description,
                    "transaction_date": tx.transaction_date,
                    "transaction_type": tx.transaction_type,
                    "account_name": tx.account_name,
                    "year_month": tx.transaction_date[:7],  # 'YYYY-MM'
                }
            )

        df = pd.DataFrame(records)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        df.sort_values(by=["transaction_date", "transaction_id"], inplace=True)
        return df

    def get_expenses_df(self) -> pd.DataFrame:
        """Filter and return only expense transactions."""
        if self.df.empty:
            return self.df
        return self.df[self.df["transaction_type"] == "expense"].copy()

    def get_income_df(self) -> pd.DataFrame:
        """Filter and return only income transactions."""
        if self.df.empty:
            return self.df
        return self.df[self.df["transaction_type"] == "income"].copy()

    # ==================== 1. FINANCIAL SUMMARY ====================

    def generate_summary(self) -> dict[str, Any]:
        """Generate high-level financial summary metrics."""
        if self.df.empty:
            return {
                "total_income": 0.0,
                "total_expenses": 0.0,
                "net_savings": 0.0,
                "savings_rate_pct": 0.0,
                "total_transactions": 0,
                "income_count": 0,
                "expense_count": 0,
                "avg_expense": 0.0,
                "median_expense": 0.0,
                "std_expense": 0.0,
                "largest_expense": None,
                "highest_spending_category": "N/A",
                "highest_spending_day": None,
                "formatted_income": "₹0.00",
                "formatted_expenses": "₹0.00",
                "formatted_savings": "₹0.00",
            }

        inc_df = self.get_income_df()
        exp_df = self.get_expenses_df()

        total_income = float(inc_df["amount"].sum()) if not inc_df.empty else 0.0
        total_expenses = float(exp_df["amount"].sum()) if not exp_df.empty else 0.0
        net_savings = round(total_income - total_expenses, 2)

        # Savings rate = (Net Savings / Total Income) * 100
        savings_rate = (
            round((net_savings / total_income) * 100.0, 2) if total_income > 0 else 0.0
        )

        expense_amounts = exp_df["amount"].to_numpy() if not exp_df.empty else np.array([])
        if len(expense_amounts) > 0:
            avg_expense = round(float(np.mean(expense_amounts)), 2)
            med_expense = round(float(np.median(expense_amounts)), 2)
            std_expense = (
                round(float(np.std(expense_amounts, ddof=1)), 2)
                if len(expense_amounts) > 1
                else 0.0
            )

            largest_idx = exp_df["amount"].idxmax()
            largest_row = exp_df.loc[largest_idx]
            largest_expense = {
                "id": str(largest_row["transaction_id"]),
                "amount": float(largest_row["amount"]),
                "category": str(largest_row["category"]),
                "description": str(largest_row["description"]),
                "date": largest_row["transaction_date"].strftime("%Y-%m-%d"),
                "formatted_amount": format_inr(largest_row["amount"]),
            }

            top_cat = (
                exp_df.groupby("category")["amount"].sum().sort_values(ascending=False).index[0]
            )

            # Daily totals
            daily_totals = exp_df.groupby(exp_df["transaction_date"].dt.strftime("%Y-%m-%d"))[
                "amount"
            ].sum()
            top_day_str = daily_totals.idxmax()
            top_day_amt = float(daily_totals.max())
            highest_spending_day = {
                "date": top_day_str,
                "amount": top_day_amt,
                "formatted_amount": format_inr(top_day_amt),
            }
        else:
            avg_expense = 0.0
            med_expense = 0.0
            std_expense = 0.0
            largest_expense = None
            top_cat = "N/A"
            highest_spending_day = None

        return {
            "total_income": round(total_income, 2),
            "total_expenses": round(total_expenses, 2),
            "net_savings": net_savings,
            "savings_rate_pct": savings_rate,
            "total_transactions": len(self.df),
            "income_count": len(inc_df),
            "expense_count": len(exp_df),
            "avg_expense": avg_expense,
            "median_expense": med_expense,
            "std_expense": std_expense,
            "largest_expense": largest_expense,
            "highest_spending_category": top_cat,
            "highest_spending_day": highest_spending_day,
            "formatted_income": format_inr(total_income),
            "formatted_expenses": format_inr(total_expenses),
            "formatted_savings": format_inr(net_savings),
        }

    # ==================== 2. MONTHLY ANALYSIS ====================

    def monthly_spending_analysis(self) -> pd.DataFrame:
        """Compute monthly income, expenses, net savings, and MoM percentage changes."""
        if self.df.empty:
            return pd.DataFrame(
                columns=[
                    "year_month",
                    "income",
                    "expenses",
                    "net_savings",
                    "savings_rate_pct",
                    "mom_expense_change",
                    "mom_expense_pct_change",
                ]
            )

        # Pivot by month and type
        monthly = (
            self.df.groupby(["year_month", "transaction_type"])["amount"]
            .sum()
            .unstack(fill_value=0.0)
            .reset_index()
        )

        for col in ["income", "expense"]:
            if col not in monthly.columns:
                monthly[col] = 0.0

        monthly.rename(columns={"expense": "expenses"}, inplace=True)
        monthly.sort_values(by="year_month", inplace=True)

        monthly["net_savings"] = (monthly["income"] - monthly["expenses"]).round(2)

        # Savings rate
        monthly["savings_rate_pct"] = np.where(
            monthly["income"] > 0,
            ((monthly["net_savings"] / monthly["income"]) * 100).round(2),
            0.0,
        )

        # Month over month expense change
        monthly["mom_expense_change"] = monthly["expenses"].diff().round(2).fillna(0.0)
        monthly["mom_expense_pct_change"] = (
            monthly["expenses"].pct_change().mul(100).round(2).fillna(0.0)
        )

        return monthly

    def monthly_category_matrix(self) -> pd.DataFrame:
        """Return pivot table of expense categories (rows) by year_month (columns)."""
        exp_df = self.get_expenses_df()
        if exp_df.empty:
            return pd.DataFrame()

        pivot = exp_df.pivot_table(
            index="category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            fill_value=0.0,
        )
        return pivot

    # ==================== 3. CATEGORY ANALYSIS ====================

    def category_breakdown(self) -> pd.DataFrame:
        """Calculate total expense, percentage of total, transaction count, and average per category."""
        exp_df = self.get_expenses_df()
        if exp_df.empty:
            return pd.DataFrame(
                columns=["category", "total_amount", "percentage", "count", "average_amount"]
            )

        total_expenses = exp_df["amount"].sum()
        grouped = (
            exp_df.groupby("category")
            .agg(
                total_amount=("amount", "sum"),
                count=("amount", "count"),
                average_amount=("amount", "mean"),
            )
            .reset_index()
        )

        grouped["percentage"] = (
            (grouped["total_amount"] / total_expenses * 100).round(2)
            if total_expenses > 0
            else 0.0
        )
        grouped["total_amount"] = grouped["total_amount"].round(2)
        grouped["average_amount"] = grouped["average_amount"].round(2)
        grouped.sort_values(by="total_amount", ascending=False, inplace=True)

        return grouped

    # ==================== 4. ANOMALY DETECTION ====================

    def detect_anomalies(
        self, z_score_threshold: float = 2.0, min_category_samples: int = 3
    ) -> list[dict[str, Any]]:
        """Identify statistically unusual expense transactions using category-aware Z-score.

        Anomalies indicate statistically significant deviation from category spending norms.
        They represent unusual expenses, NOT confirmed fraud or errors.

        Args:
            z_score_threshold: Number of standard deviations above mean to flag. Default 2.0.
            min_category_samples: Minimum count of transactions required in a category
                                  before applying category-level Z-score.

        Returns:
            List of dictionaries containing anomalous transactions and statistical context.
        """
        exp_df = self.get_expenses_df()
        if exp_df.empty or len(exp_df) < 3:
            return []

        # Overall distribution metrics as fallback
        global_mean = float(np.mean(exp_df["amount"]))
        global_std = (
            float(np.std(exp_df["amount"], ddof=1)) if len(exp_df) > 1 else 0.0
        )

        anomalies: list[dict[str, Any]] = []

        for category, cat_group in exp_df.groupby("category"):
            amounts = cat_group["amount"].to_numpy()
            n = len(amounts)

            if n >= min_category_samples:
                mean_val = float(np.mean(amounts))
                std_val = float(np.std(amounts, ddof=1)) if n > 1 else 0.0
                method = "category_z_score"
            else:
                mean_val = global_mean
                std_val = global_std
                method = "global_z_score"

            if std_val <= 1e-6:
                # Zero or negligible variance, cannot divide by zero
                continue

            for _, row in cat_group.iterrows():
                amt = float(row["amount"])
                z = (amt - mean_val) / std_val
                z_rounded = round(float(z), 2)

                if z_rounded >= z_score_threshold:
                    anomalies.append(
                        {
                            "transaction_id": str(row["transaction_id"]),
                            "date": row["transaction_date"].strftime("%Y-%m-%d"),
                            "category": str(category),
                            "description": str(row["description"]),
                            "amount": amt,
                            "formatted_amount": format_inr(amt),
                            "z_score": z_rounded,
                            "category_mean": round(mean_val, 2),
                            "category_std": round(std_val, 2),
                            "method": method,
                            "explanation": (
                                f"Amount {format_inr(amt)} is {z_rounded:.1f} standard deviations above "
                                f"average {format_inr(mean_val)} for category '{category}'."
                            ),
                        }
                    )

        # Sort anomalies by z_score descending
        anomalies.sort(key=lambda x: x["z_score"], reverse=True)
        return anomalies
