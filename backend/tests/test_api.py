"""
test_api.py — End-to-end API tests using FastAPI's TestClient.

Every test hits a real route, goes through the router, and reads/writes
the in-memory SQLite test DB. No mocking — this tests the full stack
minus the network layer.

Covers:
  - Health check
  - Market data endpoints
  - Trade blotter (GET, POST, filters, validation)
  - Portfolio analytics (P&L, sector exposure, SMA)
  - Error cases: 404s, invalid payloads, insufficient position
"""

import pytest
from tests.conftest import seed_instruments, seed_price_history, seed_position


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthCheck:

    def test_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_returns_ok_status(self, client):
        r = client.get("/")
        assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------------

class TestMarketData:

    def test_all_market_data_empty_db(self, client):
        # No instruments seeded — should return empty list
        r = client.get("/market-data/")
        assert r.status_code == 200
        assert r.json() == []

    def test_all_market_data_with_instruments(self, client, db):
        seed_instruments(db)
        seed_price_history(db, "AAPL", [170.0, 175.0, 180.0])
        r = client.get("/market-data/")
        assert r.status_code == 200
        symbols = [item["symbol"] for item in r.json()]
        assert "AAPL" in symbols

    def test_single_symbol_returns_correct_price(self, client, db):
        seed_instruments(db)
        seed_price_history(db, "AAPL", [170.0, 175.0, 182.50])
        r = client.get("/market-data/AAPL")
        assert r.status_code == 200
        data = r.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 182.50  # latest close

    def test_single_symbol_change_computed(self, client, db):
        seed_instruments(db)
        seed_price_history(db, "AAPL", [170.0, 180.0])  # +10 = +5.88%
        r = client.get("/market-data/AAPL")
        assert r.status_code == 200
        data = r.json()
        assert data["change"] == pytest.approx(10.0)
        assert data["change_pct"] == pytest.approx(5.8824, rel=1e-3)

    def test_unknown_symbol_returns_404(self, client):
        r = client.get("/market-data/FAKE")
        assert r.status_code == 404

    def test_symbol_lookup_case_insensitive(self, client, db):
        seed_instruments(db)
        seed_price_history(db, "AAPL", [180.0])
        r = client.get("/market-data/aapl")
        assert r.status_code == 200
        assert r.json()["symbol"] == "AAPL"

    def test_price_history_returns_ohlcv(self, client, db):
        seed_instruments(db)
        closes = [170.0, 172.0, 175.0, 178.0, 180.0]
        seed_price_history(db, "AAPL", closes)
        r = client.get("/market-data/AAPL/history?days=5")
        assert r.status_code == 200
        data = r.json()
        assert data["symbol"] == "AAPL"
        assert len(data["history"]) == 5
        first = data["history"][0]
        assert all(k in first for k in ["date", "open", "high", "low", "close", "volume"])


# ---------------------------------------------------------------------------
# Trade blotter
# ---------------------------------------------------------------------------

