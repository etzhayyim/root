"""Seed 63 builtin LangGraph assistants as py_factory rows (P1a).

ADR-2605080600 — DB becomes sole SSoT for /assistants registry.
Static _register_builtin_graphs() block in langgraph_server_app.py is
removed in a follow-up commit, after at least one Cron firing has been
verified against the row-driven path (advisor's two-phase rule).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509120000_seed_langgraph_builtin_63"
down_revision = "r_20260509110000_vertex_spiff_runtime"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509120000_seed_langgraph_builtin_63.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509120000_seed_langgraph_builtin_63.down.sql"))
