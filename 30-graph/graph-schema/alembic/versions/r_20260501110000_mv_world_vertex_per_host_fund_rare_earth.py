"""Converted from Kysely migration 20260501110000_mv_world_vertex_per_host_fund_rare_earth."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260501110000_mv_world_vertex_per_host_fund_rare_earth"
down_revision = 'r_20260501100000_vertex_pq_codebook_wet_chunk_pq'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260501110000_mv_world_vertex_per_host_fund_rare_earth.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260501110000_mv_world_vertex_per_host_fund_rare_earth.down.sql"))
