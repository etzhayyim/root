"""saikin.cycle.v2 — first topology with kind=mcp_tool nodes (ADR-2605082000 PoC).

Inserts a new assistant row (v2) that mirrors v1's spec but binds each node
via mcp:// nsid resolution. v1 stays in place; deployment pin is NOT flipped
yet (saikin dispatcher must handle MCP envelopes first).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509170000_topology_saikin_cycle_v2_mcp"
down_revision = "r_20260509160000_seed_saikin_mcp_tools"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509170000_topology_saikin_cycle_v2_mcp.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509170000_topology_saikin_cycle_v2_mcp.down.sql"))
