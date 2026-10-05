"""Automated transaction categorization using TF-IDF and Multinomial Naive Bayes."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from models.exceptions import NotEnoughDataError
from models.transaction import Transaction

# Documented curated baseline training dataset for common transaction descriptions
DEFAULT_TRAINING_CORPUS: list[tuple[str, str]] = [
    # Food
    ("Swiggy food order dinner", "Food"),
    ("Zomato lunch delivery biryani", "Food"),
    ("Dominos pizza party", "Food"),
    ("Starbucks coffee and snacks", "Food"),
    ("McDonalds burger meal", "Food"),
    ("Haldirams sweets and snacks", "Food"),
    ("Cafe Coffee Day beverage", "Food"),
    ("Subway sandwich takeaway", "Food"),
    # Groceries
    ("BigBasket fresh vegetables fruits", "Groceries"),
    ("Blinkit grocery delivery milk bread", "Groceries"),
    ("Zepto quick 10 min groceries", "Groceries"),
    ("DMart monthly supermarket provisions", "Groceries"),
    ("Nature Basket organic grocery store", "Groceries"),
    ("Mother Dairy milk and curd", "Groceries"),
    ("Local vegetable vendor and fruits", "Groceries"),
    # Transport
    ("Uber cab ride to office", "Transport"),
    ("Ola auto ride to metro station", "Transport"),
    ("Indian Oil petrol fuel pump", "Transport"),
    ("Bharat Petroleum diesel filling", "Transport"),
    ("Metro rail smart card recharge", "Transport"),
    ("Fastag highway toll deduction", "Transport"),
    ("Bus ticket redBus booking", "Transport"),
    ("Flight ticket booking Indigo airlines", "Transport"),
    # Housing
    ("Monthly apartment flat rent payment", "Housing"),
    ("Society maintenance maintenance charges", "Housing"),
    ("House cleaning deep clean service", "Housing"),
    ("Plumber repair plumbing bathroom", "Housing"),
    ("House painting repair carpenter work", "Housing"),
    # Utilities
    ("Electricity bill payment BESCOM", "Utilities"),
    ("Airtel broadband wifi internet bill", "Utilities"),
    ("Jio mobile prepaid recharge plan", "Utilities"),
    ("Piped gas natural gas IGL bill", "Utilities"),
    ("Water supply tanker municipal bill", "Utilities"),
    ("Tata Play DTH television cable recharge", "Utilities"),
    # Shopping
    ("Amazon online retail shopping clothes", "Shopping"),
    ("Flipkart electronics gadget purchase", "Shopping"),
    ("Myntra apparel fashion shoes order", "Shopping"),
    ("Zara clothing retail store shopping", "Shopping"),
    ("Ikea home decor furniture shopping", "Shopping"),
    ("Croma electronic appliances headphones", "Shopping"),
    # Entertainment
    ("BookMyShow cinema movie tickets PVR", "Entertainment"),
    ("Netflix monthly streaming subscription", "Entertainment"),
    ("Spotify premium music subscription", "Entertainment"),
    ("Hotstar Disney annual subscription", "Entertainment"),
    ("Gaming console steam game purchase", "Entertainment"),
    ("Concert live show event tickets", "Entertainment"),
    # Healthcare
    ("Apollo pharmacy medicines prescription", "Healthcare"),
    ("Doctor consultation fee clinic visit", "Healthcare"),
    ("Diagnostic lab blood test Metropolis", "Healthcare"),
    ("Dental cleaning dentist treatment", "Healthcare"),
    ("Health insurance mediclaim premium", "Healthcare"),
    ("Hospital emergency medical expenses", "Healthcare"),
    # Education
    ("Udemy online course certification", "Education"),
    ("College tuition semester fees", "Education"),
    ("Coursera learning professional certificate", "Education"),
    ("School books stationery notebook uniform", "Education"),
    ("Exam registration application fee", "Education"),
    # Salary
    ("Monthly salary credit company payroll", "Salary"),
    ("Direct deposit corporate salary transfer", "Salary"),
    ("Annual performance bonus payout", "Salary"),
    ("Freelance consulting client invoice payment", "Salary"),
]


class TransactionCategorizer:
    """Predicts expense/income categories from transaction descriptions using NLP pipeline."""

    def __init__(self, confidence_threshold: float = 0.30) -> None:
        self.confidence_threshold = confidence_threshold
        self.pipeline: Pipeline | None = None
        self._categories: list[str] = []
        self._is_trained: bool = False

        # Train on default baseline dataset
        self.train_default_model()

    @property
    def is_trained(self) -> bool:
        """Check if pipeline has been fitted."""
        return self._is_trained

    def _create_pipeline(self) -> Pipeline:
        """Create fresh TF-IDF + Multinomial Naive Bayes pipeline."""
        return Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        lowercase=True,
                        ngram_range=(1, 2),
                        sublinear_tf=True,
                        token_pattern=r"(?u)\b\w+\b",
                    ),
                ),
                ("classifier", MultinomialNB(alpha=0.1)),
            ]
        )

    def train_default_model(self) -> None:
        """Train pipeline using curated baseline corpus."""
        descriptions, categories = zip(*DEFAULT_TRAINING_CORPUS)
        self.train(list(descriptions), list(categories))

    def train(self, descriptions: list[str], categories: list[str]) -> None:
        """Train or retrain classifier on labeled description-category pairs."""
        if not descriptions or not categories or len(descriptions) != len(categories):
            raise NotEnoughDataError(
                required_records=2,
                actual_records=len(descriptions),
                context="Categorizer Training",
            )

        unique_cats = sorted(set(categories))
        if len(unique_cats) < 2:
            raise NotEnoughDataError(
                required_records=2,
                actual_records=len(unique_cats),
                context="Categorizer Training (Unique Categories)",
            )

        self.pipeline = self._create_pipeline()
        self.pipeline.fit(descriptions, categories)
        self._categories = list(self.pipeline.classes_)
        self._is_trained = True

    def train_from_transactions(self, transactions: list[Transaction]) -> None:
        """Fine-tune or retrain model using labeled application transactions."""
        labeled = [(tx.description, tx.category) for tx in transactions if tx.description.strip()]
        if len(labeled) < 5:
            # Not enough user records; keep baseline
            return

        # Combine baseline with historical transactions
        base_descs, base_cats = zip(*DEFAULT_TRAINING_CORPUS)
        combined_descs = list(base_descs) + [d for d, _ in labeled]
        combined_cats = list(base_cats) + [c for _, c in labeled]

        self.train(combined_descs, combined_cats)

    def predict(self, description: str) -> dict[str, Any]:
        """Predict category for a transaction description.

        Returns:
            Dictionary with predicted category, confidence score, and threshold evaluation.
        """
        if not description or not description.strip():
            return {
                "category": "Other",
                "confidence": 0.0,
                "is_confident": False,
                "note": "Empty description provided; defaulted to 'Other'.",
            }

        if not self._is_trained or not self.pipeline:
            return {
                "category": "Other",
                "confidence": 0.0,
                "is_confident": False,
                "note": "Model not trained yet; defaulted to 'Other'.",
            }

        cleaned_text = description.strip()
        probabilities = self.pipeline.predict_proba([cleaned_text])[0]
        max_idx = int(np.argmax(probabilities))
        confidence = float(probabilities[max_idx])
        pred_category = self.pipeline.classes_[max_idx]

        if confidence < self.confidence_threshold:
            return {
                "category": "Other",
                "predicted_candidate": str(pred_category),
                "confidence": round(confidence, 3),
                "threshold": self.confidence_threshold,
                "is_confident": False,
                "note": (
                    f"Low confidence ({confidence:.1%}) below threshold {self.confidence_threshold:.1%}. "
                    f"Suggested candidate '{pred_category}', defaulted to 'Other'."
                ),
            }

        return {
            "category": str(pred_category),
            "confidence": round(confidence, 3),
            "threshold": self.confidence_threshold,
            "is_confident": True,
            "note": f"Categorized with {confidence:.1%} confidence.",
        }
