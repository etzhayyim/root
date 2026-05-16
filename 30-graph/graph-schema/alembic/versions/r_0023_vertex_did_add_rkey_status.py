"""Converted from Kysely migration 0023_vertex_did_add_rkey_status."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0023_vertex_did_add_rkey_status"
down_revision = 'r_0022_oil_coverage_mv_trading_distribution_refresh'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0023_vertex_did_add_rkey_status.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0023_vertex_did_add_rkey_status.down.sql"))
