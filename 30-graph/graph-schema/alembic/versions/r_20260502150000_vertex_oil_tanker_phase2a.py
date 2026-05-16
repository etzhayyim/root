"""Converted from Kysely migration 20260502150000_vertex_oil_tanker_phase2a."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260502150000_vertex_oil_tanker_phase2a"
down_revision = 'r_20260502140000_update_training_export_bpmn_phase_d'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260502150000_vertex_oil_tanker_phase2a.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260502150000_vertex_oil_tanker_phase2a.down.sql"))
