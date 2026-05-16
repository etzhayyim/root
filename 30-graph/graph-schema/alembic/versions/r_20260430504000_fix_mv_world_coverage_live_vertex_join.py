"""Converted from Kysely migration 20260430504000_fix_mv_world_coverage_live_vertex_join."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260430504000_fix_mv_world_coverage_live_vertex_join"
down_revision = 'r_20260430503000_rw_admin_wrapper_probe_noop'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260430504000_fix_mv_world_coverage_live_vertex_join.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260430504000_fix_mv_world_coverage_live_vertex_join.down.sql"))
