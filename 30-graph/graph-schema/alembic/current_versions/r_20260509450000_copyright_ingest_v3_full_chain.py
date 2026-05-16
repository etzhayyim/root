"""copyright_ingest v3 — full data chain (Crossref half) per ADR-2605082000 §2.

Builds on iter56 e2e_smoke proof. Crossref half uses the 4-node chain
(http.fetch → json.extract → transform.map → sql.exec). DataCite half
remains grandfathered until the operator runs the same migration pattern.
"""
from __future__ import annotations
from pathlib import Path
from alembic import op
from graph_schema.db import execute_sql_text

revision = "r_20260509450000_copyright_ingest_v3_full_chain"
down_revision = "r_20260509440000_seed_tools_transform_mcp"
branch_labels = None
depends_on = None
ROOT = Path(__file__).resolve().parents[2]

def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")

def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509450000_copyright_ingest_v3_full_chain.up.sql"))

def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509450000_copyright_ingest_v3_full_chain.down.sql"))
