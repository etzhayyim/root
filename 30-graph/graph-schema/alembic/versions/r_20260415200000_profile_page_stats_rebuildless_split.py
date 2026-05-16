"""Converted from Kysely migration 20260415200000_profile_page_stats_rebuildless_split."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260415200000_profile_page_stats_rebuildless_split"
down_revision = 'r_20260415173000_profile_page_stats_mv_optimization'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260415200000_profile_page_stats_rebuildless_split.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260415200000_profile_page_stats_rebuildless_split.down.sql"))
