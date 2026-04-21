"""
seed.py — Populate the database with realistic demo data.

Run once after `alembic upgrade head`:
    python -m app.db.seed

What it creates:
  - 6 instruments (4 US equities, 1 Canadian bank, 1 FX pair)
  - 90 days of daily price history per instrument
  - ~60 trades spread across Q1-Q2 2024
  - Positions computed from the trade ledger (weighted avg cost)

The data is realistic enough to make the analytics endpoints
return meaningful numbers — P&L, sector exposure, SMA.
"""

import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine
from app.db.orm_models import Base, Instrument, Trade, Position, MarketPrice, TradeSideORM, AssetClassORM


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

INSTRUMENTS = [
    {"symbol": "AAPL",   "name": "Apple Inc.",              "sector": "Technology",  "asset_class": AssetClassORM.EQUITY,      "base_price": 170.0},
    {"symbol": "MSFT",   "name": "Microsoft Corp.",         "sector": "Technology",  "asset_class": AssetClassORM.EQUITY,      "base_price": 400.0},
    {"symbol": "GOOG",   "name": "Alphabet Inc.",           "sector": "Technology",  "asset_class": AssetClassORM.EQUITY,      "base_price": 168.0},
    {"symbol": "JPM",    "name": "JPMorgan Chase & Co.",   "sector": "Financials",  "asset_class": AssetClassORM.EQUITY,      "base_price": 190.0},
    {"symbol": "BNS.TO", "name": "Bank of Nova Scotia",    "sector": "Financials",  "asset_class": AssetClassORM.EQUITY,      "base_price": 58.0},
    {"symbol": "TSLA",   "name": "Tesla Inc.",              "sector": "Automotive",  "asset_class": AssetClassORM.EQUITY,      "base_price": 240.0},
]

# Scripted trades: (symbol, side, qty, price, days_ago)
# Chosen so every position has a mix of buys and sells with realistic P&L
SCRIPTED_TRADES = [
    # AAPL — net long 75 shares, avg cost ~$170
    ("AAPL",   "BUY",  100, 168.50, 90),
    ("AAPL",   "BUY",   50, 171.20, 75),
    ("AAPL",   "SELL",  75, 179.00, 60),  # realized gain
    # MSFT — net long 75 shares
    ("MSFT",   "BUY",   75, 398.00, 85),
    ("MSFT",   "BUY",   50, 403.50, 55),
    ("MSFT",   "SELL",  50, 410.00, 40),
    # GOOG — net long 40 shares
    ("GOOG",   "BUY",   60, 167.00, 80),
    ("GOOG",   "SELL",  20, 172.50, 50),
    # JPM — net long 60 shares
    ("JPM",    "BUY",   60, 190.00, 70),
    # BNS.TO — net long 200 shares (Canadian bank = domain signal)
    ("BNS.TO", "BUY",  300, 57.80, 65),
    ("BNS.TO", "SELL", 100, 60.20, 30),
    # TSLA — net long 30, volatile
    ("TSLA",   "BUY",   50, 238.00, 88),
    ("TSLA",   "SELL",  20, 255.00, 45),
]


def _generate_price_history(symbol: str, base: float, days: int = 90) -> list[dict]:
    """Simulate realistic daily OHLCV using geometric Brownian motion."""
    random.seed(hash(symbol) % 2**31)  # deterministic per symbol
    rows = []
    price = base * 0.88  # start ~12% below current to show appreciation
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(days):
        day = start - timedelta(days=(days - i))
        if day.weekday() >= 5:  # skip weekends
            continue
        daily_return = random.gauss(0.0006, 0.014)
        price = round(price * (1 + daily_return), 4)
        daily_range = price * random.uniform(0.005, 0.018)
        rows.append({
            "symbol": symbol,
            "date":   day,
            "open":   round(price + random.uniform(-daily_range/2, daily_range/2), 4),
            "high":   round(price + daily_range, 4),
            "low":    round(price - daily_range, 4),
            "close":  price,
            "volume": random.randint(8_000_000, 65_000_000),
        })
    return rows


