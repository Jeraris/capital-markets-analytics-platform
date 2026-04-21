"""
schemas.py — Pydantic models for all API request/response contracts.

Why this matters: typed contracts mean FastAPI auto-validates every
request and auto-generates the /docs OpenAPI spec. No raw dicts anywhere.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    FIXED_INCOME = "FIXED_INCOME"
    FX = "FX"
    COMMODITY = "COMMODITY"


# ---------------------------------------------------------------------------
# Market data
# ---------------------------------------------------------------------------

class MarketDataResponse(BaseModel):
    symbol: str
    price: float
    change: float = Field(description="Absolute price change from previous close")
    change_pct: float = Field(description="Percentage change from previous close")
    volume: int
    asset_class: AssetClass
    timestamp: datetime

    model_config = {"json_schema_extra": {
        "example": {
            "symbol": "AAPL",
            "price": 182.50,
            "change": 2.30,
            "change_pct": 1.28,
            "volume": 54_200_000,
            "asset_class": "EQUITY",
            "timestamp": "2024-04-20T14:32:00"
        }
    }}


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------

class TradeCreate(BaseModel):
    """Used when a client POSTs a new trade."""
    symbol: str = Field(min_length=1, max_length=10)
    side: TradeSide
    quantity: float = Field(gt=0, description="Must be positive")
    price: float = Field(gt=0, description="Execution price, must be positive")
    asset_class: AssetClass = AssetClass.EQUITY

    @field_validator("symbol")
    @classmethod
    def symbol_uppercase(cls, v: str) -> str:
        return v.upper().strip()


class TradeResponse(TradeCreate):
    """Returned to the client — includes server-generated fields."""
    id: int
    timestamp: datetime
    notional: float = Field(description="quantity × price")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Positions
# ---------------------------------------------------------------------------

class PositionResponse(BaseModel):
    symbol: str
    sector: str
    quantity: float
    avg_cost: float
    asset_class: AssetClass

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Portfolio analytics (Step 3 will use these)
# ---------------------------------------------------------------------------

class PnLEntry(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float

class PortfolioPnLResponse(BaseModel):
    positions: list[PnLEntry]
    total_unrealized_pnl: float
    total_market_value: float
    as_of: datetime

class SectorExposureEntry(BaseModel):
    sector: str
    market_value: float
    weight_pct: float
    position_count: int

class SectorExposureResponse(BaseModel):
    exposures: list[SectorExposureEntry]
    total_market_value: float
    as_of: datetime

class MovingAverageResponse(BaseModel):
    symbol: str
    window: int
    sma: float
    prices_used: int
    as_of: datetime
