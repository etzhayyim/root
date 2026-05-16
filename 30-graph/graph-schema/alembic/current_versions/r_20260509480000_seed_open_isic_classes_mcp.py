"""Seed openIsic classes MCP capabilities (ADR-2605082000 §2.6)."""
from __future__ import annotations
from pathlib import Path
from alembic import op
from graph_schema.db import execute_sql_text

revision = "r_20260509480000_seed_open_isic_classes_mcp"
down_revision = "r_20260509470000_seed_open_isic_get_taxonomy_mcp"
branch_labels = None
depends_on = None
ROOT = Path(__file__).resolve().parents[2]

def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")

def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509480000_seed_open_isic_classes_mcp.up.sql"))

def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509480000_seed_open_isic_classes_mcp.down.sql"))
