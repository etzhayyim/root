"""Converted from Kysely migration 20260425010000_view_maps_spatial_unified."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260425010000_view_maps_spatial_unified"
down_revision = 'r_20260425000000_seed_wikidata_specialty_5'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260425010000_view_maps_spatial_unified.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260425010000_view_maps_spatial_unified.down.sql"))
