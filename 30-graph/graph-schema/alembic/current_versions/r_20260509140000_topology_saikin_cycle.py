"""Topology migration for saikin.cycle.v1 (P3 PoC, ADR-2605080600).

Replaces the py_factory row with a topology assistant + 5 node bindings.
The watcher picks up the change via updated_at diff and re-compiles.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509140000_topology_saikin_cycle"
down_revision = "r_20260509130000_alter_langgraph_assistant_checkpointer_mode"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509140000_topology_saikin_cycle.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509140000_topology_saikin_cycle.down.sql"))
