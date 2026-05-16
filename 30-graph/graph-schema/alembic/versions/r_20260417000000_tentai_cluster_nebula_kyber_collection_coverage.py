"""Converted from Kysely migration 20260417000000_tentai_cluster_nebula_kyber_collection_coverage."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260417000000_tentai_cluster_nebula_kyber_collection_coverage"
down_revision = 'r_20260416330000_kyber_office_document_vertex_coverage'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417000000_tentai_cluster_nebula_kyber_collection_coverage.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417000000_tentai_cluster_nebula_kyber_collection_coverage.down.sql"))
