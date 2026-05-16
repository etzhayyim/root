"""Converted from Kysely migration 20260428240000_edge_business_person_relation."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260428240000_edge_business_person_relation"
down_revision = 'r_20260428240000_actor_did_backfill_tier1'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260428240000_edge_business_person_relation.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260428240000_edge_business_person_relation.down.sql"))
