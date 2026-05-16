"""Converted from Kysely migration 0052_vertex_repo_record_cohort_columns."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0052_vertex_repo_record_cohort_columns"
down_revision = 'r_0050_outbox_governance_page_domain'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0052_vertex_repo_record_cohort_columns.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0052_vertex_repo_record_cohort_columns.down.sql"))
