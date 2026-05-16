"""Converted from Kysely migration 0078_iso4217_currency."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0078_iso4217_currency"
down_revision = 'r_0077_atc_drug_classification'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0078_iso4217_currency.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0078_iso4217_currency.down.sql"))
