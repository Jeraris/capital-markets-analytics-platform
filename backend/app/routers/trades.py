"""
routers/trades.py — Trade blotter endpoints backed by PostgreSQL.

Every handler receives a SQLAlchemy Session via FastAPI's Depends(get_db).
No global state, no in-memory lists — real DB reads and writes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.db.orm_models import Trade, Instrument, Position, TradeSideORM
from app.models.schemas import TradeCreate, TradeResponse, TradeSide

router = APIRouter(prefix="/trades", tags=["Trade Blotter"])


def _to_response(trade: Trade) -> TradeResponse:
    """Map ORM Trade -> Pydantic TradeResponse."""
    return TradeResponse(
        id=trade.id,
        symbol=trade.symbol,
        side=TradeSide(trade.side.value),
        quantity=trade.quantity,
        price=trade.price,
        notional=trade.notional,
        asset_class=trade.instrument.asset_class.value,
        timestamp=trade.timestamp,
    )


def _update_position(db: Session, symbol: str, side: TradeSideORM, qty: float, price: float):
    """
    Update the positions table after each trade using weighted average cost.
    Called inside the same transaction as the trade insert — atomic.
    """
    pos = db.query(Position).filter_by(symbol=symbol).first()

    if side == TradeSideORM.BUY:
        if pos is None:
            pos = Position(symbol=symbol, quantity=qty, avg_cost=price, realized_pnl=0.0)
            db.add(pos)
        else:
            total_cost = pos.avg_cost * pos.quantity + price * qty
            pos.quantity += qty
            pos.avg_cost = round(total_cost / pos.quantity, 6)
            pos.updated_at = datetime.utcnow()
    else:  # SELL
        if pos is None or pos.quantity < qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient position in {symbol} to sell {qty}",
            )
        realized = round((price - pos.avg_cost) * qty, 2)
        pos.quantity -= qty
        pos.realized_pnl += realized
        pos.updated_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[TradeResponse], summary="All trades")
def get_all_trades(
    symbol: str | None = Query(default=None, description="Filter by symbol, e.g. AAPL"),
    side: TradeSide | None = Query(default=None, description="Filter by BUY or SELL"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return the full trade blotter, most recent first."""
    q = db.query(Trade)
    if symbol:
        q = q.filter(Trade.symbol == symbol.upper())
    if side:
        q = q.filter(Trade.side == TradeSideORM(side.value))
    trades = q.order_by(Trade.timestamp.desc()).limit(limit).all()
    return [_to_response(t) for t in trades]


@router.get("/{trade_id}", response_model=TradeResponse, summary="Single trade by ID")
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")
    return _to_response(trade)


@router.post("/", response_model=TradeResponse, status_code=201, summary="Submit a trade")
def create_trade(payload: TradeCreate, db: Session = Depends(get_db)):
    """
    Submit a new trade. Validates the symbol, writes the trade row,
    and updates the position — all in one atomic transaction.
    """
    symbol = payload.symbol
    instrument = db.query(Instrument).filter_by(symbol=symbol).first()
    if not instrument:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown symbol '{symbol}'. Add it to instruments first.",
        )

    side = TradeSideORM(payload.side.value)
    trade = Trade(
        symbol=symbol,
        side=side,
        quantity=payload.quantity,
        price=payload.price,
        notional=round(payload.quantity * payload.price, 2),
        timestamp=datetime.utcnow(),
    )
    db.add(trade)
    _update_position(db, symbol, side, payload.quantity, payload.price)
    db.commit()
    db.refresh(trade)
    return _to_response(trade)
