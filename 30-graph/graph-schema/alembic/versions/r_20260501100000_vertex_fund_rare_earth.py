"""Converted from Kysely migration 20260501100000_vertex_fund_rare_earth."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260501100000_vertex_fund_rare_earth"
down_revision = 'r_20260501082500_update_oshinobi_bpmn_payment_charge'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260501100000_vertex_fund_rare_earth.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260501100000_vertex_fund_rare_earth.down.sql"))
