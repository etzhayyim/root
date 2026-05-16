"""copyright_ingest v2 — Phase B PoC #3, minimal (1/5 mcp_tool: emit_audit only)."""
from __future__ import annotations
from pathlib import Path
from alembic import op
from graph_schema.db import execute_sql_text

revision = "r_20260509410000_copyright_ingest_canonical_v2_mcp"
down_revision = "r_20260509400000_seed_tools_http_mcp"
branch_labels = None
depends_on = None
ROOT = Path(__file__).resolve().parents[2]

def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")

def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509410000_copyright_ingest_canonical_v2_mcp.up.sql"))

def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509410000_copyright_ingest_canonical_v2_mcp.down.sql"))
