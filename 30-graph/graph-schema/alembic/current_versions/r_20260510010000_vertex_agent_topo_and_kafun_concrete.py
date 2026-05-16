"""vertex_agent_topo_and_kafun_concrete — generic agent goal-DAG + kafun concrete.

Adds:
  * Generic vertex_agent_topo_node / edge_agent_topo_depends / edge_agent_topo_concerns
  * MVs mv_agent_topo_ready, mv_agent_topo_progress
  * Kafun concrete vertex_kafun_{nursery,forest_unit,pollen_observation}
  * MV mv_kafun_pollen_yoy
  * Seed: 16-node kafun eradication DAG (L0..L5) + dependency edges

ADRs: 2605080600 (LangGraph), 0036 (Hyperdrive direct write), 0019 (path-DIDs).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510010000_vertex_agent_topo_and_kafun_concrete"
down_revision = "r_20260510000000_vertex_kafun_langgraph"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510010000_vertex_agent_topo_and_kafun_concrete.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510010000_vertex_agent_topo_and_kafun_concrete.down.sql"))
