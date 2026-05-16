"""Converted from Kysely migration 20260428230200_mv_open_cyber_vuln_analytics."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260428230200_mv_open_cyber_vuln_analytics"
down_revision = 'r_20260428230100_seed_open_cyber_bpmn_actors'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260428230200_mv_open_cyber_vuln_analytics.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260428230200_mv_open_cyber_vuln_analytics.down.sql"))
