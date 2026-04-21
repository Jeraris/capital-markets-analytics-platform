"""
conftest.py — pytest fixtures shared across all test files.

Key design:
  - SQLite in-memory, but with a *named* file path so all connections
    share the same database within a test run (bare "sqlite://" gives
    each connection its own private DB — that's the bug we fix here).
  - Each test gets fresh tables via function-scoped create/drop.
  - FastAPI's dependency_overrides swaps get_db for the test session.
  - TestClient lets us call endpoints end-to-end without a live server.

The full suite runs with:
    pytest
No Docker, no network, no external services required.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.db.orm_models import (
    Instrument, Trade, Position, MarketPrice,
    TradeSideORM, AssetClassORM,
)

# ---------------------------------------------------------------------------
# Shared in-memory SQLite engine
# Named :memory: with same_thread=False + shared cache lets all sessions
# see the same tables within a single test process.
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///file::memory:?cache=shared&uri=true"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
)

# Enable foreign key enforcement in SQLite (off by default)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=False)
def db():
    """
    Fresh schema for every test — tables are created before and dropped after.
    Yields the session so tests can insert data directly.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    FastAPI TestClient with get_db overridden to use the test session.
    The db fixture is injected here so tables exist before the client starts.
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed helpers — call inside individual tests that need data
# ---------------------------------------------------------------------------

def seed_instruments(db) -> list[Instrument]:
    instruments = [
        Instrument(symbol="AAPL",   name="Apple Inc.",          sector="Technology", asset_class=AssetClassORM.EQUITY),
        Instrument(symbol="JPM",    name="JPMorgan Chase",      sector="Financials", asset_class=AssetClassORM.EQUITY),
        Instrument(symbol="BNS.TO", name="Bank of Nova Scotia", sector="Financials", asset_class=AssetClassORM.EQUITY),
        Instrument(symbol="TSLA",   name="Tesla Inc.",          sector="Automotive", asset_class=AssetClassORM.EQUITY),
    ]
    db.add_all(instruments)
    db.commit()
    return instruments


def seed_price_history(db, symbol: str, closes: list[float]):
    base_date = datetime(2024, 1, 1)
    for i, close in enumerate(closes):
        db.add(MarketPrice(
            symbol=symbol,
            date=base_date + timedelta(days=i),
            open=close * 0.99,
            high=close * 1.01,
            low=close * 0.98,
            close=close,
            volume=1_000_000,
        ))
    db.commit()


def seed_position(db, symbol: str, quantity: float, avg_cost: float, realized_pnl: float = 0.0) -> Position:
    pos = Position(
        symbol=symbol,
        quantity=quantity,
        avg_cost=avg_cost,
        realized_pnl=realized_pnl,
        updated_at=datetime.utcnow(),
    )
    db.add(pos)
    db.commit()
    return pos
