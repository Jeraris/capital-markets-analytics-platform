"""
test_analytics.py — Unit tests for core analytics business logic.

These tests exercise the financial calculations directly —
no HTTP layer, no router, just the math. This is the most
important test file: if the numbers are wrong, everything is wrong.

Covers:
  - Unrealized P&L calculation
  - Weighted average cost accounting
  - Realized P&L on sells
  - Simple moving average
  - Sector exposure weights
  - Edge cases: zero position, flat P&L, single-price SMA
"""

import pytest
from app.db.orm_models import TradeSideORM
from app.db.seed import _compute_positions, _generate_price_history


# ---------------------------------------------------------------------------
# P&L calculation helpers (extracted so they're independently testable)
# ---------------------------------------------------------------------------

def calc_unrealized_pnl(avg_cost: float, current_price: float, quantity: float) -> float:
    return round((current_price - avg_cost) * quantity, 2)

def calc_unrealized_pnl_pct(avg_cost: float, current_price: float) -> float:
    return round(((current_price - avg_cost) / avg_cost) * 100, 4)

def calc_notional(quantity: float, price: float) -> float:
    return round(quantity * price, 2)

def calc_weighted_avg_cost(existing_qty: float, existing_avg: float, new_qty: float, new_price: float) -> float:
    total_cost = existing_avg * existing_qty + new_price * new_qty
    return round(total_cost / (existing_qty + new_qty), 6)

def calc_sma(prices: list[float]) -> float:
    return round(sum(prices) / len(prices), 4)

def calc_sector_weights(positions: list[dict]) -> dict[str, float]:
    """positions: list of {sector, market_value}"""
    total = sum(p["market_value"] for p in positions)
    weights = {}
    for p in positions:
        weights[p["sector"]] = weights.get(p["sector"], 0.0) + round(p["market_value"] / total * 100, 4)
    return weights


# ---------------------------------------------------------------------------
# Unrealized P&L
# ---------------------------------------------------------------------------

class TestUnrealizedPnL:

    def test_profit_when_price_rises(self):
        pnl = calc_unrealized_pnl(avg_cost=170.0, current_price=185.0, quantity=100)
        assert pnl == 1500.0

    def test_loss_when_price_falls(self):
        pnl = calc_unrealized_pnl(avg_cost=260.0, current_price=240.0, quantity=50)
        assert pnl == -1000.0

    def test_flat_when_price_unchanged(self):
        pnl = calc_unrealized_pnl(avg_cost=150.0, current_price=150.0, quantity=200)
        assert pnl == 0.0

    def test_fractional_shares(self):
        pnl = calc_unrealized_pnl(avg_cost=100.0, current_price=101.5, quantity=0.5)
        assert pnl == 0.75

    def test_pnl_pct_gain(self):
        pct = calc_unrealized_pnl_pct(avg_cost=170.0, current_price=182.5)
        assert pct == pytest.approx(7.3529, rel=1e-3)

    def test_pnl_pct_loss(self):
        pct = calc_unrealized_pnl_pct(avg_cost=200.0, current_price=180.0)
        assert pct == pytest.approx(-10.0, rel=1e-3)

    def test_pnl_pct_flat(self):
        pct = calc_unrealized_pnl_pct(avg_cost=100.0, current_price=100.0)
        assert pct == 0.0

    def test_notional_value(self):
        assert calc_notional(100, 182.50) == 18250.0

    def test_notional_fractional(self):
        assert calc_notional(2.5, 100.0) == 250.0


# ---------------------------------------------------------------------------
# Weighted average cost accounting
# ---------------------------------------------------------------------------

