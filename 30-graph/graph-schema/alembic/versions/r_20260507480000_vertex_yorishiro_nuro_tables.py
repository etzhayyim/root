"""Converted from Kysely migration 20260507480000_vertex_yorishiro_nuro_tables."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260507480000_vertex_yorishiro_nuro_tables"
down_revision = 'r_20260507470000_vertex_saiban_tables'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507480000_vertex_yorishiro_nuro_tables.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507480000_vertex_yorishiro_nuro_tables.down.sql"))
