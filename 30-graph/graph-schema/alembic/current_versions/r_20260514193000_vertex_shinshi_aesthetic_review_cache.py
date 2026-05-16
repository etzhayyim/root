"""Shinshi aesthetic review cache."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260514193000_vertex_shinshi_aesthetic_review_cache"
down_revision = "r_20260514010000_seed_open_unispsc_hierarchy_mcp"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260514193000_vertex_shinshi_aesthetic_review_cache.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260514193000_vertex_shinshi_aesthetic_review_cache.down.sql"))
