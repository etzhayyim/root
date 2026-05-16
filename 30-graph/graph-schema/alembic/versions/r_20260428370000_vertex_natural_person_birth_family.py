"""Converted from Kysely migration 20260428370000_vertex_natural_person_birth_family."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260428370000_vertex_natural_person_birth_family"
down_revision = 'r_20260428360000_vertex_open_ossekai'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260428370000_vertex_natural_person_birth_family.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260428370000_vertex_natural_person_birth_family.down.sql"))
