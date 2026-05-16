"""vertex_langgraph_assistant + assistant_node + deployment — RW-resident LangGraph SSoT.

ADR-2605080600 amendment. Deploy/rollback via row INSERT (PK implicit upsert).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509100000_vertex_langgraph_assistant_registry"
down_revision = "r_20260509073000_vertex_langgraph_checkpoint_blob"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509100000_vertex_langgraph_assistant_registry.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509100000_vertex_langgraph_assistant_registry.down.sql"))
