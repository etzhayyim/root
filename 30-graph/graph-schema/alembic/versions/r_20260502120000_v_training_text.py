"""Converted from Kysely migration 20260502120000_v_training_text."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260502120000_v_training_text"
down_revision = 'r_20260501970000_alter_signal_tables_generic_cols'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260502120000_v_training_text.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260502120000_v_training_text.down.sql"))
