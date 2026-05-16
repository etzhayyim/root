"""ALTER vertex_langgraph_assistant — add checkpointer_mode / authored_by / superseded_by.

ADR-2605082000 (amended). Extends the existing assistant registry with the
3 lineage columns required for data-only self-evolution. No new table is
created — see deleted parallel proposal `20260509020000_vertex_langgraph_graph_def.ts`.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509130000_alter_langgraph_assistant_lineage"
down_revision = "r_20260509120000_seed_langgraph_builtin_63"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509130000_alter_langgraph_assistant_lineage.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509130000_alter_langgraph_assistant_lineage.down.sql"))
