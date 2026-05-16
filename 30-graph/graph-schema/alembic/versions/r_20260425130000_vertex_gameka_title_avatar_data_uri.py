"""Converted from Kysely migration 20260425130000_vertex_gameka_title_avatar_data_uri."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260425130000_vertex_gameka_title_avatar_data_uri"
down_revision = 'r_20260425130000_open_defence_event_typed_columns_and_edges'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260425130000_vertex_gameka_title_avatar_data_uri.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260425130000_vertex_gameka_title_avatar_data_uri.down.sql"))
