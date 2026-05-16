"""Converted from Kysely migration 0074_sitc2_sitc3_isco_bec."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0074_sitc2_sitc3_isco_bec"
down_revision = 'r_0073_derived_concordance_bridges'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0074_sitc2_sitc3_isco_bec.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0074_sitc2_sitc3_isco_bec.down.sql"))
