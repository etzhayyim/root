"""NDL image-first ingest tables.

ADR-2605080700: active DDL lives under alembic/current_versions, starting
from the live RisingWave baseline. Historical Kysely migrations and
alembic/versions are lineage archives only.

Base tables are Alembic-owned. Rebuildable coverage views live in SQLMesh.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509150000_vertex_ndl_image_ocr"
down_revision = "r_20260509140000_topology_saikin_cycle"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509150000_vertex_ndl_image_ocr.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509150000_vertex_ndl_image_ocr.down.sql"))
