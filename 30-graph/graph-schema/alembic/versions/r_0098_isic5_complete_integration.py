"""Converted from Kysely migration 0098_isic5_complete_integration."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0098_isic5_complete_integration"
down_revision = 'r_0097_isic5_cpc21_nace_geo_iso639'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0098_isic5_complete_integration.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0098_isic5_complete_integration.down.sql"))
