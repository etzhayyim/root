"""Converted from Kysely migration 0107_cpc21_reverses_naics_extended_sitc_cpc3."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0107_cpc21_reverses_naics_extended_sitc_cpc3"
down_revision = 'r_0106_bec_asfis_hierarchy_naics_extended'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0107_cpc21_reverses_naics_extended_sitc_cpc3.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0107_cpc21_reverses_naics_extended_sitc_cpc3.down.sql"))
