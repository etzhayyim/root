"""Converted from Kysely migration 20260421030000_vertex_projector_task."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260421030000_vertex_projector_task"
down_revision = 'r_20260421020000_mv_projector_reflection_count'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260421030000_vertex_projector_task.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260421030000_vertex_projector_task.down.sql"))
