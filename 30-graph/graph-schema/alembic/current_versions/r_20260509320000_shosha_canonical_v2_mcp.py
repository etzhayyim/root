"""shosha canonical v2 — 6 of 7 assistants, 15 nodes (10 actor + 5 audit.emit).

ADR-2605082000 Phase A. shosha_agent_loop excluded (fetchContext + callLlm
self_logic per iter25 NO_TASK_IMPORT spot-check)."""
from __future__ import annotations
from pathlib import Path
from alembic import op
from graph_schema.db import execute_sql_text

revision = "r_20260509320000_shosha_canonical_v2_mcp"
down_revision = "r_20260509310000_seed_tools_audit_mcp"
branch_labels = None
depends_on = None
ROOT = Path(__file__).resolve().parents[2]

def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")

def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509320000_shosha_canonical_v2_mcp.up.sql"))

def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509320000_shosha_canonical_v2_mcp.down.sql"))
