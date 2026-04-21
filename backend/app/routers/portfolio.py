"""
routers/portfolio.py — Portfolio analytics backed by PostgreSQL.

All three endpoints now query real DB tables:
  - /pnl       : joins positions + market_prices (latest close)
  - /exposure  : joins positions + instruments for sector grouping
  - /moving-average/{symbol} : queries market_prices price history
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.db.database import get_db
from app.db.orm_models import Position, Instrument, MarketPrice
from app.models.schemas import (
    PortfolioPnLResponse, PnLEntry,
    SectorExposureResponse, SectorExposureEntry,
    MovingAverageResponse,
)

router = APIRouter(prefix="/portfolio", tags=["Portfolio Analytics"])


def _latest_close(db: Session, symbol: str) -> float | None:
    """Return the most recent closing price for a symbol from market_prices."""
    row = (
        db.query(MarketPrice.close)
        .filter(MarketPrice.symbol == symbol)
        .order_by(MarketPrice.date.desc())
        .first()
    )
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/pnl", response_model=PortfolioPnLResponse, summary="Unrealized P&L by position")
def get_portfolio_pnl(db: Session = Depends(get_db)):
    """
    For each open position, compute unrealized P&L using the latest
    closing price from market_prices.

    Formula: (current_price - avg_cost) x quantity
    """
    positions = db.query(Position).filter(Position.quantity > 0).all()
    if not positions:
        raise HTTPException(status_code=404, detail="No open positions found")

    entries = []
    total_pnl = 0.0
    total_mv = 0.0

    for pos in positions:
        current_price = _latest_close(db, pos.symbol)
        if current_price is None:
            current_price = pos.avg_cost  # fallback: no price data

        pnl = round((current_price - pos.avg_cost) * pos.quantity, 2)
        pnl_pct = round(((current_price - pos.avg_cost) / pos.avg_cost) * 100, 4)
        mv = round(current_price * pos.quantity, 2)
        total_pnl += pnl
        total_mv += mv

        entries.append(PnLEntry(
            symbol=pos.symbol,
            quantity=pos.quantity,
            avg_cost=pos.avg_cost,
            current_price=current_price,
            unrealized_pnl=pnl,
            unrealized_pnl_pct=pnl_pct,
        ))

    return PortfolioPnLResponse(
        positions=sorted(entries, key=lambda e: abs(e.unrealized_pnl), reverse=True),
        total_unrealized_pnl=round(total_pnl, 2),
        total_market_value=round(total_mv, 2),
        as_of=datetime.utcnow(),
    )


@router.get("/exposure", response_model=SectorExposureResponse, summary="Sector exposure breakdown")
def get_sector_exposure(db: Session = Depends(get_db)):
    """
    Group open positions by sector and compute each sector's share
    of total portfolio market value.

    Standard risk management view used on trading desks.
    """
    positions = (
        db.query(Position, Instrument)
        .join(Instrument, Position.symbol == Instrument.symbol)
        .filter(Position.quantity > 0)
        .all()
    )
    if not positions:
        raise HTTPException(status_code=404, detail="No open positions found")

    sector_mv: dict[str, float] = {}
    sector_count: dict[str, int] = {}
    total_mv = 0.0

    for pos, inst in positions:
        current_price = _latest_close(db, pos.symbol) or pos.avg_cost
        mv = current_price * pos.quantity
        sector_mv[inst.sector] = sector_mv.get(inst.sector, 0.0) + mv
        sector_count[inst.sector] = sector_count.get(inst.sector, 0) + 1
        total_mv += mv

    exposures = [
        SectorExposureEntry(
            sector=sector,
            market_value=round(mv, 2),
            weight_pct=round((mv / total_mv) * 100, 4),
            position_count=sector_count[sector],
        )
        for sector, mv in sorted(sector_mv.items(), key=lambda x: x[1], reverse=True)
    ]

    return SectorExposureResponse(
        exposures=exposures,
        total_market_value=round(total_mv, 2),
        as_of=datetime.utcnow(),
    )


@router.get(
    "/moving-average/{symbol}",
    response_model=MovingAverageResponse,
    summary="Simple moving average from price history",
)
def get_moving_average(
    symbol: str,
    window: int = Query(default=20, ge=5, le=200, description="SMA window in trading days"),
    db: Session = Depends(get_db),
):
    """
    Compute the N-day simple moving average (SMA) for a symbol
    using closing prices from the market_prices table.

    SMA is a standard technical indicator used in equities trading.
    """
    symbol = symbol.upper()

    rows = (
        db.query(MarketPrice.close)
        .filter(MarketPrice.symbol == symbol)
        .order_by(MarketPrice.date.desc())
        .limit(window)
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No price history for '{symbol}'",
        )

    closes = [r[0] for r in rows]
    sma = round(sum(closes) / len(closes), 4)

    return MovingAverageResponse(
        symbol=symbol,
        window=window,
        sma=sma,
        prices_used=len(closes),
        as_of=datetime.utcnow(),
    )
