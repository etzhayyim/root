"""Seed vertex_mcp_tool_def with the 4 ki tools (ADR-2605082000 PoC sibling)."""
from __future__ import annotations
from pathlib import Path
from alembic import op
from graph_schema.db import execute_sql_text

revision = "r_20260509190000_seed_ki_mcp_tools"
down_revision = "r_20260509180000_flip_saikin_cycle_v2_pin"
branch_labels = None
depends_on = None
ROOT = Path(__file__).resolve().parents[2]

def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")

def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509190000_seed_ki_mcp_tools.up.sql"))

def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509190000_seed_ki_mcp_tools.down.sql"))
