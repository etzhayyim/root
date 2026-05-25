"""Seed vertex_mcp_tool_def with the 5 saikin tools (ADR-2605082000 PoC).

Pre-requisite for the saikin.cycle.v2 topology rewrite (next migration) which
binds nodes via `kind=mcp_tool ref=mcp://app.etzhayyim.apps.saikin.<method>`.
The resolver SELECTs actor_host from this table.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509160000_seed_saikin_mcp_tools"
down_revision = "r_20260509130000_alter_langgraph_assistant_lineage"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509160000_seed_saikin_mcp_tools.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509160000_seed_saikin_mcp_tools.down.sql"))
