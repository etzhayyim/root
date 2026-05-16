"""vertex_keiei_cxo — keiei (経営) C-suite AI role layer graph projection.

Adds 4 vertex (vertex_keiei_role / agent / profile / decision) + 4 edge
(agent_acts_as / reports_to / role_has_profile / decision_made_by) + 2 narrow
materialized views (mv_keiei_decision_count_by_role / mv_keiei_role_active_agent).

Driven by `pymagatama.keiei` LSP server (ADR 2605101200). Operating entity =
amanomibashira (sole principal). Vendor = Gftd Japan engineering capacity.

Path-based DIDs (ADR-0019):
  did:web:keiei.gftd.ai
  did:web:keiei.gftd.ai:role:{role_id}
  did:web:keiei.gftd.ai:role:{role_id}:agent
  did:web:keiei.gftd.ai:role:{role_id}:profile

ADRs: 2605101200 (this layer), 0036 (Hyperdrive direct write),
      0019 (path-based DID), 2605082100 (LangGraph checkpointer).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510020000_vertex_keiei_cxo"
down_revision = "r_20260510010000_vertex_hubspot"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020000_vertex_keiei_cxo.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510020000_vertex_keiei_cxo.down.sql"))
