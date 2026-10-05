"""Unit tests for InvestmentManager simulated portfolio tracking and asset allocations."""

import pytest

from models.exceptions import InvestmentValidationError
from services.investment_manager import InvestmentManager
from services.storage import StorageService


@pytest.fixture
def inv_manager(tmp_path):
    storage = StorageService(base_data_dir=tmp_path)
    inv_file = tmp_path / "investments.csv"
    return InvestmentManager(storage_service=storage, investments_file=inv_file)


def test_add_and_accumulate_investment(inv_manager):
    # Add initial 10 units at 100
    inv = inv_manager.add_investment("Nifty Index", "Mutual Fund", 10.0, 100.0, 120.0)
    assert inv.quantity == 10.0
    assert inv.purchase_price == 100.0
    assert inv.current_estimated_value == 1200.0

    # Accumulate 10 more units at 150
    # Average price = (1000 + 1500) / 20 = 125
    updated = inv_manager.add_investment("Nifty Index", "Mutual Fund", 10.0, 150.0, 140.0)
    assert updated.quantity == 20.0
    assert updated.purchase_price == 125.0
    assert updated.current_price == 140.0
    assert len(inv_manager.list_investments()) == 1


def test_sell_shares_and_update_price(inv_manager):
    inv = inv_manager.add_investment("Infosys", "Equity", 50.0, 1400.0, 1600.0)
    # Sell 20 shares
    updated = inv_manager.sell_shares(inv.investment_id, 20.0)
    assert updated.quantity == 30.0

    # Update current market price
    price_updated = inv_manager.update_price(inv.investment_id, 1750.0)
    assert price_updated.current_price == 1750.0


def test_sell_excess_shares_error(inv_manager):
    inv = inv_manager.add_investment("HDFC Bank", "Equity", 10.0, 1500.0)
    with pytest.raises(InvestmentValidationError):
        inv_manager.sell_shares(inv.investment_id, 50.0)


def test_portfolio_totals_and_allocation(inv_manager):
    inv_manager.add_investment("Reliance", "Equity", 10.0, 2000.0, 2500.0)  # Invested 20k, Val 25k
    inv_manager.add_investment("Gold BeES", "Gold", 100.0, 50.0, 60.0)      # Invested 5k, Val 6k

    totals = inv_manager.calculate_portfolio_totals()
    assert totals["total_holdings_count"] == 2
    assert totals["total_invested"] == 25000.0
    assert totals["total_estimated_value"] == 31000.0
    assert totals["total_profit_loss"] == 6000.0
    assert totals["total_return_percentage"] == 24.0

    alloc = totals["asset_type_allocation"]
    assert "Equity" in alloc
    assert "Gold" in alloc
    # Equity percentage: 25000 / 31000 = ~80.65%
    assert 80.0 <= alloc["Equity"]["percentage"] <= 81.0
    assert totals["disclaimer"] is not None


def test_remove_investment(inv_manager):
    inv = inv_manager.add_investment("Wipro", "Equity", 100.0, 400.0)
    assert inv_manager.remove_investment(inv.investment_id) is True
    assert len(inv_manager.list_investments()) == 0
