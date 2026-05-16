"""Converted from Kysely migration 0093_hs_sitc2_isic_cpc3_extended."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0093_hs_sitc2_isic_cpc3_extended"
down_revision = 'r_0092_sitc_isic4_hs_sitc3_cpc_nace'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0093_hs_sitc2_isic_cpc3_extended.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0093_hs_sitc2_isic_cpc3_extended.down.sql"))
