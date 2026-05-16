"""Converted from Kysely migration 0095_reversal_completion_isic5_extended."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0095_reversal_completion_isic5_extended"
down_revision = 'r_0094_hs_legacy_isic4_nace_cpc21_chains'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0095_reversal_completion_isic5_extended.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0095_reversal_completion_isic5_extended.down.sql"))
