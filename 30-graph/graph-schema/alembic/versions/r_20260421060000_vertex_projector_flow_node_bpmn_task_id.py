"""Converted from Kysely migration 20260421060000_vertex_projector_flow_node_bpmn_task_id."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260421060000_vertex_projector_flow_node_bpmn_task_id"
down_revision = 'r_20260421050000_vertex_projector_flow_run_owner_token'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260421060000_vertex_projector_flow_node_bpmn_task_id.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260421060000_vertex_projector_flow_node_bpmn_task_id.down.sql"))
