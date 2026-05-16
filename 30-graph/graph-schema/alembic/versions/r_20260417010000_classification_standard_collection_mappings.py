"""Converted from Kysely migration 20260417010000_classification_standard_collection_mappings."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260417010000_classification_standard_collection_mappings"
down_revision = 'r_20260417000500_maps_vector_source_graph'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417010000_classification_standard_collection_mappings.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417010000_classification_standard_collection_mappings.down.sql"))
