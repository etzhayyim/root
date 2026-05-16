"""Converted from Kysely migration 0081_who_gho_sdg."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0081_who_gho_sdg"
down_revision = 'r_0080_iso639_languages'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0081_who_gho_sdg.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0081_who_gho_sdg.down.sql"))
