"""Converted from Kysely migration 0085_sitc_hs_derived_bridges."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0085_sitc_hs_derived_bridges"
down_revision = 'r_0084_icd10_iso4217_iso3166'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0085_sitc_hs_derived_bridges.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0085_sitc_hs_derived_bridges.down.sql"))
