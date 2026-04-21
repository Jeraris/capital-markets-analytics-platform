"""
routers/market.py — Market data endpoints backed by PostgreSQL.

/market-data/          — latest close per instrument (from market_prices)
/market-data/{symbol}  — latest close for one symbol
/market-data/{symbol}/history — OHLCV rows from market_prices table
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.db.orm_models import Instrument, MarketPrice
from app.models.schemas import MarketDataResponse, AssetClass

router = APIRouter(prefix="/market-data", tags=["Market Data"])


def _build_response(inst: Instrument, latest: MarketPrice, prev: MarketPrice | None) -> MarketDataResponse:
    prev_close = prev.close if prev else latest.close
    change = round(latest.close - prev_close, 4)
    change_pct = round((change / prev_close) * 100, 4) if prev_close else 0.0
    return MarketDataResponse(
        symbol=inst.symbol,
        price=latest.close,
        change=change,
        change_pct=change_pct,
        volume=latest.volume,
        asset_class=AssetClass(inst.asset_class.value),
        timestamp=latest.date,
    )


def _get_latest_two(db: Session, symbol: str) -> tuple[MarketPrice | None, MarketPrice | None]:
    """Return (latest, previous) closing price rows for a symbol."""
    rows = (
        db.query(MarketPrice)
        .filter(MarketPrice.symbol == symbol)
        .order_by(MarketPrice.date.desc())
        .limit(2)
        .all()
    )
    latest = rows[0] if len(rows) >= 1 else None
    prev   = rows[1] if len(rows) >= 2 else None
    return latest, prev


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[MarketDataResponse], summary="All instruments — latest price")
def get_all_market_data(db: Session = Depends(get_db)):
    """Return the most recent closing price for every tracked instrument."""
    instruments = db.query(Instrument).all()
    results = []
    for inst in instruments:
        latest, prev = _get_latest_two(db, inst.symbol)
        if latest:
            results.append(_build_response(inst, latest, prev))
    return results


@router.get("/{symbol}", response_model=MarketDataResponse, summary="Single instrument — latest price")
def get_market_data_by_symbol(symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper()
    inst = db.query(Instrument).filter_by(symbol=symbol).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    latest, prev = _get_latest_two(db, symbol)
    if not latest:
        raise HTTPException(status_code=404, detail=f"No price data for '{symbol}'")
    return _build_response(inst, latest, prev)


@router.get("/{symbol}/history", summary="OHLCV price history")
def get_price_history(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Return up to N days of OHLCV history from the market_prices table."""
    symbol = symbol.upper()
    if not db.query(Instrument).filter_by(symbol=symbol).first():
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")

    rows = (
        db.query(MarketPrice)
        .filter(MarketPrice.symbol == symbol)
        .order_by(MarketPrice.date.asc())
        .limit(days)
        .all()
    )
    return {
        "symbol": symbol,
        "days": len(rows),
        "history": [
            {
                "date":   r.date.strftime("%Y-%m-%d"),
                "open":   r.open,
                "high":   r.high,
                "low":    r.low,
                "close":  r.close,
                "volume": r.volume,
            }
            for r in rows
        ],
    }