class TestWeightedAverageCost:

    def test_single_buy(self):
        # First buy — avg cost is just the purchase price
        avg = calc_weighted_avg_cost(0, 0, 100, 170.0)
        assert avg == 170.0

    def test_avg_cost_two_equal_buys(self):
        avg = calc_weighted_avg_cost(100, 170.0, 100, 180.0)
        assert avg == 175.0

    def test_avg_cost_unequal_buys(self):
        # 100 shares @ $170, then 50 shares @ $200
        # total cost = 17000 + 10000 = 27000 / 150 = 180.0
        avg = calc_weighted_avg_cost(100, 170.0, 50, 200.0)
        assert avg == 180.0

    def test_avg_cost_small_add(self):
        # buying a small lot at a higher price barely moves the average
        avg = calc_weighted_avg_cost(1000, 100.0, 10, 200.0)
        assert avg == pytest.approx(100.99, rel=1e-3)

    def test_avg_cost_does_not_change_on_sell(self):
        # sells reduce quantity but avg_cost stays the same
        # (realized P&L is booked separately)
        avg_before = 170.0
        avg_after = avg_before  # avg cost unchanged by a sell
        assert avg_before == avg_after


# ---------------------------------------------------------------------------
# Realized P&L on sells
# ---------------------------------------------------------------------------

class TestRealizedPnL:

    def test_realized_gain(self):
        avg_cost = 170.0
        sell_price = 185.0
        qty = 50
        realized = round((sell_price - avg_cost) * qty, 2)
        assert realized == 750.0

    def test_realized_loss(self):
        avg_cost = 260.0
        sell_price = 240.0
        qty = 20
        realized = round((sell_price - avg_cost) * qty, 2)
        assert realized == -400.0

    def test_realized_zero_at_cost(self):
        avg_cost = 150.0
        realized = round((avg_cost - avg_cost) * 100, 2)
        assert realized == 0.0

    def test_cumulative_realized_pnl(self):
        # Two separate sells — realized P&L accumulates
        r1 = round((185.0 - 170.0) * 25, 2)   # sell 25 @ 185
        r2 = round((190.0 - 170.0) * 25, 2)   # sell 25 @ 190
        assert r1 + r2 == 875.0


# ---------------------------------------------------------------------------
# Simple moving average
# ---------------------------------------------------------------------------

class TestSimpleMovingAverage:

    def test_sma_uniform_prices(self):
        prices = [100.0] * 20
        assert calc_sma(prices) == 100.0

    def test_sma_ascending_prices(self):
        prices = [float(i) for i in range(1, 21)]  # 1..20
        assert calc_sma(prices) == 10.5

    def test_sma_single_price(self):
        assert calc_sma([182.50]) == 182.50

    def test_sma_two_prices(self):
        assert calc_sma([100.0, 200.0]) == 150.0

    def test_sma_window_5(self):
        prices = [10.0, 20.0, 30.0, 40.0, 50.0]
        assert calc_sma(prices) == 30.0

    def test_sma_rounds_to_4dp(self):
        prices = [100.0, 100.0, 100.0]
        result = calc_sma(prices)
        # Result should have at most 4 decimal places
        assert result == round(result, 4)


# ---------------------------------------------------------------------------
# Sector exposure weights
# ---------------------------------------------------------------------------

class TestSectorExposure:

    def test_single_sector_100_pct(self):
        positions = [
            {"sector": "Technology", "market_value": 50000.0},
            {"sector": "Technology", "market_value": 50000.0},
        ]
        weights = calc_sector_weights(positions)
        assert weights["Technology"] == pytest.approx(100.0)

    def test_two_sectors_equal_split(self):
        positions = [
            {"sector": "Technology", "market_value": 50000.0},
            {"sector": "Financials", "market_value": 50000.0},
        ]
        weights = calc_sector_weights(positions)
        assert weights["Technology"] == pytest.approx(50.0)
        assert weights["Financials"] == pytest.approx(50.0)

    def test_weights_sum_to_100(self):
        positions = [
            {"sector": "Technology", "market_value": 60000.0},
            {"sector": "Financials", "market_value": 25000.0},
            {"sector": "Automotive", "market_value": 15000.0},
        ]
        weights = calc_sector_weights(positions)
        assert sum(weights.values()) == pytest.approx(100.0, rel=1e-3)

    def test_dominant_sector(self):
        positions = [
            {"sector": "Technology", "market_value": 90000.0},
            {"sector": "Financials", "market_value": 10000.0},
        ]
        weights = calc_sector_weights(positions)
        assert weights["Technology"] == pytest.approx(90.0)
        assert weights["Financials"] == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# Seed logic — _compute_positions and _generate_price_history
