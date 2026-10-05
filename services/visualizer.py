"""Matplotlib visualizer for generating financial charts from real application data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Headless backend safe for CLI and servers
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from models.investment import Investment
from models.transaction import Transaction
from services.analytics import FinancialAnalytics
from services.predictor import SpendingPredictor
from utils.helpers import format_inr


class FinancialVisualizer:
    """Generates informative and aesthetically polished financial charts."""

    # Curated modern color palette
    PALETTE = [
        "#2563EB",  # Royal Blue
        "#10B981",  # Emerald Green
        "#F59E0B",  # Amber
        "#EF4444",  # Crimson Red
        "#8B5CF6",  # Purple
        "#06B6D4",  # Cyan
        "#EC4899",  # Pink
        "#64748B",  # Slate
        "#F97316",  # Orange
        "#14B8A6",  # Teal
    ]

    def __init__(self, charts_dir: Path | str = "charts") -> None:
        self.charts_dir = Path(charts_dir)
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    def _setup_figure(
        self, title: str, xlabel: str = "", ylabel: str = "", figsize: tuple[int, int] = (9, 5)
    ) -> tuple[plt.Figure, plt.Axes]:
        """Configure standard figure layout and typography."""
        fig, ax = plt.subplots(figsize=figsize, dpi=150)
        ax.set_title(title, fontsize=13, fontweight="bold", pad=14, color="#1E293B")
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10, fontweight="semibold", labelpad=8, color="#334155")
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, fontweight="semibold", labelpad=8, color="#334155")

        ax.grid(True, linestyle="--", alpha=0.35, color="#94A3B8")
        ax.set_axisbelow(True)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#CBD5E1")
        ax.spines["bottom"].set_color("#CBD5E1")
        return fig, ax

    # ==================== 1. EXPENSE DISTRIBUTION ====================

    def plot_expense_distribution(
        self, transactions: list[Transaction], filename: str = "expense_distribution.png"
    ) -> Path | None:
        """Donut chart showing expense breakdown by category."""
        analytics = FinancialAnalytics(transactions)
        cat_df = analytics.category_breakdown()

        if cat_df.empty:
            return None

        fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
        labels = cat_df["category"].tolist()
        sizes = cat_df["total_amount"].tolist()
        colors = [self.PALETTE[i % len(self.PALETTE)] for i in range(len(labels))]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.8,
            wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
        )

        for text in texts:
            text.set_color("#1E293B")
            text.set_fontsize(9)
            text.set_fontweight("semibold")
        for autotext in autotexts:
            autotext.set_color("#0F172A")
            autotext.set_fontsize(8)

        total_exp = cat_df["total_amount"].sum()
        ax.text(
            0,
            0,
            f"Total Expenses\n{format_inr(total_exp)}",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=10,
            fontweight="bold",
            color="#334155",
        )

        ax.set_title(
            "Expense Distribution by Category",
            fontsize=13,
            fontweight="bold",
            pad=15,
            color="#1E293B",
        )

        output_path = self.charts_dir / filename
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    # ==================== 2. MONTHLY INCOME VS EXPENSES ====================

    def plot_income_vs_expenses(
        self, transactions: list[Transaction], filename: str = "monthly_income_vs_expense.png"
    ) -> Path | None:
        """Grouped bar chart comparing monthly income versus monthly expenses."""
        analytics = FinancialAnalytics(transactions)
        monthly = analytics.monthly_spending_analysis()

        if monthly.empty:
            return None

        fig, ax = self._setup_figure(
            title="Monthly Income vs Expenses",
            xlabel="Month",
            ylabel="Amount (₹)",
            figsize=(10, 5),
        )

        x = np.arange(len(monthly))
        width = 0.35

        bars1 = ax.bar(
            x - width / 2,
            monthly["income"],
            width,
            label="Income",
            color="#10B981",
            edgecolor="none",
            alpha=0.9,
        )
        bars2 = ax.bar(
            x + width / 2,
            monthly["expenses"],
            width,
            label="Expenses",
            color="#EF4444",
            edgecolor="none",
            alpha=0.9,
        )

        ax.set_xticks(x)
        ax.set_xticklabels(monthly["year_month"], rotation=30, ha="right", fontsize=9)
        ax.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#E2E8F0", loc="upper left")

        # Format Y-axis tick labels
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda val, pos: f"₹{val:,.0f}")
        )

        output_path = self.charts_dir / filename
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    # ==================== 3. MONTHLY SPENDING TREND ====================

    def plot_spending_trend(
        self, transactions: list[Transaction], filename: str = "spending_trend.png"
    ) -> Path | None:
        """Line chart showing monthly spending trend with average baseline."""
        analytics = FinancialAnalytics(transactions)
        monthly = analytics.monthly_spending_analysis()

        if monthly.empty:
            return None

        fig, ax = self._setup_figure(
            title="Monthly Expense Trend",
            xlabel="Month",
            ylabel="Monthly Expenses (₹)",
            figsize=(10, 5),
        )

        months = monthly["year_month"].tolist()
        expenses = monthly["expenses"].tolist()

        ax.plot(
            months,
            expenses,
            color="#2563EB",
            marker="o",
            linewidth=2.5,
            markersize=6,
            label="Actual Monthly Expenses",
        )
        ax.fill_between(months, expenses, color="#93C5FD", alpha=0.25)

        avg_expense = float(np.mean(expenses))
        ax.axhline(
            avg_expense,
            color="#F59E0B",
            linestyle="--",
            linewidth=1.8,
            label=f"Historical Average ({format_inr(avg_expense)})",
        )

        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=30, ha="right", fontsize=9)
        ax.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#E2E8F0")
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda val, pos: f"₹{val:,.0f}")
        )

        output_path = self.charts_dir / filename
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    # ==================== 4. ACTUAL VS PREDICTED SPENDING ====================

    def plot_actual_vs_predicted(
        self, transactions: list[Transaction], filename: str = "actual_vs_predicted.png"
    ) -> Path | None:
        """Line chart contrasting actual monthly historical spending with Linear Regression forecast."""
        predictor = SpendingPredictor(min_months=3)
        try:
            pred_result = predictor.predict_next_month(transactions)
        except Exception:
            return None

        hist_records = pred_result["historical_monthly_data"]
        months = [r["year_month_str"] for r in hist_records]
        actual_amounts = [r["expenses"] for r in hist_records]

        target_month = pred_result["target_month"]
        predicted_amount = pred_result["predicted_amount"]

        all_months = months + [target_month]

        fig, ax = self._setup_figure(
            title=f"Monthly Spending: Actual vs Predicted Forecast ({target_month})",
            xlabel="Month",
            ylabel="Expenses (₹)",
            figsize=(10, 5),
        )

        # Plot historical line
        ax.plot(
            months,
            actual_amounts,
            color="#2563EB",
            marker="o",
            linewidth=2.2,
            label="Historical Actual Spending",
        )

        # Connect last actual month to predicted month via dashed line
        pred_x = [months[-1], target_month]
        pred_y = [actual_amounts[-1], predicted_amount]
        ax.plot(
            pred_x,
            pred_y,
            color="#DC2626",
            linestyle="--",
            linewidth=2.0,
            marker="s",
            label=f"Projected Forecast ({format_inr(predicted_amount)})",
        )

        # Add annotation for predicted point
        ax.annotate(
            f"Forecast:\n{format_inr(predicted_amount)}",
            xy=(target_month, predicted_amount),
            xytext=(10, 15),
            textcoords="offset points",
            fontweight="bold",
            color="#DC2626",
            arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.2),
        )

        ax.set_xticks(range(len(all_months)))
        ax.set_xticklabels(all_months, rotation=30, ha="right", fontsize=9)
        ax.legend(frameon=True, facecolor="#F8FAFC", edgecolor="#E2E8F0")
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda val, pos: f"₹{val:,.0f}")
        )

        output_path = self.charts_dir / filename
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    # ==================== 5. PORTFOLIO ALLOCATION ====================

    def plot_portfolio_allocation(
        self, investments: list[Investment], filename: str = "portfolio_allocation.png"
    ) -> Path | None:
        """Donut chart showing simulated investment portfolio asset allocation."""
        if not investments:
            return None

        # Group by asset type
        allocation: dict[str, float] = {}
        for inv in investments:
            allocation[inv.asset_type] = (
                allocation.get(inv.asset_type, 0.0) + inv.current_estimated_value
            )

        labels = list(allocation.keys())
        sizes = list(allocation.values())
        total_val = sum(sizes)

        if total_val <= 0:
            return None

        fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
        colors = [self.PALETTE[i % len(self.PALETTE)] for i in range(len(labels))]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.8,
            wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
        )

        for text in texts:
            text.set_color("#1E293B")
            text.set_fontsize(9)
            text.set_fontweight("semibold")
        for autotext in autotexts:
            autotext.set_color("#0F172A")
            autotext.set_fontsize(8)

        ax.text(
            0,
            0,
            f"Portfolio Value\n{format_inr(total_val)}",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=10,
            fontweight="bold",
            color="#334155",
        )

        ax.set_title(
            "Simulated Portfolio Asset Allocation",
            fontsize=13,
            fontweight="bold",
            pad=15,
            color="#1E293B",
        )

        output_path = self.charts_dir / filename
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    def generate_all_charts(
        self, transactions: list[Transaction], investments: list[Investment]
    ) -> dict[str, Path | None]:
        """Generate all supported financial charts and return dict of paths."""
        return {
            "expense_distribution": self.plot_expense_distribution(transactions),
            "income_vs_expenses": self.plot_income_vs_expenses(transactions),
            "spending_trend": self.plot_spending_trend(transactions),
            "actual_vs_predicted": self.plot_actual_vs_predicted(transactions),
            "portfolio_allocation": self.plot_portfolio_allocation(investments),
        }
