"""Main entry point for Smart Personal Finance & Investment Advisor CLI."""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path
import shutil
import sys
from typing import Any

from models.exceptions import (
    FinanceAdvisorError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidTransactionError,
    NotEnoughDataError,
    TransactionNotFoundError,
)
from services.analytics import FinancialAnalytics
from services.budget_manager import BudgetManager
from services.categorizer import TransactionCategorizer
from services.finance_manager import FinanceManager
from services.investment_manager import InvestmentManager
from services.predictor import SpendingPredictor
from services.storage import StorageService
from services.visualizer import FinancialVisualizer
from utils.helpers import format_inr, truncate_string

APP_TITLE = "SMART PERSONAL FINANCE & INVESTMENT ADVISOR"
APP_VERSION = "1.0.0"
DEFAULT_DATA_DIR = Path("data")


def prompt_string(prompt_msg: str, default: str | None = None) -> str:
    """Prompt user for a non-empty string."""
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            val = input(f"{prompt_msg}{suffix}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return ""
        if val:
            return val
        if default is not None:
            return default
        print("Error: Input cannot be empty. Please try again.")


def prompt_float(prompt_msg: str, allow_zero: bool = False) -> float:
    """Prompt user for a valid positive float."""
    while True:
        try:
            val_str = input(f"{prompt_msg}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return -1.0
        try:
            val = float(val_str)
            if allow_zero and val >= 0:
                return val
            if not allow_zero and val > 0:
                return val
            print(f"Error: Value must be {'non-negative' if allow_zero else 'strictly positive'}.")
        except ValueError:
            print(f"Error: '{val_str}' is not a valid number. Please enter a valid amount.")


class FinancialAdvisorCLI:
    """Coordinates command-line user interactions with domain services."""

    def __init__(self, demo_mode: bool = False, base_dir: Path = DEFAULT_DATA_DIR) -> None:
        self.demo_mode = demo_mode
        self.base_dir = base_dir
        self.storage = StorageService(base_dir)

        # File paths
        if self.demo_mode:
            # In demo mode, load directly from immutable sample files
            self.tx_file = self.base_dir / "sample_transactions.csv"
            self.acc_file = self.base_dir / "sample_accounts.csv"
            self.budgets_file = self.base_dir / "sample_budgets.csv"
            self.investments_file = self.base_dir / "sample_investments.csv"
        else:
            self.tx_file = self.base_dir / "transactions.csv"
            self.acc_file = self.base_dir / "accounts.csv"
            self.budgets_file = self.base_dir / "budgets.csv"
            self.investments_file = self.base_dir / "investments.csv"
            self._ensure_user_data_files()

        # Initialize core managers
        self.finance = FinanceManager(
            storage_service=self.storage,
            transactions_file=self.tx_file,
            accounts_file=self.acc_file,
        )
        self.budget_mgr = BudgetManager(
            storage_service=self.storage,
            budgets_file=self.budgets_file,
        )
        self.investment_mgr = InvestmentManager(
            storage_service=self.storage,
            investments_file=self.investments_file,
        )
        self.visualizer = FinancialVisualizer(charts_dir="charts")
        self.categorizer = TransactionCategorizer()
        self.predictor = SpendingPredictor(min_months=3)

    def _ensure_user_data_files(self) -> None:
        """Create initial files if user data does not exist yet."""
        if not self.acc_file.exists():
            default_accs = [
                {
                    "account_id": "ACC-001",
                    "account_name": "Primary Bank Account",
                    "opening_balance": "50000.00",
                    "current_balance": "50000.00",
                    "account_type": "Savings",
                    "extra_info": "4.0",
                },
                {
                    "account_id": "ACC-002",
                    "account_name": "Investment Wallet",
                    "opening_balance": "10000.00",
                    "current_balance": "10000.00",
                    "account_type": "Investment",
                    "extra_info": "",
                },
            ]
            self.storage.save_accounts(
                [self.storage.load_accounts(self.acc_file)] if False else [], self.acc_file
            )
            # Write default accounts
            import csv
            with open(self.acc_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "account_id",
                        "account_name",
                        "opening_balance",
                        "current_balance",
                        "account_type",
                        "extra_info",
                    ],
                )
                writer.writeheader()
                writer.writerows(default_accs)

        if not self.tx_file.exists():
            self.storage.save_transactions([], self.tx_file)
        if not self.budgets_file.exists():
            self.storage.save_budgets([], self.budgets_file)
        if not self.investments_file.exists():
            self.storage.save_investments([], self.investments_file)

    def print_header(self) -> None:
        mode_str = " [DEMO MODE (Sample Data)]" if self.demo_mode else ""
        print("=" * 64)
        print(f"        {APP_TITLE}{mode_str}")
        print("=" * 64)

    def display_menu(self) -> None:
        menu = f"""
 1. Add Income                    8. View Accounts
 2. Add Expense                   9. Manage Budgets
 3. View Transactions            10. View Budget Status
 4. Search Transactions          11. Manage Investment Portfolio
 5. Edit Transaction             12. View Portfolio Summary
 6. Delete Transaction           13. Financial Summary (pandas/NumPy)
 7. Undo Last Operation          14. Monthly Spending Analysis
                                 15. Category Analysis
 16. Detect Unusual Expenses     19. Auto-Categorize Transaction (NLP)
 17. View Top Expenses (Heap)    20. Generate Financial Charts
 18. Predict Next Month (ML)     21. Load Demo Data
                                 22. Export Financial Report
                                  0. Exit
{"=" * 64}"""
        print(menu)

    def run(self) -> None:
        """Main application REPL loop."""
        self.print_header()
        while True:
            self.display_menu()
            try:
                choice = input("Select an option (0-22): ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n\nExiting application. Goodbye!")
                break

            if choice == "0":
                print("\nThank you for using Smart Personal Finance & Investment Advisor. Goodbye!")
                break

            try:
                self.route_choice(choice)
            except FinanceAdvisorError as err:
                print(f"\n[Error] {err}")
            except Exception as exc:
                print(f"\n[Unexpected Error] An error occurred: {exc}")

            input("\nPress [Enter] to return to the main menu...")

    def route_choice(self, choice: str) -> None:
        actions = {
            "1": self.cmd_add_income,
            "2": self.cmd_add_expense,
            "3": self.cmd_view_transactions,
            "4": self.cmd_search_transactions,
            "5": self.cmd_edit_transaction,
            "6": self.cmd_delete_transaction,
            "7": self.cmd_undo,
            "8": self.cmd_view_accounts,
            "9": self.cmd_manage_budgets,
            "10": self.cmd_view_budget_status,
            "11": self.cmd_manage_investments,
            "12": self.cmd_view_portfolio_summary,
            "13": self.cmd_financial_summary,
            "14": self.cmd_monthly_analysis,
            "15": self.cmd_category_analysis,
            "16": self.cmd_detect_anomalies,
            "17": self.cmd_top_expenses,
            "18": self.cmd_predict_spending,
            "19": self.cmd_auto_categorize,
            "20": self.cmd_generate_charts,
            "21": self.cmd_load_demo_data,
            "22": self.cmd_export_report,
        }

        action = actions.get(choice)
        if action:
            action()
        else:
            print(f"Invalid option '{choice}'. Please choose a valid number from the menu.")

    # ==================== TRANSACTION COMMANDS ====================

    def cmd_add_income(self) -> None:
        print("\n--- ADD INCOME ---")
        amount = prompt_float("Enter income amount (INR)")
        if amount <= 0:
            return

        desc = prompt_string("Enter description (e.g., Monthly salary credit)")
        if not desc:
            return

        # Suggested category via NLP
        pred = self.categorizer.predict(desc)
        suggested_cat = pred["category"] if pred["category"] != "Other" else "Salary"
        cat = prompt_string("Category", default=suggested_cat)

        dt = prompt_string("Date (YYYY-MM-DD)", default=date.today().isoformat())

        accounts = self.finance.list_accounts()
        if not accounts:
            print("No accounts available. Please add an account first.")
            return

        print("\nAvailable Accounts:")
        for idx, acc in enumerate(accounts, start=1):
            print(f"  {idx}. {acc.account_name} (Balance: {format_inr(acc.current_balance)})")
        acc_choice = prompt_string("Select account number or enter name", default="1")
        acc_name = accounts[0].account_name
        if acc_choice.isdigit() and 1 <= int(acc_choice) <= len(accounts):
            acc_name = accounts[int(acc_choice) - 1].account_name
        elif acc_choice:
            acc_name = acc_choice

        tx = self.finance.add_transaction(
            amount=amount,
            category=cat,
            description=desc,
            transaction_date=dt,
            transaction_type="income",
            account_name=acc_name,
        )
        print(f"\n[Success] Income recorded: {tx}")
        print(f"Updated balance of '{acc_name}': {format_inr(self.finance.get_account(acc_name).current_balance)}")

    def cmd_add_expense(self) -> None:
        print("\n--- ADD EXPENSE ---")
        amount = prompt_float("Enter expense amount (INR)")
        if amount <= 0:
            return

        desc = prompt_string("Enter description (e.g., Swiggy dinner or Uber ride)")
        if not desc:
            return

        # Category suggestion via TF-IDF + Naive Bayes
        pred = self.categorizer.predict(desc)
        suggested_cat = pred["category"]
        if pred["is_confident"]:
            print(f"  [AI Recommendation] Suggested Category: '{suggested_cat}' (Confidence: {pred['confidence']:.1%})")
        cat = prompt_string("Category", default=suggested_cat)

        dt = prompt_string("Date (YYYY-MM-DD)", default=date.today().isoformat())

        accounts = self.finance.list_accounts()
        if not accounts:
            print("No accounts available.")
            return

        print("\nAvailable Accounts:")
        for idx, acc in enumerate(accounts, start=1):
            print(f"  {idx}. {acc.account_name} (Balance: {format_inr(acc.current_balance)})")
        acc_choice = prompt_string("Select account number or enter name", default="1")
        acc_name = accounts[0].account_name
        if acc_choice.isdigit() and 1 <= int(acc_choice) <= len(accounts):
            acc_name = accounts[int(acc_choice) - 1].account_name
        elif acc_choice:
            acc_name = acc_choice

        # Check budget alert before committing
        from models.transaction import Transaction
        temp_tx = Transaction(
            transaction_id="TEMP-000",
            amount=amount,
            category=cat,
            description=desc,
            transaction_date=dt,
            transaction_type="expense",
            account_name=acc_name,
        )
        is_ok, budget_warn = self.budget_mgr.evaluate_transaction(
            temp_tx, self.finance.list_transactions()
        )
        if budget_warn:
            print(f"\n[WARNING] {budget_warn}")
            confirm = prompt_string("Do you still wish to proceed? (yes/no)", default="yes")
            if confirm.lower() not in ("yes", "y"):
                print("Expense entry cancelled.")
                return

        tx = self.finance.add_transaction(
            amount=amount,
            category=cat,
            description=desc,
            transaction_date=dt,
            transaction_type="expense",
            account_name=acc_name,
        )
        print(f"\n[Success] Expense recorded: {tx}")
        print(f"Updated balance of '{acc_name}': {format_inr(self.finance.get_account(acc_name).current_balance)}")

    def cmd_view_transactions(self) -> None:
        print("\n--- VIEW TRANSACTIONS ---")
        txs = self.finance.list_transactions()
        if not txs:
            print("No transactions recorded yet.")
            return

        print(f"Total Transactions: {len(txs)}")
        print("-" * 92)
        print(f"{'ID':<10} {'Date':<12} {'Type':<8} {'Amount':>14} {'Category':<14} {'Account':<18} {'Description'}")
        print("-" * 92)
        # Display the most recent 25 by default or prompt
        display_txs = txs[-30:] if len(txs) > 30 else txs
        if len(txs) > 30:
            print(f"Showing the latest 30 of {len(txs)} transactions:")

        for tx in display_txs:
            sign = "+" if tx.is_income else "-"
            amt_str = f"{sign}{format_inr(tx.amount)}"
            print(
                f"{tx.transaction_id:<10} {tx.transaction_date:<12} {tx.transaction_type:<8} "
                f"{amt_str:>14} {tx.category:<14} {truncate_string(tx.account_name, 16):<18} {tx.description}"
            )
        print("-" * 92)

    def cmd_search_transactions(self) -> None:
        print("\n--- SEARCH & FILTER TRANSACTIONS ---")
        print("1. Search by Description / Transaction ID (Hash Map / Substring)")
        print("2. Filter by Date Range (Binary Search / Bisect)")
        sub_choice = prompt_string("Select search mode (1 or 2)", default="1")

        if sub_choice == "2":
            start_date = prompt_string("Start Date (YYYY-MM-DD)", default="2025-01-01")
            end_date = prompt_string("End Date (YYYY-MM-DD)", default=date.today().isoformat())
            matched = self.finance.filter_by_date_range(start_date, end_date)
            print(f"\n[Binary Search Result] Found {len(matched)} transactions between {start_date} and {end_date}:")
        else:
            query = prompt_string("Search keyword or Transaction ID (leave blank for all)", default="")
            cat = prompt_string("Filter by Category (optional)", default="")
            matched = self.finance.search_transactions(query=query, category=cat)
            print(f"\nFound {len(matched)} matching transactions:")

        if not matched:
            print("No matching transactions found.")
            return

        print("-" * 88)
        print(f"{'ID':<10} {'Date':<12} {'Type':<8} {'Amount':>14} {'Category':<14} {'Description'}")
        print("-" * 88)
        for tx in matched[:50]:
            sign = "+" if tx.is_income else "-"
            amt_str = f"{sign}{format_inr(tx.amount)}"
            print(f"{tx.transaction_id:<10} {tx.transaction_date:<12} {tx.transaction_type:<8} {amt_str:>14} {tx.category:<14} {tx.description}")
        if len(matched) > 50:
            print(f"... and {len(matched) - 50} more records.")
        print("-" * 88)

    def cmd_edit_transaction(self) -> None:
        print("\n--- EDIT TRANSACTION ---")
        tx_id = prompt_string("Enter Transaction ID to edit (e.g. TX-00001)")
        tx = self.finance.get_transaction_by_id(tx_id)
        print(f"Current Record: {tx}")

        new_amt_str = input(f"New Amount (current: {tx.amount}) [press Enter to keep]: ").strip()
        new_amt = float(new_amt_str) if new_amt_str else None

        new_desc_str = input(f"New Description (current: '{tx.description}') [press Enter to keep]: ").strip()
        new_desc = new_desc_str if new_desc_str else None

        new_cat_str = input(f"New Category (current: '{tx.category}') [press Enter to keep]: ").strip()
        new_cat = new_cat_str if new_cat_str else None

        new_date_str = input(f"New Date (current: '{tx.transaction_date}') [press Enter to keep]: ").strip()
        new_date = new_date_str if new_date_str else None

        updated = self.finance.edit_transaction(
            transaction_id=tx_id,
            new_amount=new_amt,
            new_category=new_cat,
            new_description=new_desc,
            new_date=new_date,
        )
        print(f"\n[Success] Transaction updated: {updated}")

    def cmd_delete_transaction(self) -> None:
        print("\n--- DELETE TRANSACTION ---")
        tx_id = prompt_string("Enter Transaction ID to delete")
        tx = self.finance.get_transaction_by_id(tx_id)
        print(f"Transaction to delete: {tx}")
        confirm = prompt_string(f"Are you sure you want to delete {tx_id}? (yes/no)", default="no")
        if confirm.lower() in ("yes", "y"):
            self.finance.delete_transaction(tx_id)
            print(f"[Success] Transaction {tx_id} deleted and account balance restored.")
        else:
            print("Deletion cancelled.")

    def cmd_undo(self) -> None:
        print("\n--- UNDO LAST OPERATION ---")
        if self.finance.undo_stack.is_empty():
            print("Undo stack is empty. No operations to undo.")
            return

        top = self.finance.undo_stack.peek()
        print(f"Top operation on stack: {top.action_type} - {top.description}")
        confirm = prompt_string("Confirm rollback of this action? (yes/no)", default="yes")
        if confirm.lower() in ("yes", "y"):
            msg = self.finance.undo_last_operation()
            print(f"[Undo Result] {msg}")
        else:
            print("Undo cancelled.")

    # ==================== ACCOUNT & BUDGET COMMANDS ====================

    def cmd_view_accounts(self) -> None:
        print("\n--- REGISTERED ACCOUNTS ---")
        accounts = self.finance.list_accounts()
        if not accounts:
            print("No accounts found.")
            return

        print("-" * 80)
        print(f"{'ID':<10} {'Account Name':<28} {'Type':<14} {'Current Balance':>18}")
        print("-" * 80)
        for acc in accounts:
            print(f"{acc.account_id:<10} {acc.account_name:<28} {acc.account_type:<14} {format_inr(acc.current_balance):>18}")
        print("-" * 80)

        total_cash = self.finance.calculate_total_liquidity()
        total_net_worth = self.finance.calculate_net_worth()
        print(f"Total Liquid Cash:    {format_inr(total_cash)}")
        print(f"Total Net Worth:      {format_inr(total_net_worth)}")

        # Offer to add account
        add_more = prompt_string("\nAdd a new account? (yes/no)", default="no")
        if add_more.lower() in ("yes", "y"):
            name = prompt_string("Account Name (e.g. Axis Savings)")
            opening = prompt_float("Opening Balance (INR)", allow_zero=True)
            acc_type = prompt_string("Account Type (Savings/Investment/Standard)", default="Savings")
            new_acc = self.finance.add_account(name, opening, acc_type)
            print(f"[Success] Account created: {new_acc}")

    def cmd_manage_budgets(self) -> None:
        print("\n--- MANAGE BUDGETS ---")
        print("1. View Configured Budgets")
        print("2. Set / Update Category Budget")
        print("3. Delete Budget")
        sub = prompt_string("Select option", default="1")

        if sub == "1":
            budgets = self.budget_mgr.list_budgets()
            if not budgets:
                print("No budgets configured yet.")
                return
            print("-" * 65)
            print(f"{'ID':<15} {'Category':<18} {'Month-Year':<12} {'Limit (INR)':>16}")
            print("-" * 65)
            for b in budgets:
                print(f"{b.budget_id:<15} {b.category:<18} {b.year}-{b.month:02d}      {format_inr(b.monthly_limit):>16}")
            print("-" * 65)

        elif sub == "2":
            cat = prompt_string("Category (e.g. Food, Groceries, Shopping)")
            limit = prompt_float("Monthly Spending Limit (INR)")
            m = prompt_string("Month (1-12)", default=str(date.today().month))
            y = prompt_string("Year (YYYY)", default=str(date.today().year))
            b = self.budget_mgr.set_budget(cat, limit, int(m), int(y))
            print(f"[Success] Budget configured: {b}")

        elif sub == "3":
            bid = prompt_string("Enter Budget ID to delete")
            if self.budget_mgr.delete_budget(bid):
                print(f"[Success] Budget {bid} deleted.")
            else:
                print(f"Budget {bid} not found.")

    def cmd_view_budget_status(self) -> None:
        print("\n--- BUDGET STATUS & ALERTS ---")
        txs = self.finance.list_transactions()
        statuses = self.budget_mgr.get_all_budget_statuses(txs)
        if not statuses:
            print("No budgets configured. Use option 9 to configure monthly budgets.")
            return

        print("-" * 92)
        print(f"{'Category':<16} {'Month':<8} {'Limit':>14} {'Spent':>14} {'Remaining':>14} {'Util%':>8} {'Status'}")
        print("-" * 92)
        for st in statuses:
            print(
                f"{st['category']:<16} {st['year']}-{st['month']:02d} "
                f"{st['formatted_limit']:>14} {st['formatted_spent']:>14} {st['formatted_remaining']:>14} "
                f"{st['percentage_utilized']:>7.1f}%  {st['status_text']}"
            )
        print("-" * 92)

    # ==================== INVESTMENT COMMANDS ====================

    def cmd_manage_investments(self) -> None:
        print("\n--- MANAGE SIMULATED INVESTMENTS ---")
        print(self.investment_mgr.DISCLAIMER)
        print("\n1. View Holdings")
        print("2. Add / Buy Holding")
        print("3. Sell / Reduce Holding")
        print("4. Update Current Asset Price")
        print("5. Remove Holding")
        sub = prompt_string("Select option", default="1")

        if sub == "1":
            holdings = self.investment_mgr.list_investments()
            if not holdings:
                print("No investment holdings recorded.")
                return
            print("-" * 90)
            print(f"{'ID':<10} {'Asset Name':<28} {'Type':<12} {'Qty':>8} {'Buy Price':>12} {'Curr Price':>12} {'P&L %':>10}")
            print("-" * 90)
            for inv in holdings:
                print(
                    f"{inv.investment_id:<10} {truncate_string(inv.asset_name, 26):<28} {inv.asset_type:<12} "
                    f"{inv.quantity:>8.2f} {format_inr(inv.purchase_price):>12} {format_inr(inv.current_price):>12} "
                    f"{inv.percentage_return:>+9.2f}%"
                )
            print("-" * 90)

        elif sub == "2":
            name = prompt_string("Asset Name (e.g. Tata Consultancy Services or Nifty 50 ETF)")
            asset_type = prompt_string("Asset Type (Equity/Mutual Fund/Gold/ETF/FD)", default="Equity")
            qty = prompt_float("Quantity (Units / Shares)")
            price = prompt_float("Purchase / Entry Price (INR)")
            curr_price = prompt_float("Current Estimated Price (INR)", allow_zero=True)
            inv = self.investment_mgr.add_investment(name, asset_type, qty, price, curr_price)
            print(f"[Success] Investment recorded: {inv}")

        elif sub == "3":
            inv_id = prompt_string("Enter Investment ID to sell shares from")
            qty = prompt_float("Quantity to sell")
            updated = self.investment_mgr.sell_shares(inv_id, qty)
            print(f"[Success] Holding updated: {updated}")

        elif sub == "4":
            inv_id = prompt_string("Enter Investment ID")
            new_p = prompt_float("New current estimated market price (INR)")
            updated = self.investment_mgr.update_price(inv_id, new_p)
            print(f"[Success] Price updated: {updated}")

        elif sub == "5":
            inv_id = prompt_string("Enter Investment ID to remove")
            if self.investment_mgr.remove_investment(inv_id):
                print(f"[Success] Holding {inv_id} removed.")
            else:
                print(f"Holding {inv_id} not found.")

    def cmd_view_portfolio_summary(self) -> None:
        print("\n--- SIMULATED PORTFOLIO SUMMARY ---")
        summary = self.investment_mgr.calculate_portfolio_totals()
        print(f"Total Holdings:          {summary['total_holdings_count']}")
        print(f"Total Capital Invested:  {summary['formatted_invested']}")
        print(f"Current Estimated Value: {summary['formatted_value']}")
        print(f"Total Profit / Loss:     {summary['formatted_pnl']} ({summary['total_return_percentage']:+.2f}%)")

        print("\nAsset Class Allocation:")
        print("-" * 45)
        for a_type, data in summary["asset_type_allocation"].items():
            print(f"  {a_type:<18}: {format_inr(data['value']):>14} ({data['percentage']:>5.1f}%)")
        print("-" * 45)
        print(f"\nNotice: {summary['disclaimer']}")

    # ==================== ANALYTICS & ML COMMANDS ====================

    def cmd_financial_summary(self) -> None:
        print("\n--- FINANCIAL SUMMARY (pandas & NumPy) ---")
        txs = self.finance.list_transactions()
        analytics = FinancialAnalytics(txs)
        summary = analytics.generate_summary()

        print(f"Total Transactions:      {summary['total_transactions']} (Income: {summary['income_count']}, Expenses: {summary['expense_count']})")
        print(f"Total Income:            {summary['formatted_income']}")
        print(f"Total Expenses:          {summary['formatted_expenses']}")
        print(f"Net Savings:             {summary['formatted_savings']}")
        print(f"Savings Rate:            {summary['savings_rate_pct']:.2f}%")
        print(f"Average Expense:         {format_inr(summary['avg_expense'])}")
        print(f"Median Expense:          {format_inr(summary['median_expense'])}")
        print(f"Expense Std Deviation:   {format_inr(summary['std_expense'])}")
        print(f"Highest Spending Cat:    {summary['highest_spending_category']}")

        if summary["largest_expense"]:
            le = summary["largest_expense"]
            print(f"Largest Single Expense:  {le['formatted_amount']} on {le['date']} ('{le['description']}')")
        if summary["highest_spending_day"]:
            hd = summary["highest_spending_day"]
            print(f"Highest Spending Day:    {hd['formatted_amount']} on {hd['date']}")

    def cmd_monthly_analysis(self) -> None:
        print("\n--- MONTHLY SPENDING ANALYSIS ---")
        txs = self.finance.list_transactions()
        analytics = FinancialAnalytics(txs)
        monthly_df = analytics.monthly_spending_analysis()

        if monthly_df.empty:
            print("No monthly transactions to display.")
            return

        print("-" * 88)
        print(f"{'Month':<10} {'Income':>14} {'Expenses':>14} {'Savings':>14} {'Rate%':>8} {'MoM Change':>14} {'MoM %':>8}")
        print("-" * 88)
        for _, r in monthly_df.iterrows():
            print(
                f"{r['year_month']:<10} {format_inr(r['income']):>14} {format_inr(r['expenses']):>14} "
                f"{format_inr(r['net_savings']):>14} {r['savings_rate_pct']:>7.1f}% "
                f"{format_inr(r['mom_expense_change']):>14} {r['mom_expense_pct_change']:>+7.1f}%"
            )
        print("-" * 88)

    def cmd_category_analysis(self) -> None:
        print("\n--- CATEGORY BREAKDOWN ---")
        txs = self.finance.list_transactions()
        analytics = FinancialAnalytics(txs)
        cat_df = analytics.category_breakdown()

        if cat_df.empty:
            print("No expense records available for category analysis.")
            return

        print("-" * 72)
        print(f"{'Category':<18} {'Total (INR)':>16} {'% of Expenses':>14} {'Count':>8} {'Average':>14}")
        print("-" * 72)
        for _, r in cat_df.iterrows():
            print(
                f"{r['category']:<18} {format_inr(r['total_amount']):>16} "
                f"{r['percentage']:>13.1f}% {int(r['count']):>8} {format_inr(r['average_amount']):>14}"
            )
        print("-" * 72)

    def cmd_detect_anomalies(self) -> None:
        print("\n--- DETECT UNUSUAL EXPENSES (STATISTICAL Z-SCORE) ---")
        print("Note: Detected anomalies represent statistically unusual spending within a category, NOT fraud.")
        thresh = prompt_string("Z-Score threshold (e.g. 2.0 standard deviations)", default="2.0")
        z_thresh = float(thresh) if thresh else 2.0

        txs = self.finance.list_transactions()
        analytics = FinancialAnalytics(txs)
        anomalies = analytics.detect_anomalies(z_score_threshold=z_thresh)

        if not anomalies:
            print(f"\nNo statistical anomalies detected above Z-Score >= {z_thresh}.")
            return

        print(f"\nFound {len(anomalies)} statistically unusual expense transaction(s):")
        print("-" * 96)
        print(f"{'ID':<10} {'Date':<12} {'Category':<14} {'Amount':>14} {'Z-Score':>8} {'Explanation'}")
        print("-" * 96)
        for a in anomalies:
            print(
                f"{a['transaction_id']:<10} {a['date']:<12} {a['category']:<14} "
                f"{a['formatted_amount']:>14} {a['z_score']:>7.2f}σ  {truncate_string(a['explanation'], 36)}"
            )
        print("-" * 96)

    def cmd_top_expenses(self) -> None:
        print("\n--- TOP EXPENSES (HEAP / PRIORITY QUEUE) ---")
        limit_str = prompt_string("Number of top expenses to view", default="5")
        limit = int(limit_str) if limit_str.isdigit() else 5

        top_exp = self.finance.get_top_n_expenses(limit=limit)
        if not top_exp:
            print("No expense transactions recorded.")
            return

        print(f"\nTop {len(top_exp)} largest expense transactions (O(N log K) min-heap retrieval):")
        print("-" * 84)
        print(f"{'Rank':<6} {'ID':<10} {'Date':<12} {'Amount':>14} {'Category':<14} {'Description'}")
        print("-" * 84)
        for rank, tx in enumerate(top_exp, start=1):
            print(f"#{rank:<5} {tx.transaction_id:<10} {tx.transaction_date:<12} {format_inr(tx.amount):>14} {tx.category:<14} {tx.description}")
        print("-" * 84)

    def cmd_predict_spending(self) -> None:
        print("\n--- PREDICT NEXT MONTH'S SPENDING (LINEAR REGRESSION) ---")
        txs = self.finance.list_transactions()
        try:
            res = self.predictor.predict_next_month(txs)
        except NotEnoughDataError as e:
            print(f"\n[Insufficient Data] {e}")
            return

        print(f"\nForecast Target Month:     {res['target_month']}")
        print(f"Predicted Spending:        {res['formatted_predicted']}")
        print(f"Monthly Spending Trend:    {res['trend_direction'].upper()} (Slope: {format_inr(res['slope_per_month'])} / month)")
        print(f"Historical Months Fitted:  {res['historical_months_count']}")
        print(f"Model In-Sample MAE:       {format_inr(res['in_sample_mae'])}")
        if res["backtest_mae"] is not None:
            print(f"Chronological Holdout MAE: {format_inr(res['backtest_mae'])}")
        print(f"Model R² Score:            {res['r2_score']:.4f}")
        print(f"\nNotice: {res['disclaimer']}")

    def cmd_auto_categorize(self) -> None:
        print("\n--- AUTO-CATEGORIZE TRANSACTION (TF-IDF & NAIVE BAYES) ---")
        desc = prompt_string("Enter transaction description (e.g., 'BigBasket monthly milk eggs order')")
        if not desc:
            return

        result = self.categorizer.predict(desc)
        print("\nNLP Classification Result:")
        print(f"  Predicted Category: {result['category']}")
        print(f"  Confidence Score:   {result['confidence']:.1%}")
        print(f"  Threshold Check:    {'CONFIDENT' if result['is_confident'] else 'LOW CONFIDENCE'}")
        print(f"  Note:               {result['note']}")

    def cmd_generate_charts(self) -> None:
        print("\n--- GENERATE FINANCIAL CHARTS (MATPLOTLIB) ---")
        txs = self.finance.list_transactions()
        invs = self.investment_mgr.list_investments()

        if not txs:
            print("No transactions available to generate charts.")
            return

        print("Generating aesthetic charts from actual application data...")
        chart_paths = self.visualizer.generate_all_charts(txs, invs)
        print("\nCharts generated in 'charts/' directory:")
        for name, p in chart_paths.items():
            if p:
                print(f"  ✓ {name:<24} -> {p}")
            else:
                print(f"  - {name:<24} -> (Skipped: insufficient data)")

    def cmd_load_demo_data(self) -> None:
        print("\n--- LOAD DEMO DATA ---")
        print("This will load the realistic 12-month sample dataset into your working database.")
        print("Original sample CSVs in 'data/sample_*.csv' will remain unchanged.")
        confirm = prompt_string("Proceed and overwrite current working data with demo data? (yes/no)", default="no")
        if confirm.lower() in ("yes", "y"):
            shutil.copyfile(self.base_dir / "sample_transactions.csv", self.base_dir / "transactions.csv")
            shutil.copyfile(self.base_dir / "sample_accounts.csv", self.base_dir / "accounts.csv")
            shutil.copyfile(self.base_dir / "sample_budgets.csv", self.base_dir / "budgets.csv")
            shutil.copyfile(self.base_dir / "sample_investments.csv", self.base_dir / "investments.csv")

            # Reload all services
            self.finance.load_data()
            self.budget_mgr.load()
            self.investment_mgr.load()
            print(f"[Success] Demo data loaded! Loaded {len(self.finance.list_transactions())} transactions.")
        else:
            print("Demo data load cancelled.")

    def cmd_export_report(self) -> None:
        print("\n--- EXPORT COMPREHENSIVE FINANCIAL REPORT ---")
        report_dir = Path("reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"financial_report_{date.today().isoformat()}.txt"

        txs = self.finance.list_transactions()
        invs = self.investment_mgr.list_investments()
        analytics = FinancialAnalytics(txs)
        summary = analytics.generate_summary()
        monthly = analytics.monthly_spending_analysis()
        budgets = self.budget_mgr.get_all_budget_statuses(txs)
        portfolio = self.investment_mgr.calculate_portfolio_totals()

        lines = [
            "=" * 70,
            f"       FINANCIAL HEALTH & INVESTMENT ADVISORY REPORT",
            f"                  Generated: {date.today().isoformat()}",
            "=" * 70,
            "",
            "1. FINANCIAL OVERVIEW",
            "-" * 40,
            f"Total Income:           {summary['formatted_income']}",
            f"Total Expenses:         {summary['formatted_expenses']}",
            f"Net Savings:            {summary['formatted_savings']}",
            f"Savings Rate:           {summary['savings_rate_pct']:.2f}%",
            f"Total Transactions:     {summary['total_transactions']}",
            f"Average Expense:        {format_inr(summary['avg_expense'])}",
            f"Highest Spending Cat:   {summary['highest_spending_category']}",
            "",
            "2. ACCOUNTS & LIQUIDITY",
            "-" * 40,
        ]

        for acc in self.finance.list_accounts():
            lines.append(f"  * {acc.account_name:<28} [{acc.account_type}]: {format_inr(acc.current_balance)}")
        lines.append(f"Total Liquid Cash:      {format_inr(self.finance.calculate_total_liquidity())}")
        lines.append(f"Total Net Worth:        {format_inr(self.finance.calculate_net_worth())}")

        lines.extend([
            "",
            "3. SIMULATED PORTFOLIO VALUATION",
            "-" * 40,
            f"Total Capital Invested: {portfolio['formatted_invested']}",
            f"Current Value Estimate: {portfolio['formatted_value']}",
            f"Unrealized P&L:         {portfolio['formatted_pnl']} ({portfolio['total_return_percentage']:+.2f}%)",
            "",
            "4. RECENT MONTHLY PERFORMANCE",
            "-" * 40,
        ])

        for _, r in monthly.tail(6).iterrows():
            lines.append(
                f"  * {r['year_month']}: Income={format_inr(r['income'])}, "
                f"Expenses={format_inr(r['expenses'])}, Savings={format_inr(r['net_savings'])}"
            )

        lines.extend([
            "",
            "=" * 70,
            "DISCLAIMER: Educational simulation tool only. Not certified financial advice.",
            "=" * 70,
        ])

        report_content = "\n".join(lines)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"[Success] Comprehensive report exported to: {report_file}")
        print("\nReport Preview:")
        print("-" * 60)
        print(report_content[:500] + "\n... [truncated] ...")


def main() -> None:
    """CLI argument parser and entry function."""
    parser = argparse.ArgumentParser(
        description="Smart Personal Finance & Investment Advisor — Educational tracking and analytics tool."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode using realistic 12-month sample dataset without modifying sample files.",
    )
    args = parser.parse_args()

    cli = FinancialAdvisorCLI(demo_mode=args.demo)
    cli.run()


if __name__ == "__main__":
    main()
