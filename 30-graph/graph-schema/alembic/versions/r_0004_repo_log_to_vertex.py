"""Converted from Kysely migration 0004_repo_log_to_vertex."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0004_repo_log_to_vertex"
down_revision = 'r_0003_iceberg_sinks'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0004_repo_log_to_vertex.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0004_repo_log_to_vertex.down.sql"))
