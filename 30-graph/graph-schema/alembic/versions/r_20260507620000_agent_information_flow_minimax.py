"""Converted from Kysely migration 20260507620000_agent_information_flow_minimax."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260507620000_agent_information_flow_minimax"
down_revision = 'r_20260507610000_vertex_resources_app_tables'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507620000_agent_information_flow_minimax.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507620000_agent_information_flow_minimax.down.sql"))
