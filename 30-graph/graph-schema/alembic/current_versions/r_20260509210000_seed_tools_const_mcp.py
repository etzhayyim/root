"""Seed ai.gftd.tools.const.echo generic primitive in vertex_mcp_tool_def."""
from __future__ import annotations
from pathlib import Path
from alembic import op
from graph_schema.db import execute_sql_text

revision = "r_20260509210000_seed_tools_const_mcp"
down_revision = "r_20260509200000_topology_ki_cycle_v2_mcp"
branch_labels = None
depends_on = None
ROOT = Path(__file__).resolve().parents[2]

def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")

def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509210000_seed_tools_const_mcp.up.sql"))

def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509210000_seed_tools_const_mcp.down.sql"))
