"""Converted from Kysely migration 20260430150000_fix_actor_registry_canonical_did."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260430150000_fix_actor_registry_canonical_did"
down_revision = 'r_20260430140000_update_yukkuri_compose_bpmn_social_post'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260430150000_fix_actor_registry_canonical_did.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260430150000_fix_actor_registry_canonical_did.down.sql"))
