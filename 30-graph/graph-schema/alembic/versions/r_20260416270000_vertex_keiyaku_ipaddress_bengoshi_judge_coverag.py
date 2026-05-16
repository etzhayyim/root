"""Converted from Kysely migration 20260416270000_vertex_keiyaku_ipaddress_bengoshi_judge_coverage."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260416270000_vertex_keiyaku_ipaddress_bengoshi_judge_coverag"
down_revision = 'r_20260416260000_plc_record_attribution_coverage'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260416270000_vertex_keiyaku_ipaddress_bengoshi_judge_coverage.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260416270000_vertex_keiyaku_ipaddress_bengoshi_judge_coverage.down.sql"))
