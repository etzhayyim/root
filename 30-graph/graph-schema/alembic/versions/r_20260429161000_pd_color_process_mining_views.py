"""Converted from Kysely migration 20260429161000_pd_color_process_mining_views."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260429161000_pd_color_process_mining_views"
down_revision = 'r_20260429153000_gov_fetch_coverage_view'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260429161000_pd_color_process_mining_views.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260429161000_pd_color_process_mining_views.down.sql"))