class TestTrades:

    def test_empty_blotter_returns_list(self, client):
        r = client.get("/trades/")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_trade_returns_201(self, client, db):
        seed_instruments(db)
        r = client.post("/trades/", json={
            "symbol": "AAPL", "side": "BUY",
            "quantity": 100, "price": 170.0, "asset_class": "EQUITY"
        })
        assert r.status_code == 201

    def test_create_trade_fields(self, client, db):
        seed_instruments(db)
        r = client.post("/trades/", json={
            "symbol": "AAPL", "side": "BUY",
            "quantity": 50, "price": 180.0, "asset_class": "EQUITY"
        })
        data = r.json()
        assert data["symbol"] == "AAPL"
        assert data["side"] == "BUY"
        assert data["quantity"] == 50
        assert data["price"] == 180.0
        assert data["notional"] == 9000.0  # 50 * 180

    def test_create_trade_symbol_uppercased(self, client, db):
        seed_instruments(db)
        r = client.post("/trades/", json={
            "symbol": "aapl", "side": "BUY",
            "quantity": 10, "price": 170.0, "asset_class": "EQUITY"
        })
        assert r.status_code == 201
        assert r.json()["symbol"] == "AAPL"

    def test_create_trade_updates_position(self, client, db):
        seed_instruments(db)
        client.post("/trades/", json={
            "symbol": "AAPL", "side": "BUY",
            "quantity": 100, "price": 170.0, "asset_class": "EQUITY"
        })
        from app.db.orm_models import Position
        pos = db.query(Position).filter_by(symbol="AAPL").first()
        assert pos is not None
        assert pos.quantity == 100
        assert pos.avg_cost == 170.0

    def test_trade_appears_in_blotter(self, client, db):
        seed_instruments(db)
        client.post("/trades/", json={
            "symbol": "JPM", "side": "BUY",
            "quantity": 60, "price": 190.0, "asset_class": "EQUITY"
        })
        r = client.get("/trades/")
        assert r.status_code == 200
        symbols = [t["symbol"] for t in r.json()]
        assert "JPM" in symbols

    def test_filter_by_symbol(self, client, db):
        seed_instruments(db)
        client.post("/trades/", json={"symbol": "AAPL", "side": "BUY", "quantity": 10, "price": 170.0, "asset_class": "EQUITY"})
        client.post("/trades/", json={"symbol": "JPM",  "side": "BUY", "quantity": 10, "price": 190.0, "asset_class": "EQUITY"})
        r = client.get("/trades/?symbol=AAPL")
        assert all(t["symbol"] == "AAPL" for t in r.json())

    def test_filter_by_side(self, client, db):
        seed_instruments(db)
        client.post("/trades/", json={"symbol": "AAPL", "side": "BUY",  "quantity": 100, "price": 170.0, "asset_class": "EQUITY"})
        client.post("/trades/", json={"symbol": "AAPL", "side": "SELL", "quantity": 20,  "price": 180.0, "asset_class": "EQUITY"})
        r = client.get("/trades/?side=SELL")
        assert all(t["side"] == "SELL" for t in r.json())

    def test_get_trade_by_id(self, client, db):
        seed_instruments(db)
        created = client.post("/trades/", json={
            "symbol": "AAPL", "side": "BUY",
            "quantity": 10, "price": 170.0, "asset_class": "EQUITY"
        }).json()
        r = client.get(f"/trades/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_unknown_trade_id_returns_404(self, client):
        r = client.get("/trades/99999")
        assert r.status_code == 404

    def test_unknown_symbol_returns_422(self, client):
        r = client.post("/trades/", json={
            "symbol": "FAKE", "side": "BUY",
            "quantity": 10, "price": 100.0, "asset_class": "EQUITY"
        })
        assert r.status_code == 422

    def test_sell_without_position_returns_400(self, client, db):
        seed_instruments(db)
        r = client.post("/trades/", json={
            "symbol": "AAPL", "side": "SELL",
            "quantity": 10, "price": 180.0, "asset_class": "EQUITY"
        })
        assert r.status_code == 400

    def test_oversell_returns_400(self, client, db):
        seed_instruments(db)
        client.post("/trades/", json={"symbol": "AAPL", "side": "BUY",  "quantity": 10, "price": 170.0, "asset_class": "EQUITY"})
        r = client.post("/trades/",   json={"symbol": "AAPL", "side": "SELL", "quantity": 99, "price": 180.0, "asset_class": "EQUITY"})
        assert r.status_code == 400

    def test_negative_quantity_rejected(self, client):
        r = client.post("/trades/", json={
            "symbol": "AAPL", "side": "BUY",
            "quantity": -10, "price": 170.0, "asset_class": "EQUITY"
        })
        assert r.status_code == 422

    def test_zero_price_rejected(self, client):
        r = client.post("/trades/", json={
            "symbol": "AAPL", "side": "BUY",
            "quantity": 10, "price": 0, "asset_class": "EQUITY"
        })
        assert r.status_code == 422

    def test_invalid_side_rejected(self, client):
        r = client.post("/trades/", json={
            "symbol": "AAPL", "side": "HOLD",
            "quantity": 10, "price": 170.0, "asset_class": "EQUITY"
        })
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Portfolio analytics
# ---------------------------------------------------------------------------

class TestPortfolioPnL:

    def test_no_positions_returns_404(self, client):
        r = client.get("/portfolio/pnl")
        assert r.status_code == 404

    def test_pnl_positive_when_price_above_avg_cost(self, client, db):
        seed_instruments(db)
        seed_position(db, "AAPL", quantity=100, avg_cost=170.0)
        seed_price_history(db, "AAPL", [170.0, 175.0, 185.0])
        r = client.get("/portfolio/pnl")
        assert r.status_code == 200
        entry = next(p for p in r.json()["positions"] if p["symbol"] == "AAPL")
        assert entry["unrealized_pnl"] > 0

    def test_pnl_negative_when_price_below_avg_cost(self, client, db):
        seed_instruments(db)
        seed_position(db, "AAPL", quantity=100, avg_cost=200.0)
        seed_price_history(db, "AAPL", [200.0, 195.0, 180.0])
        r = client.get("/portfolio/pnl")
        entry = next(p for p in r.json()["positions"] if p["symbol"] == "AAPL")
        assert entry["unrealized_pnl"] < 0

    def test_pnl_correct_formula(self, client, db):
        seed_instruments(db)
        seed_position(db, "AAPL", quantity=100, avg_cost=170.0)
        seed_price_history(db, "AAPL", [170.0, 185.0])  # latest close = 185
        r = client.get("/portfolio/pnl")
        entry = next(p for p in r.json()["positions"] if p["symbol"] == "AAPL")
        assert entry["unrealized_pnl"] == pytest.approx(1500.0)  # (185-170)*100

    def test_total_pnl_is_sum_of_positions(self, client, db):
        seed_instruments(db)
        seed_position(db, "AAPL", quantity=100, avg_cost=170.0)
        seed_position(db, "JPM",  quantity=60,  avg_cost=190.0)
        seed_price_history(db, "AAPL", [185.0])
        seed_price_history(db, "JPM",  [200.0])
        r = client.get("/portfolio/pnl")
        data = r.json()
        position_sum = sum(p["unrealized_pnl"] for p in data["positions"])
        assert data["total_unrealized_pnl"] == pytest.approx(position_sum, rel=1e-3)

    def test_response_schema(self, client, db):
        seed_instruments(db)
        seed_position(db, "AAPL", quantity=10, avg_cost=170.0)
        seed_price_history(db, "AAPL", [180.0])
        r = client.get("/portfolio/pnl")
        data = r.json()
        assert "positions" in data
        assert "total_unrealized_pnl" in data
        assert "total_market_value" in data
        assert "as_of" in data


class TestSectorExposure:

    def test_no_positions_returns_404(self, client):
        r = client.get("/portfolio/exposure")
        assert r.status_code == 404

    def test_single_sector_100_pct(self, client, db):
        seed_instruments(db)
        seed_position(db, "AAPL", quantity=100, avg_cost=170.0)
        seed_price_history(db, "AAPL", [180.0])
        r = client.get("/portfolio/exposure")
        assert r.status_code == 200
        exposures = r.json()["exposures"]
        assert len(exposures) == 1
        assert exposures[0]["sector"] == "Technology"
        assert exposures[0]["weight_pct"] == pytest.approx(100.0)

    def test_weights_sum_to_100(self, client, db):
        seed_instruments(db)
        seed_position(db, "AAPL", quantity=100, avg_cost=170.0)
        seed_position(db, "JPM",  quantity=60,  avg_cost=190.0)
        seed_price_history(db, "AAPL", [180.0])
        seed_price_history(db, "JPM",  [200.0])
        r = client.get("/portfolio/exposure")
        weights = [e["weight_pct"] for e in r.json()["exposures"]]
        assert sum(weights) == pytest.approx(100.0, rel=1e-3)

    def test_sector_grouping(self, client, db):
        seed_instruments(db)
        # Both AAPL and TSLA are in different sectors
        seed_position(db, "AAPL", quantity=100, avg_cost=170.0)
        seed_position(db, "TSLA", quantity=50,  avg_cost=240.0)
        seed_price_history(db, "AAPL", [180.0])
        seed_price_history(db, "TSLA", [250.0])
        r = client.get("/portfolio/exposure")
        sectors = {e["sector"] for e in r.json()["exposures"]}
        assert "Technology" in sectors
        assert "Automotive" in sectors


class TestMovingAverage:

    def test_unknown_symbol_returns_404(self, client):
        r = client.get("/portfolio/moving-average/FAKE")
        assert r.status_code == 404

    def test_sma_correct_value(self, client, db):
        seed_instruments(db)
        closes = [100.0, 110.0, 120.0, 130.0, 140.0]  # SMA = 120.0
        seed_price_history(db, "AAPL", closes)
        r = client.get("/portfolio/moving-average/AAPL?window=5")
        assert r.status_code == 200
        assert r.json()["sma"] == pytest.approx(120.0)

    def test_sma_uses_correct_window(self, client, db):
        seed_instruments(db)
        seed_price_history(db, "AAPL", [100.0] * 30)
        r = client.get("/portfolio/moving-average/AAPL?window=20")
        assert r.json()["prices_used"] == 20

    def test_sma_response_schema(self, client, db):
        seed_instruments(db)
        seed_price_history(db, "AAPL", [150.0, 160.0, 170.0, 180.0, 190.0])
        r = client.get("/portfolio/moving-average/AAPL")
        data = r.json()
        assert all(k in data for k in ["symbol", "window", "sma", "prices_used", "as_of"])

    def test_window_below_minimum_rejected(self, client):
        r = client.get("/portfolio/moving-average/AAPL?window=2")
        assert r.status_code == 422

    def test_window_above_maximum_rejected(self, client):
        r = client.get("/portfolio/moving-average/AAPL?window=500")
        assert r.status_code == 422
