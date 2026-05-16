"""Converted from Kysely migration 20260429094500_public_domain_colorization_process_events."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260429094500_public_domain_colorization_process_events"
down_revision = 'r_20260429091300_seed_coverage_lda_core_bpmn_actors'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260429094500_public_domain_colorization_process_events.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260429094500_public_domain_colorization_process_events.down.sql"))
