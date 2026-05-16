"""Converted from Kysely migration 0094_hs_legacy_isic4_nace_cpc21_chains."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0094_hs_legacy_isic4_nace_cpc21_chains"
down_revision = 'r_0093_hs_sitc2_isic_cpc3_extended'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0094_hs_legacy_isic4_nace_cpc21_chains.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0094_hs_legacy_isic4_nace_cpc21_chains.down.sql"))
