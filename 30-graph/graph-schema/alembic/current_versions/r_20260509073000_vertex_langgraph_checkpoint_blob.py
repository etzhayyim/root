"""vertex_langgraph_checkpoint_blob — real content-addressed dedup."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509073000_vertex_langgraph_checkpoint_blob"
down_revision = "r_20260509072000_alter_langgraph_checkpoint_dedup"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509073000_vertex_langgraph_checkpoint_blob.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509073000_vertex_langgraph_checkpoint_blob.down.sql"))
