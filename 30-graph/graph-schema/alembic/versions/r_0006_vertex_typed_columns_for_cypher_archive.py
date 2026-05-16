"""Converted from Kysely migration 0006_vertex_typed_columns_for_cypher_archive."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0006_vertex_typed_columns_for_cypher_archive"
down_revision = 'r_0005_vertex_gitrepo'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0006_vertex_typed_columns_for_cypher_archive.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0006_vertex_typed_columns_for_cypher_archive.down.sql"))