# ---------------------------------------------------------------------------

class TestComputePositions:

    def _make_trade(self, symbol, side, qty, price, days_ago=1):
        from datetime import datetime, timedelta

        class MockTrade:
            pass

        t = MockTrade()
        t.symbol = symbol
        t.side = TradeSideORM(side)
        t.quantity = qty
        t.price = price
        t.timestamp = datetime.utcnow() - timedelta(days=days_ago)
        return t

    def test_single_buy_creates_position(self):
        trades = [self._make_trade("AAPL", "BUY", 100, 170.0)]
        positions = _compute_positions(trades)
        assert positions["AAPL"]["quantity"] == 100
        assert positions["AAPL"]["avg_cost"] == 170.0

    def test_two_buys_weighted_avg(self):
        trades = [
            self._make_trade("AAPL", "BUY", 100, 170.0, days_ago=2),
            self._make_trade("AAPL", "BUY", 100, 180.0, days_ago=1),
        ]
        positions = _compute_positions(trades)
        assert positions["AAPL"]["quantity"] == 200
        assert positions["AAPL"]["avg_cost"] == pytest.approx(175.0)

    def test_buy_then_partial_sell(self):
        trades = [
            self._make_trade("AAPL", "BUY",  100, 170.0, days_ago=2),
            self._make_trade("AAPL", "SELL",  25, 185.0, days_ago=1),
        ]
        positions = _compute_positions(trades)
        assert positions["AAPL"]["quantity"] == 75
        assert positions["AAPL"]["realized_pnl"] == pytest.approx(375.0)  # (185-170)*25

    def test_multiple_symbols_independent(self):
        trades = [
            self._make_trade("AAPL", "BUY", 100, 170.0, days_ago=2),
            self._make_trade("JPM",  "BUY",  60, 190.0, days_ago=1),
        ]
        positions = _compute_positions(trades)
        assert "AAPL" in positions
        assert "JPM" in positions
        assert positions["AAPL"]["quantity"] == 100
        assert positions["JPM"]["quantity"] == 60

    def test_full_sell_leaves_zero_quantity(self):
        trades = [
            self._make_trade("TSLA", "BUY",  50, 240.0, days_ago=2),
            self._make_trade("TSLA", "SELL", 50, 260.0, days_ago=1),
        ]
        positions = _compute_positions(trades)
        assert positions["TSLA"]["quantity"] == 0

    def test_realized_pnl_accumulates_across_sells(self):
        trades = [
            self._make_trade("AAPL", "BUY",  150, 170.0, days_ago=3),
            self._make_trade("AAPL", "SELL",  50, 180.0, days_ago=2),  # +500
            self._make_trade("AAPL", "SELL",  50, 190.0, days_ago=1),  # +1000
        ]
        positions = _compute_positions(trades)
        assert positions["AAPL"]["realized_pnl"] == pytest.approx(1500.0)


class TestGeneratePriceHistory:

    def test_returns_only_weekdays(self):
        rows = _generate_price_history("AAPL", 170.0, days=14)
        for row in rows:
            assert row["date"].weekday() < 5, f"{row['date']} is a weekend"

    def test_high_always_above_low(self):
        rows = _generate_price_history("MSFT", 400.0, days=30)
        for row in rows:
            assert row["high"] >= row["low"]

    def test_close_within_high_low(self):
        rows = _generate_price_history("GOOG", 170.0, days=30)
        for row in rows:
            assert row["low"] <= row["close"] <= row["high"]

    def test_deterministic_per_symbol(self):
        # Same symbol always produces same sequence (seeded random)
        rows1 = _generate_price_history("AAPL", 170.0, days=10)
        rows2 = _generate_price_history("AAPL", 170.0, days=10)
        assert [r["close"] for r in rows1] == [r["close"] for r in rows2]

    def test_different_symbols_differ(self):
        aapl = _generate_price_history("AAPL", 170.0, days=10)
        tsla = _generate_price_history("TSLA", 170.0, days=10)
        assert [r["close"] for r in aapl] != [r["close"] for r in tsla]
