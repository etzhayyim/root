"""Converted from Kysely migration 0022_oil_coverage_mv_trading_distribution_refresh."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0022_oil_coverage_mv_trading_distribution_refresh"
down_revision = 'r_0021_oil_trading_distribution_backbone'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0022_oil_coverage_mv_trading_distribution_refresh.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0022_oil_coverage_mv_trading_distribution_refresh.down.sql"))
