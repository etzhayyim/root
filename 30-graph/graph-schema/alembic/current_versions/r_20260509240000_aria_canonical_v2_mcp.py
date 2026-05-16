"""aria canonical-actor v2 — first multi-assistant cluster migration (ADR-2605082000 Phase A)."""
from __future__ import annotations
from pathlib import Path
from alembic import op
from graph_schema.db import execute_sql_text

revision = "r_20260509240000_aria_canonical_v2_mcp"
down_revision = "r_20260509230000_adsk_ingest_dataset_v2_mcp"
branch_labels = None
depends_on = None
ROOT = Path(__file__).resolve().parents[2]

def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")

def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509240000_aria_canonical_v2_mcp.up.sql"))

def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509240000_aria_canonical_v2_mcp.down.sql"))
