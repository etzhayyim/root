"""Converted from Kysely migration 20260506093000_vertex_ads_analysis."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260506093000_vertex_ads_analysis"
down_revision = 'r_20260506000100_adsk_bpmn_v3_xml_comment_fix'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260506093000_vertex_ads_analysis.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260506093000_vertex_ads_analysis.down.sql"))
