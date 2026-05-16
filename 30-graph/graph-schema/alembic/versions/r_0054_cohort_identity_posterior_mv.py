"""Converted from Kysely migration 0054_cohort_identity_posterior_mv."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0054_cohort_identity_posterior_mv"
down_revision = 'r_0053_vertex_cohort_actor'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0054_cohort_identity_posterior_mv.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0054_cohort_identity_posterior_mv.down.sql"))
