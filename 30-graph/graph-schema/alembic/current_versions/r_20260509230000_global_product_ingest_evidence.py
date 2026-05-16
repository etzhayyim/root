"""Global product ingest evidence tables and Phase 1 LangGraph assistant."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509230000_global_product_ingest_evidence"
down_revision = "r_20260509220000_flip_ki_cycle_v2_pin"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509230000_global_product_ingest_evidence.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509230000_global_product_ingest_evidence.down.sql"))
