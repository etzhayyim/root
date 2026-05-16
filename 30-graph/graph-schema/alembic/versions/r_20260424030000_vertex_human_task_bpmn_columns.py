"""Converted from Kysely migration 20260424030000_vertex_human_task_bpmn_columns."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260424030000_vertex_human_task_bpmn_columns"
down_revision = 'r_20260424014529_mv_actor_social_stats_root_normalization'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260424030000_vertex_human_task_bpmn_columns.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260424030000_vertex_human_task_bpmn_columns.down.sql"))
