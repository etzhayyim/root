"""Add checkpoint state for NDL OAI-PMH window ingest."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509163000_vertex_ndl_oai_checkpoint"
down_revision = "r_20260509162000_biblio_ocr_assets"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509163000_vertex_ndl_oai_checkpoint.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509163000_vertex_ndl_oai_checkpoint.down.sql"))
