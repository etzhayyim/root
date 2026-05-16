"""Converted from Kysely migration 20260505100000_update_maps_coverage_binding_async."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260505100000_update_maps_coverage_binding_async"
down_revision = 'r_20260505100000_seed_purge_live_tracker_bpmn'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260505100000_update_maps_coverage_binding_async.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260505100000_update_maps_coverage_binding_async.down.sql"))