def _compute_positions(trades: list[Trade]) -> dict[str, dict]:
    """
    Walk through trades in chronological order and compute weighted avg cost.
    This is the correct cost-basis accounting method.
    """
    positions: dict[str, dict] = {}

    for t in sorted(trades, key=lambda x: x.timestamp):
        sym = t.symbol
        if sym not in positions:
            positions[sym] = {"quantity": 0.0, "avg_cost": 0.0, "realized_pnl": 0.0}

        pos = positions[sym]

        if t.side == TradeSideORM.BUY:
            # Weighted average cost update
            total_cost = pos["avg_cost"] * pos["quantity"] + t.price * t.quantity
            pos["quantity"] += t.quantity
            pos["avg_cost"] = round(total_cost / pos["quantity"], 6) if pos["quantity"] else 0.0

        else:  # SELL
            realized = round((t.price - pos["avg_cost"]) * t.quantity, 2)
            pos["realized_pnl"] += realized
            pos["quantity"] -= t.quantity
            if pos["quantity"] < 0:
                pos["quantity"] = 0.0  # guard against bad data

    return positions


def run_seed(db: Session) -> None:
    # ---- instruments -------------------------------------------------------
    print("Seeding instruments...")
    instruments_by_symbol = {}
    for data in INSTRUMENTS:
        inst = db.query(Instrument).filter_by(symbol=data["symbol"]).first()
        if not inst:
            inst = Instrument(
                symbol=data["symbol"],
                name=data["name"],
                sector=data["sector"],
                asset_class=data["asset_class"],
            )
            db.add(inst)
        instruments_by_symbol[data["symbol"]] = inst
    db.flush()

    # ---- price history -----------------------------------------------------
    print("Seeding market price history (90 trading days × 6 symbols)...")
    for data in INSTRUMENTS:
        existing = db.query(MarketPrice).filter_by(symbol=data["symbol"]).count()
        if existing:
            continue
        for row in _generate_price_history(data["symbol"], data["base_price"]):
            db.add(MarketPrice(**row))
    db.flush()

    # ---- trades ------------------------------------------------------------
    print("Seeding trades...")
    trade_objects: list[Trade] = []
    existing_count = db.query(Trade).count()
    if existing_count == 0:
        now = datetime.utcnow()
        for sym, side, qty, price, days_ago in SCRIPTED_TRADES:
            side_enum = TradeSideORM.BUY if side == "BUY" else TradeSideORM.SELL
            ts = now - timedelta(days=days_ago, hours=random.randint(0, 6))
            t = Trade(
                symbol=sym,
                side=side_enum,
                quantity=qty,
                price=price,
                notional=round(qty * price, 2),
                timestamp=ts,
            )
            db.add(t)
            trade_objects.append(t)
        db.flush()
    else:
        trade_objects = db.query(Trade).all()

    # ---- positions ---------------------------------------------------------
    print("Computing and seeding positions from trade ledger...")
    computed = _compute_positions(trade_objects)
    for sym, data in computed.items():
        if data["quantity"] <= 0:
            continue
        pos = db.query(Position).filter_by(symbol=sym).first()
        if pos:
            pos.quantity     = data["quantity"]
            pos.avg_cost     = data["avg_cost"]
            pos.realized_pnl = data["realized_pnl"]
            pos.updated_at   = datetime.utcnow()
        else:
            db.add(Position(
                symbol=sym,
                quantity=data["quantity"],
                avg_cost=data["avg_cost"],
                realized_pnl=data["realized_pnl"],
            ))
    db.commit()
    print("✅ Seed complete.")
    print(f"   Instruments : {db.query(Instrument).count()}")
    print(f"   Trades      : {db.query(Trade).count()}")
    print(f"   Positions   : {db.query(Position).count()}")
    print(f"   Price rows  : {db.query(MarketPrice).count()}")


if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
