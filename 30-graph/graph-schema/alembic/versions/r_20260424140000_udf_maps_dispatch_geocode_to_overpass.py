"""Converted from Kysely migration 20260424140000_udf_maps_dispatch_geocode_to_overpass."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260424140000_udf_maps_dispatch_geocode_to_overpass"
down_revision = 'r_20260424132100_seed_open_network_bpmn_actors'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260424140000_udf_maps_dispatch_geocode_to_overpass.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260424140000_udf_maps_dispatch_geocode_to_overpass.down.sql"))
