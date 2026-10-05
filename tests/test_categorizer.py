"""Unit tests for TransactionCategorizer using TF-IDF and Multinomial Naive Bayes."""

import pytest

from models.exceptions import NotEnoughDataError
from models.transaction import Transaction
from services.categorizer import TransactionCategorizer


def test_categorizer_default_predictions():
    categorizer = TransactionCategorizer()
    assert categorizer.is_trained is True

    # Test Food
    pred_food = categorizer.predict("Swiggy chicken biryani dinner delivery")
    assert pred_food["category"] == "Food"
    assert pred_food["is_confident"] is True

    # Test Transport
    pred_transport = categorizer.predict("Uber cab ride to tech park")
    assert pred_transport["category"] == "Transport"

    # Test Utilities
    pred_utility = categorizer.predict("BESCOM electricity bill online payment")
    assert pred_utility["category"] == "Utilities"

    # Test Groceries
    pred_groc = categorizer.predict("BigBasket fresh vegetables and fruits")
    assert pred_groc["category"] == "Groceries"


def test_categorizer_empty_and_unknown():
    categorizer = TransactionCategorizer(confidence_threshold=0.30)

    # Empty string
    empty_res = categorizer.predict("")
    assert empty_res["category"] == "Other"
    assert empty_res["confidence"] == 0.0

    # Completely alien string with nonsense tokens
    gibberish = categorizer.predict("xyzqwe 9999 zzzz")
    assert "category" in gibberish
    assert "confidence" in gibberish


def test_categorizer_insufficient_training_data():
    categorizer = TransactionCategorizer()
    # Attempting to train with only 1 class should raise NotEnoughDataError
    with pytest.raises(NotEnoughDataError):
        categorizer.train(["Coffee", "Pizza"], ["Food", "Food"])

    # Attempting to train with empty lists
    with pytest.raises(NotEnoughDataError):
        categorizer.train([], [])


def test_train_from_transactions():
    categorizer = TransactionCategorizer()
    txs = [
        Transaction(f"TX-{i}", 100.0, "Gadgets", f"Mechanical keyboard switch item {i}", "2026-01-01", "expense", "Bank")
        for i in range(10)
    ]
    # Retrain from transaction history
    categorizer.train_from_transactions(txs)
    res = categorizer.predict("mechanical keyboard keycaps")
    assert res["category"] == "Gadgets"
