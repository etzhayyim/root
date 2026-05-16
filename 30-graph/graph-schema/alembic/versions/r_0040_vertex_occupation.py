"""Converted from Kysely migration 0040_vertex_occupation."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0040_vertex_occupation"
down_revision = 'r_0039_vertex_profile_fragment_embedding'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0040_vertex_occupation.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0040_vertex_occupation.down.sql"))
