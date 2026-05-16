"""Converted from Kysely migration 20260507800000_vertex_webmk_tables."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260507800000_vertex_webmk_tables"
down_revision = 'r_20260507780000_coverage_recipe_natural_person_deps_follows'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507800000_vertex_webmk_tables.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507800000_vertex_webmk_tables.down.sql"))
