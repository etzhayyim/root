"""Converted from Kysely migration 20260417040000_drop_legacy_val_columns."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260417040000_drop_legacy_val_columns"
down_revision = 'r_20260417030000_final_collection_mappings_yukkuri_shinka_domain'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417040000_drop_legacy_val_columns.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417040000_drop_legacy_val_columns.down.sql"))
