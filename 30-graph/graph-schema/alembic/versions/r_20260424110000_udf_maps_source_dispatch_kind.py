"""Converted from Kysely migration 20260424110000_udf_maps_source_dispatch_kind."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260424110000_udf_maps_source_dispatch_kind"
down_revision = 'r_20260424100000_seed_maps_coverage_targets_phase2'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260424110000_udf_maps_source_dispatch_kind.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260424110000_udf_maps_source_dispatch_kind.down.sql"))
