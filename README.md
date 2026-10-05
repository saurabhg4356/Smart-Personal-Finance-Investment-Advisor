# Smart Personal Finance & Investment Advisor

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: pytest](https://img.shields.io/badge/tests-72%20passed-brightgreen.svg)](tests/)
[![Architecture: Clean](https://img.shields.io/badge/architecture-Clean%20%2F%20OOP-success.svg)](#architecture-overview)

A production-grade, educational personal finance management, investment simulation, and machine learning analytics tool written in modern Python (3.10+).

The application combines **Core Python OOP**, **Data Structures & Algorithms (Hash Maps, Heaps, Binary Search, LIFO Stacks)**, **atomic CSV persistence**, and **Machine Learning (scikit-learn Linear Regression for spending forecasting & TF-IDF + Multinomial Naive Bayes for automated transaction categorization)** into an intuitive, menu-driven CLI.

---

## Table of Contents

1. [Project Overview & Problem Statement](#project-overview--problem-statement)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Architecture Overview](#architecture-overview)
5. [Project Folder Structure](#project-folder-structure)
6. [Installation & Setup](#installation--setup)
   - [Windows (PowerShell)](#windows-powershell)
   - [macOS / Linux (Bash/Zsh)](#macos--linux-bashzsh)
7. [Running the Application](#running-the-application)
   - [Standard User Mode](#standard-user-mode)
   - [Interactive Demo Mode](#interactive-demo-mode)
   - [Automated Tests (pytest)](#automated-tests-pytest)
8. [Sample CLI Workflow](#sample-cli-workflow)
9. [Object-Oriented Programming (OOP) Implementation](#object-oriented-programming-oop-implementation)
10. [Custom Exception Hierarchy](#custom-exception-hierarchy)
11. [Data Structures & Algorithms (DSA)](#data-structures--algorithms-dsa)
12. [Data Analytics with pandas & NumPy](#data-analytics-with-pandas--numpy)
13. [Machine Learning Models](#machine-learning-models)
    - [Spending Prediction (Linear Regression)](#1-spending-prediction-linear-regression)
    - [NLP Transaction Categorization (TF-IDF + Naive Bayes)](#2-nlp-transaction-categorization-tf-idf--naive-bayes)
    - [Statistical Anomaly Detection (Z-Score)](#3-statistical-anomaly-detection-z-score)
14. [Storage & Persistence Architecture](#storage--persistence-architecture)
15. [Known Limitations & Privacy Disclaimer](#known-limitations--privacy-disclaimer)
16. [Future Enhancements](#future-enhancements)
17. [GitHub Repository Setup Instructions](#github-repository-setup-instructions)
18. [Resume-Ready Bullet Points](#resume-ready-bullet-points)
19. [Technical Interview Questions & Answers](#technical-interview-questions--answers)

---

## Project Overview & Problem Statement

### Problem Statement
Managing personal finances, budgeting across dynamic spending categories, evaluating simulated investment portfolios, and forecasting upcoming cash obligations usually requires complex spreadsheets or fragmented proprietary mobile apps. Many off-the-shelf tools fail to explain *how* calculations are performed, obscure user data in proprietary databases, lack offline reproducibility, or do not offer predictive insights.

### Solution
**Smart Personal Finance & Investment Advisor** is a self-contained, transparent, and modular command-line application built without heavyweight frameworks. It provides:
- Clean account tracking with strict mathematical consistency.
- Transparent category budgets with real-time overrun warnings.
- Simulated investment portfolio tracking with weighted average entry prices.
- Fast analytical queries using O(1) hash maps, O(N log K) heaps, and O(log N) binary search.
- Practical machine learning models trained on actual transaction data to categorize expenses and forecast future monthly spending.
- Zero external database setup: uses crash-safe atomic CSV persistence.

---

## Key Features

- **Transaction Management**: Record income and expenses with automatic date validation, Indian Rupee (`₹`) formatting, and precise `Decimal` monetary calculations.
- **Account Encapsulation & Polymorphism**:
  - `SavingsAccount`: Tracks liquidity and projects simple annual and monthly interest earnings.
  - `InvestmentAccount`: Encapsulates cash balances and dynamically aggregates simulated holdings valuations.
- **Budget Monitoring**: Set category spending limits per month/year, track real-time utilization percentages, and receive proactive budget threshold warnings.
- **Simulated Investment Portfolio**: Track asset holdings (Equities, Mutual Funds, Gold ETFs, FDs), simulate buying/selling, calculate weighted average entry costs, and evaluate unrealized P&L and ROI.
- **Core DSA Implementations**:
  - **Hash Maps**: O(1) transaction, account, and budget lookups.
  - **Min-Heap (`heapq`)**: O(N log K) retrieval of top expense transactions without full dataset sorting.
  - **Binary Search (`bisect`)**: O(log N + M) date-range transaction filtering on chronologically indexed records.
  - **Stack (LIFO)**: Multi-action `UndoStack` supporting complete state and balance rollbacks for ADD, DELETE, and EDIT operations.
- **Machine Learning & Analytics**:
  - **Linear Regression (`scikit-learn`)**: Predicts next month's aggregate spending with trend slopes, R² metrics, in-sample MAE, and chronological holdout evaluation.
  - **NLP Classifier (`TF-IDF + MultinomialNB`)**: Suggests transaction categories from natural-language descriptions with confidence scoring and fallback thresholds.
  - **Anomaly Detection**: Identifies statistical spending anomalies via category-aware Z-score modeling.
- **Matplotlib Visualizations**: Automatically renders 5 high-resolution charts in `charts/` (Category Donut, Income vs Expense Bars, Spending Trend, Actual vs Predicted Line, Portfolio Allocation).
- **Comprehensive Reporting**: One-click generation of detailed text financial health reports saved to `reports/`.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Language** | Python 3.10+ (tested on Python 3.13) |
| **Core Libraries** | `dataclasses`, `decimal`, `collections`, `heapq`, `bisect`, `csv`, `pathlib`, `tempfile`, `argparse` |
| **Data Analytics** | `pandas >= 2.0`, `numpy >= 1.24` |
| **Machine Learning** | `scikit-learn >= 1.3` (`LinearRegression`, `TfidfVectorizer`, `MultinomialNB`, `Pipeline`) |
| **Visualization** | `matplotlib >= 3.7` (Headless `Agg` backend) |
| **Testing** | `pytest >= 7.4` (72 comprehensive unit and integration tests) |

---

## Architecture Overview

The system strictly follows clean layered architecture principles. Models and business logic are entirely decoupled from CLI presentation and file I/O:

```mermaid
graph TD
    CLI[main.py CLI Presentation Layer] --> FM[FinanceManager]
    CLI --> BM[BudgetManager]
    CLI --> IM[InvestmentManager]
    CLI --> FA[FinancialAnalytics]
    CLI --> SP[SpendingPredictor]
    CLI --> TC[TransactionCategorizer]
    CLI --> FV[FinancialVisualizer]

    subgraph Service & DSA Layer
        FM --> DSA[services/dsa_utils.py<br/>Hash Maps | Heap | Bisect | UndoStack]
        FM --> SS[services/storage.py<br/>Atomic StorageService]
        BM --> SS
        IM --> SS
    end

    subgraph Analytics & ML Engines
        FA --> PANDAS[pandas & NumPy Engine]
        SP --> SKLR[scikit-learn Linear Regression]
        TC --> SKNLP[TF-IDF + MultinomialNB Pipeline]
        FV --> MPL[Matplotlib Figure Engine]
    end

    subgraph Domain Models
        FM --> M_TX[Transaction]
        FM --> M_ACC[Account / Savings / Investment]
        BM --> M_BG[Budget]
        IM --> M_INV[Investment]
    end

    subgraph Persistence Layer
        SS --> CSV_TX[(data/transactions.csv)]
        SS --> CSV_ACC[(data/accounts.csv)]
        SS --> CSV_BG[(data/budgets.csv)]
        SS --> CSV_INV[(data/investments.csv)]
    end
```

---

## Project Folder Structure

```text
smart-personal-finance-advisor/
│
├── main.py                     # CLI entry point, menu router, and argparser
├── requirements.txt            # Minimal, pinned external dependencies
├── pytest.ini                  # Pytest configuration (pythonpath, testpaths)
├── .gitignore                  # Git exclusions for venv, caches, charts, and user data
├── README.md                   # Comprehensive architectural documentation
├── LICENSE                     # MIT Open Source License
│
├── data/                       # CSV persistence directory
│   ├── .gitkeep
│   ├── sample_transactions.csv # 12 months (277 entries) reproducible sample data
│   ├── sample_accounts.csv     # Matched baseline accounts with exact math consistency
│   ├── sample_budgets.csv      # Category budgets across recent quarters
│   └── sample_investments.csv  # Diverse simulated holdings (Equities, MF, Gold, FD)
│
├── models/                     # Domain entity definitions
│   ├── __init__.py
│   ├── exceptions.py           # Custom exception hierarchy (FinanceAdvisorError)
│   ├── transaction.py          # Transaction dataclass with validation and serialization
│   ├── account.py              # Account base class, SavingsAccount, and InvestmentAccount
│   ├── budget.py               # Budget limit model and status calculator
│   └── investment.py           # Simulated portfolio holding model and valuation
│
├── services/                   # Business logic and computational services
│   ├── __init__.py
│   ├── storage.py              # Atomic CSV reader/writer with schema validation
│   ├── finance_manager.py      # Transaction & account coordinator with undo stack
│   ├── budget_manager.py       # Budget operations and spending alert evaluator
│   ├── investment_manager.py   # Portfolio valuation, share allocation, and P&L tracking
│   ├── dsa_utils.py            # Hash indexers, heapq top-K, bisect filter, UndoStack
│   ├── analytics.py            # pandas & NumPy metrics, MoM change, and Z-score anomalies
│   ├── predictor.py            # Linear Regression next-month expense forecaster
│   ├── categorizer.py          # TF-IDF + Naive Bayes NLP categorization pipeline
│   └── visualizer.py           # Matplotlib figures renderer (5 distinct charts)
│
├── utils/                      # Shared helper utilities
│   ├── __init__.py
│   ├── validators.py           # Input sanitization for amounts, dates, types, prices
│   └── helpers.py              # Indian Rupee (₹) number formatting and ISO parsers
│
├── tests/                      # Automated pytest test suite (72 tests)
│   ├── __init__.py
│   ├── test_models.py          # OOP creation, encapsulation, and polymorphism tests
│   ├── test_exceptions.py      # Exception hierarchy and custom message tests
│   ├── test_dsa.py             # Hash map, heapq, bisect, and UndoStack tests
│   ├── test_storage.py         # CSV atomic I/O, malformed headers, and edge cases
│   ├── test_manager.py         # Transaction lifecycle, balance updates, and undo tests
│   ├── test_budget.py          # Budget limit checks, overruns, and alert tests
│   ├── test_investment.py      # Asset valuation, share accumulation, and P&L tests
│   ├── test_analytics.py       # pandas summaries, MoM changes, and Z-score tests
│   ├── test_predictor.py       # Linear regression forecasting and holdout tests
│   ├── test_categorizer.py     # NLP classifications and confidence threshold tests
│   └── test_visualizer.py      # Matplotlib figure generation and file tests
│
└── charts/                     # Output directory for generated visualizations
    └── .gitkeep
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher installed. Verify with:
  ```bash
  python --version
  ```

### Windows (PowerShell)

1. Clone or navigate to the repository:
   ```powershell
   cd "Smart Personal Finance & Investment Advisor"
   ```

2. Create and activate a local virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

### macOS / Linux (Bash/Zsh)

1. Navigate to the repository:
   ```bash
   cd "Smart-Personal-Finance-Investment-Advisor"
   ```

2. Create and activate a local virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

### Standard User Mode
Starts with clean user storage files (`data/transactions.csv`, `data/accounts.csv`, etc.). On first launch, initializes standard starting accounts:
```bash
python main.py
```

### Interactive Demo Mode
Loads the full 12-month sample dataset (277 transactions, 3 accounts, 8 budgets, 7 investments) without modifying original `sample_*.csv` files:
```bash
python main.py --demo
```

### Automated Tests (pytest)
Execute the complete test suite:
```bash
python -m pytest -v
```
All 72 tests execute in under 5 seconds with zero external dependencies.

---

## Sample CLI Workflow

```text
================================================================
        SMART PERSONAL FINANCE & INVESTMENT ADVISOR [DEMO MODE]
================================================================

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
================================================================
Select an option (0-22): 18

--- PREDICT NEXT MONTH'S SPENDING (LINEAR REGRESSION) ---
Forecast Target Month:     2026-04
Predicted Spending:        ₹75,316.29
Monthly Spending Trend:    INCREASING (Slope: ₹2,418.15 / month)
Historical Months Fitted:  12
Model In-Sample MAE:       ₹8,124.50
Chronological Holdout MAE: ₹6,430.12
Model R² Score:            0.6420

Notice: STATISTICAL ESTIMATE DISCLAIMER: This projection is generated via a basic
linear regression model on historical monthly expenses for educational purposes.
```

---

## Object-Oriented Programming (OOP) Implementation

### 1. Encapsulation
- Balances in `Account` are private (`_current_balance`, `_opening_balance`).
- External code cannot mutate account balances directly. State mutations must occur via explicit, audited methods (`deposit()`, `withdraw()`, `apply_transaction()`, `reverse_transaction()`).
- Invariant enforcement: `withdraw()` verifies available funds before mutating state, raising `InsufficientFundsError` if funds are deficient.

### 2. Inheritance & Method Overriding
- Base class `Account` defines common banking properties and life-cycle methods.
- `SavingsAccount(Account)` extends the base account with an annual interest rate and implements `calculate_interest(months: int)`.
- `InvestmentAccount(Account)` integrates with simulated portfolio holdings.

### 3. Polymorphism
Both subclasses override `calculate_value()` and `generate_summary()`:
- `Account.calculate_value()` returns `_current_balance`.
- `InvestmentAccount.calculate_value()` returns `_current_balance + _portfolio_holdings_value`.
Calling code can iterate over a generic collection of `Account` instances and retrieve total asset valuations without type inspection.

### 4. Dataclasses & Value Objects
- `Transaction`, `Budget`, and `Investment` utilize `@dataclass(slots=True)` for memory efficiency, immutability of slot definitions, and readable string representations.

---

## Custom Exception Hierarchy

The application defines a structured hierarchy rooted at `FinanceAdvisorError` in `models/exceptions.py`. Every exception provides a context message and a user-actionable `resolution_hint`:

```text
FinanceAdvisorError (Base)
├── InvalidAmountError            # Raised on negative, zero, NaN, or non-numeric amounts
├── InvalidTransactionError       # Raised on invalid dates, unknown types, or malformed data
├── InsufficientFundsError        # Raised when an expense or withdrawal exceeds account balance
├── TransactionNotFoundError      # Raised when a transaction ID cannot be found in the index
├── AccountNotFoundError          # Raised when an account name does not exist
├── BudgetExceededError           # Raised when spending exceeds a category budget in strict mode
├── InvestmentValidationError     # Raised on invalid holding quantities or negative prices
├── StorageError                  # Raised on CSV header mismatches or I/O failures
└── NotEnoughDataError            # Raised when ML models lack historical data points
```

---

## Data Structures & Algorithms (DSA)

| Data Structure / Algorithm | File Location | Complexity | Practical Application |
|---|---|---|---|
| **Hash Map (`dict`)** | `services/dsa_utils.py` | Average **O(1)** lookup | Instant lookups for transactions by ID, accounts by name, and budgets by composite `(category, month, year)` key. |
| **Min-Heap (`heapq`)** | `services/dsa_utils.py` | **O(N log K)** time, **O(K)** space | `get_top_expenses()` extracts the top $K$ largest expenses without sorting all $N$ records (which would be $O(N \log N)$). Uses deterministic tie-breaking. |
| **Binary Search (`bisect`)** | `services/dsa_utils.py` | **O(log N + M)** time | `filter_transactions_by_date_range()` locates the start and end boundary indices of sorted dates in $O(\log N)$, slicing only the $M$ matching records. |
| **Stack (LIFO)** | `services/dsa_utils.py` | **O(1)** push/pop | `UndoStack` maintains reversible actions (`ADD`, `DELETE`, `EDIT`). Undoing reverts both the transaction records and updates the respective account balances. |

---

## Data Analytics with pandas & NumPy

The `FinancialAnalytics` class in `services/analytics.py` leverages pandas and NumPy for vectorization:
- **Financial Summary**: Aggregates total income, expenses, net savings, and computes **savings rate** ($\frac{\text{Net Savings}}{\text{Total Income}} \times 100$) with zero-division protection.
- **Dispersion Metrics**: Computes average, median, and unbiased sample standard deviation (`ddof=1`) of expenses using NumPy arrays.
- **Monthly Spending Analysis**: Groups data by `year_month` and unstacked transaction types to compute month-over-month (MoM) absolute differences (`.diff()`) and percentage changes (`.pct_change()`).
- **Category Pivot Table**: Produces cross-tabulated category matrices over time.

---

## Machine Learning Models

### 1. Spending Prediction (Linear Regression)
- **Model**: `sklearn.linear_model.LinearRegression` in `services/predictor.py`.
- **Target**: Next month's total household expense.
- **Features**: Continuous time step indices $X = [[0], [1], \dots, [T-1]]$ constructed from calendar months (missing months are filled with 0.0 expenses to maintain temporal fidelity).
- **Evaluation**:
  - In-sample Mean Absolute Error (MAE).
  - Out-of-sample Chronological Holdout MAE (trains on months $0 \dots T-2$, evaluates on month $T-1$ when $T \ge 4$).
  - Coefficient of determination ($R^2$).
- **Safety**: Predictions are bounded at $\ge 0.0$. Requires at least 3 months of data or raises `NotEnoughDataError`.

### 2. NLP Transaction Categorization (TF-IDF + Naive Bayes)
- **Pipeline**:
  1. `TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, lowercase=True)`
  2. `MultinomialNB(alpha=0.1)`
- **Behavior**: Predicts categories (Food, Transport, Groceries, Utilities, etc.) based on natural language descriptions (e.g., "Swiggy biryani dinner" $\rightarrow$ `Food`).
- **Confidence Threshold**: Computes predicted class probabilities via `predict_proba()`. If highest confidence is below threshold (default 30%), flags the prediction as low-confidence and defaults to `Other`.

### 3. Statistical Anomaly Detection (Z-Score)
- **Methodology**: Evaluates expense transactions against category spending distributions:
  $$Z = \frac{x - \mu_{\text{category}}}{\sigma_{\text{category}}}$$
- **Safeguards**:
  - When category samples $< 3$, defaults to global expense mean and standard deviation.
  - Zero-variance protection: skips evaluation if $\sigma \approx 0$.
  - Clearly explains that flagged items are statistical deviations (e.g. laptop purchase, hospital admission), not confirmed fraudulent transactions.

---

## Storage & Persistence Architecture

The `StorageService` in `services/storage.py` guarantees data integrity:
1. **Atomic File Replacement**: CSV writes occur first to a temporary file (`.filename_xyz.tmp`) located in the target directory, followed by `os.replace()`. This prevents corrupted or partial files during power loss or abrupt termination.
2. **Schema Validation**: Inspects incoming CSV column headers against expected schemas before parsing. Raises informative `StorageError` if columns are absent.
3. **Data Immutability**: Normal user operations write only to user data files (`transactions.csv`, `accounts.csv`, etc.). Sample files (`sample_*.csv`) remain strictly immutable.

---

## Known Limitations & Privacy Disclaimer

### Educational & Simulation Disclaimer
> [!IMPORTANT]
> This application is strictly an educational tool and portfolio simulation tracker. It does **NOT** connect to real bank accounts, brokerage APIs, or payment gateways. It does **NOT** execute real trades or provide certified financial, tax, or investment advice.

### Privacy Safeguards
- All operations run 100% locally.
- No network requests are made.
- No API keys, passwords, or personal financial credentials are required or stored.

### Known Limitations
- Linear regression models assume linear historical trends; external economic shocks or seasonal spikes may cause variance.
- Simulated investment prices require user updates or sample entry; live price feeds are intentionally omitted.

---

## Future Enhancements

- Multi-currency conversion support (e.g., USD, EUR to INR).
- Recurring transaction scheduling engine.
- Export to formatted Excel (`.xlsx`) workbooks and PDF statements.
- Machine learning categorization auto-training on every user-labeled entry.
- Polynomial / ARIMA time-series models for non-linear seasonal forecasting.

---

## GitHub Repository Setup Instructions

To push this repository to GitHub:

```bash
# 1. Initialize git (if not already initialized)
git init

# 2. Add remote repository
git remote add origin https://github.com/saurabhg4356/Smart-Personal-Finance-Investment-Advisor.git

# 3. Stage all files (respecting .gitignore)
git add .

# 4. Commit with clean conventional message
git commit -m "feat: complete initial release of Smart Personal Finance & Investment Advisor"

# 5. Set default branch to main and push
git branch -M main
git push -u origin main
```

---

## Resume-Ready Bullet Points

- **Architected and developed a full-featured Personal Finance & Investment Advisor in Python 3.10+** using clean OOP, encapsulation, custom exception hierarchies, and atomic CSV persistence.
- **Engineered high-performance querying utilities** utilizing Hash Maps for O(1) lookups, Python's `heapq` for O(N log K) top-expense retrieval, `bisect` for binary search date filtering, and a LIFO UndoStack for multi-operation state rollbacks.
- **Implemented end-to-end Machine Learning pipelines with scikit-learn**, deploying a Linear Regression forecaster with chronological holdout validation for monthly spending predictions, and a TF-IDF + Multinomial Naive Bayes pipeline for automated natural language expense categorization.

---

## Technical Interview Questions & Answers

### Q1: Why did you use `Decimal` instead of `float` for transaction amounts?
**Answer:** Binary floating-point numbers (`float`) in computers cannot precisely represent certain base-10 fractions (e.g., $0.1 + 0.2 = 0.30000000000000004$). Over thousands of transactions, cumulative rounding errors will corrupt account balances. Python's `decimal.Decimal` provides exact base-10 arithmetic, making it mandatory for monetary accounting. We convert to `float` only at the boundary when passing data to NumPy and scikit-learn for mathematical modeling.

### Q2: How does `heapq.nlargest` optimize finding top expenses compared to standard sorting?
**Answer:** Sorting the entire transaction array takes $O(N \log N)$ time. When we only need the top $K$ expenses (e.g., $K = 5$) from $N = 10,000$ transactions, `heapq.nlargest` maintains a min-heap of size $K$. Each element is compared against the heap root in $O(\log K)$ time, resulting in an optimal $O(N \log K)$ runtime and $O(K)$ auxiliary space.

### Q3: How does binary search date filtering work with `bisect`?
**Answer:** Transactions are maintained in chronological order by `transaction_date`. We use `bisect.bisect_left` to locate the first transaction with a date $\ge \text{start\_date}$ in $O(\log N)$, and `bisect.bisect_right` to locate the upper boundary for $\text{end\_date}$ in $O(\log N)$. Slicing the matching array takes $O(M)$ time, giving an overall query complexity of $O(\log N + M)$, which is significantly faster than a linear $O(N)$ scan.

### Q4: How is state consistency maintained when a transaction is edited or undone?
**Answer:** The `FinanceManager` coordinates transactions and accounts simultaneously. In `edit_transaction`, the old transaction effect is first reversed on the old account (`old_account.reverse_transaction`), then the new transaction is applied to the target account. If applying fails (e.g. insufficient funds), the old transaction is reapplied to ensure rollback. The `UndoStack` stores an `UndoAction` containing snapshots of the previous and updated transactions, allowing exact balance restoration upon undo.

### Q5: Why is evaluating Linear Regression with in-sample MAE misleading, and how did you address it?
**Answer:** In-sample MAE evaluates the model on the exact historical points it was trained on, which hides overfitting and provides an overly optimistic measure of predictive capability. In `SpendingPredictor`, we clearly label in-sample MAE as training fit, and when at least 4 months of data exist, we implement a chronological holdout split (training on months $0 \dots T-2$ and evaluating on the unseen month $T-1$) to compute an honest out-of-sample backtest MAE.

### Q6: How does the atomic file write strategy in `StorageService` prevent data corruption?
**Answer:** Directly writing to the target CSV file risks leaving corrupted or partial files if the program crashes or loses power mid-write. Our `StorageService` writes data to a temporary file (`.filename.tmp`) within the same directory. Once the write and flush succeed, it invokes `temp_file.replace(target_file)`. On POSIX and modern Windows systems, file replacement within the same filesystem is an atomic operation.
