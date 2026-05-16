"""vertex_recap_download — add license column.

Revision ID: r_20260512130000
Revises: r_20260512120000
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text

revision = "r_20260512130000"
down_revision = "r_20260512120000"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260512130000_recap_download_add_license.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260512130000_recap_download_add_license.down.sql"))
