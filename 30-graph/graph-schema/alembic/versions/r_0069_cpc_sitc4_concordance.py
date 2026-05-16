"""Converted from Kysely migration 0069_cpc_sitc4_concordance."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0069_cpc_sitc4_concordance"
down_revision = 'r_0068_m49_isic4_isic5_concordance'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0069_cpc_sitc4_concordance.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0069_cpc_sitc4_concordance.down.sql"))
