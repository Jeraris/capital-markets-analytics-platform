"""
db/orm_models.py — SQLAlchemy ORM table definitions.

Four tables that mirror a real (simplified) capital markets data model:
  - instruments   — reference data for each tradeable symbol
  - trades        — immutable ledger of every executed trade
  - positions     — current net holding per symbol (derived from trades)
  - market_prices — daily closing price history per symbol

Keeping ORM models in a separate file from Pydantic schemas is intentional:
ORM models describe the DB shape; Pydantic schemas describe the API contract.
They look similar but serve different purposes and evolve independently.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    Enum as SAEnum, ForeignKey, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class TradeSideORM(str, enum.Enum):
    BUY  = "BUY"
    SELL = "SELL"

class AssetClassORM(str, enum.Enum):
    EQUITY       = "EQUITY"
    FIXED_INCOME = "FIXED_INCOME"
    FX           = "FX"
    COMMODITY    = "COMMODITY"


# ---------------------------------------------------------------------------
# instruments — reference / static data
# ---------------------------------------------------------------------------

class Instrument(Base):
    __tablename__ = "instruments"

    id          = Column(Integer, primary_key=True, index=True)
    symbol      = Column(String(10), unique=True, nullable=False, index=True)
    name        = Column(String(100), nullable=False)
    sector      = Column(String(50), nullable=False)
    asset_class = Column(SAEnum(AssetClassORM), nullable=False)

    # back-references
    trades   = relationship("Trade",       back_populates="instrument")
    position = relationship("Position",    back_populates="instrument", uselist=False)
    prices   = relationship("MarketPrice", back_populates="instrument")

    def __repr__(self):
        return f"<Instrument {self.symbol}>"


# ---------------------------------------------------------------------------
# trades — immutable event ledger; never updated, only appended
# ---------------------------------------------------------------------------

class Trade(Base):
    __tablename__ = "trades"

    id            = Column(Integer, primary_key=True, index=True)
    symbol        = Column(String(10), ForeignKey("instruments.symbol"), nullable=False, index=True)
    side          = Column(SAEnum(TradeSideORM), nullable=False)
    quantity      = Column(Float, nullable=False)
    price         = Column(Float, nullable=False)
    notional      = Column(Float, nullable=False)   # stored for query efficiency
    timestamp     = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    instrument = relationship("Instrument", back_populates="trades")

    __table_args__ = (
        Index("ix_trades_symbol_timestamp", "symbol", "timestamp"),
    )

    def __repr__(self):
        return f"<Trade {self.side} {self.quantity} {self.symbol} @ {self.price}>"


# ---------------------------------------------------------------------------
# positions — net holding per symbol; updated on every trade
# ---------------------------------------------------------------------------

class Position(Base):
    __tablename__ = "positions"

    id           = Column(Integer, primary_key=True, index=True)
    symbol       = Column(String(10), ForeignKey("instruments.symbol"), unique=True, nullable=False)
    quantity     = Column(Float, nullable=False, default=0.0)
    avg_cost     = Column(Float, nullable=False, default=0.0)
    realized_pnl = Column(Float, nullable=False, default=0.0)
    updated_at   = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    instrument = relationship("Instrument", back_populates="position")

    def __repr__(self):
        return f"<Position {self.symbol} qty={self.quantity} avg={self.avg_cost}>"


# ---------------------------------------------------------------------------
# market_prices — daily OHLCV history per symbol
# ---------------------------------------------------------------------------

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id     = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), ForeignKey("instruments.symbol"), nullable=False, index=True)
    date   = Column(DateTime, nullable=False, index=True)
    open   = Column(Float, nullable=False)
    high   = Column(Float, nullable=False)
    low    = Column(Float, nullable=False)
    close  = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    instrument = relationship("Instrument", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_market_prices_symbol_date"),
        Index("ix_market_prices_symbol_date", "symbol", "date"),
    )

    def __repr__(self):
        return f"<MarketPrice {self.symbol} {self.date.date()} close={self.close}>"
