"""Converted from Kysely migration 20260430402000_dim_world_domain_missing_coverage_domains."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260430402000_dim_world_domain_missing_coverage_domains"
down_revision = 'r_20260430401000_seed_curpus2skill_bpmn'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260430402000_dim_world_domain_missing_coverage_domains.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260430402000_dim_world_domain_missing_coverage_domains.down.sql"))
