"""Converted from Kysely migration 0017_project_convo_overflow_columns."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0017_project_convo_overflow_columns"
down_revision = 'r_0016_actor_repo_stats_mv'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0017_project_convo_overflow_columns.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0017_project_convo_overflow_columns.down.sql"))
