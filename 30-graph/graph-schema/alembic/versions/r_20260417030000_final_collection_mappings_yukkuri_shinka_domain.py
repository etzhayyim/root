"""Converted from Kysely migration 20260417030000_final_collection_mappings_yukkuri_shinka_domains."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260417030000_final_collection_mappings_yukkuri_shinka_domain"
down_revision = 'r_20260417023000_space_satellite_tle_seed'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417030000_final_collection_mappings_yukkuri_shinka_domains.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417030000_final_collection_mappings_yukkuri_shinka_domains.down.sql"))
