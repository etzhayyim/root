"""Converted from Kysely migration 20260418013944_kaikei_pl_bs_reporting."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260418013944_kaikei_pl_bs_reporting"
down_revision = 'r_20260417230000_vertex_api_key'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260418013944_kaikei_pl_bs_reporting.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260418013944_kaikei_pl_bs_reporting.down.sql"))
