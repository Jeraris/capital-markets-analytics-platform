"""Initial schema: instruments, trades, positions, market_prices

Revision ID: 0001_initial
Revises:
Create Date: 2024-04-20
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id",          sa.Integer(),    primary_key=True),
        sa.Column("symbol",      sa.String(10),   nullable=False),
        sa.Column("name",        sa.String(100),  nullable=False),
        sa.Column("sector",      sa.String(50),   nullable=False),
        sa.Column("asset_class", sa.Enum("EQUITY", "FIXED_INCOME", "FX", "COMMODITY", name="assetclassorm"), nullable=False),
    )
    op.create_index("ix_instruments_id",     "instruments", ["id"])
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"], unique=True)

    op.create_table(
        "trades",
        sa.Column("id",        sa.Integer(),  primary_key=True),
        sa.Column("symbol",    sa.String(10), sa.ForeignKey("instruments.symbol"), nullable=False),
        sa.Column("side",      sa.Enum("BUY", "SELL", name="tradesideorm"), nullable=False),
        sa.Column("quantity",  sa.Float(),    nullable=False),
        sa.Column("price",     sa.Float(),    nullable=False),
        sa.Column("notional",  sa.Float(),    nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_trades_id",               "trades", ["id"])
    op.create_index("ix_trades_symbol",           "trades", ["symbol"])
    op.create_index("ix_trades_timestamp",        "trades", ["timestamp"])
    op.create_index("ix_trades_symbol_timestamp", "trades", ["symbol", "timestamp"])

    op.create_table(
        "positions",
        sa.Column("id",           sa.Integer(), primary_key=True),
        sa.Column("symbol",       sa.String(10), sa.ForeignKey("instruments.symbol"), nullable=False, unique=True),
        sa.Column("quantity",     sa.Float(),   nullable=False, server_default="0"),
        sa.Column("avg_cost",     sa.Float(),   nullable=False, server_default="0"),
        sa.Column("realized_pnl", sa.Float(),   nullable=False, server_default="0"),
        sa.Column("updated_at",   sa.DateTime(), nullable=False),
    )
    op.create_index("ix_positions_id", "positions", ["id"])

    op.create_table(
        "market_prices",
        sa.Column("id",     sa.Integer(),  primary_key=True),
        sa.Column("symbol", sa.String(10), sa.ForeignKey("instruments.symbol"), nullable=False),
        sa.Column("date",   sa.DateTime(), nullable=False),
        sa.Column("open",   sa.Float(),    nullable=False),
        sa.Column("high",   sa.Float(),    nullable=False),
        sa.Column("low",    sa.Float(),    nullable=False),
        sa.Column("close",  sa.Float(),    nullable=False),
        sa.Column("volume", sa.Integer(),  nullable=False),
        sa.UniqueConstraint("symbol", "date", name="uq_market_prices_symbol_date"),
    )
    op.create_index("ix_market_prices_id",          "market_prices", ["id"])
    op.create_index("ix_market_prices_symbol",      "market_prices", ["symbol"])
    op.create_index("ix_market_prices_date",        "market_prices", ["date"])
    op.create_index("ix_market_prices_symbol_date", "market_prices", ["symbol", "date"])


def downgrade() -> None:
    op.drop_table("market_prices")
    op.drop_table("positions")
    op.drop_table("trades")
    op.drop_table("instruments")
    op.execute("DROP TYPE IF EXISTS tradesideorm")
    op.execute("DROP TYPE IF EXISTS assetclassorm")
