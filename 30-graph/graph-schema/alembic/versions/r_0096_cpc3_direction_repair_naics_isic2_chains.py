"""Converted from Kysely migration 0096_cpc3_direction_repair_naics_isic2_chains."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0096_cpc3_direction_repair_naics_isic2_chains"
down_revision = 'r_0095_reversal_completion_isic5_extended'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0096_cpc3_direction_repair_naics_isic2_chains.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0096_cpc3_direction_repair_naics_isic2_chains.down.sql"))
