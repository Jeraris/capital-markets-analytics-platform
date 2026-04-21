"""
main.py — FastAPI application entry point.

This file does ONE thing: create the app and mount routers.
No business logic here. All route logic lives in app/routers/.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import market, trades, portfolio

app = FastAPI(
    title="Capital Markets Analytics Platform",
    description=(
        "A full-stack financial analytics platform simulating trade monitoring, "
        "market data ingestion, and portfolio risk analytics. "
        "Built to demonstrate backend engineering for capital markets systems."
    ),
    version="1.0.0",
    contact={"name": "Jeremiah Arisekola-Ojo"},
)

# Allow the React frontend (localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(market.router)
app.include_router(trades.router)
app.include_router(portfolio.router)


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint. Used by Docker and load balancers."""
    return {"status": "ok", "service": "capital-markets-analytics-platform"}
