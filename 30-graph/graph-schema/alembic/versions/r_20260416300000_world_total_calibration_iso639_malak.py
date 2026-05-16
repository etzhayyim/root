"""Converted from Kysely migration 20260416300000_world_total_calibration_iso639_malak."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260416300000_world_total_calibration_iso639_malak"
down_revision = 'r_20260416290000_gov_municipality_talent_bls_vertex_coverage'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260416300000_world_total_calibration_iso639_malak.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260416300000_world_total_calibration_iso639_malak.down.sql"))
