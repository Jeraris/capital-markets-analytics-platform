"""
db/database.py — SQLAlchemy engine, session factory, and Base.

This is the single source of truth for the DB connection.
Every router that needs DB access imports `get_db` from here
and uses FastAPI's Depends() injection — no global state, no
manual session management, no connection leaks.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Read from environment variable; falls back to local dev default.
# In Docker Compose this is set to the postgres service URL.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cmuser:cmpass@localhost:5432/capital_markets",
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # connections kept alive in the pool
    max_overflow=10,      # extra connections allowed under load
    pool_pre_ping=True,   # discard stale connections automatically
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from this Base — Alembic uses it to detect schema changes
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a DB session and guarantees cleanup.

    Usage in any router:
        @router.get("/trades/")
        def list_trades(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
