"""Converted from Kysely migration 20260427005000_gov_form_extraction_queue."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260427005000_gov_form_extraction_queue"
down_revision = 'r_20260427003000_vertex_open_jpn_mynumber'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260427005000_gov_form_extraction_queue.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260427005000_gov_form_extraction_queue.down.sql"))
