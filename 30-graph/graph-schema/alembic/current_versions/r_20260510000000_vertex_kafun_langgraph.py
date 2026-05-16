"""vertex_kafun_langgraph — kafun-bokumetsu LangGraph migration.

Adds 4 T2 domain tables (vertex_kafun_research / insight / proposal / action)
and seeds the LangGraph registry (assistant + deployment + bpmn_lexicon_binding)
for kafun.research.v1 / kafun.think.v1 / kafun.tick.v1.

ADRs: 2605080600 (LangGraph Server), 2605082000 (Graph-Definition-as-Data),
      0019 (path-based actor DIDs), 0036 (Hyperdrive direct domain write).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510000000_vertex_kafun_langgraph"
down_revision = "r_20260509500000_organism_ecosystem_schema"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510000000_vertex_kafun_langgraph.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510000000_vertex_kafun_langgraph.down.sql"))
