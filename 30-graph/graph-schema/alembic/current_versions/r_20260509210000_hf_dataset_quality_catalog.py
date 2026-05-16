"""HF dataset quality catalog graph.

Adds a judgment layer on top of the raw Hugging Face Hub catalog so curated
dataset lists, modality roles, and reliability decisions are queryable in
RisingWave without forcing full row/blob ingest for huge datasets.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509210000_hf_dataset_quality_catalog"
down_revision = "r_20260509200000_topology_ki_cycle_v2_mcp"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509210000_hf_dataset_quality_catalog.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509210000_hf_dataset_quality_catalog.down.sql"))
