"""Converted from Kysely migration 20260417160000_lawfirm_projection_mvs."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260417160000_lawfirm_projection_mvs"
down_revision = 'r_20260417150000_etzhayyim_did_recursive_tree'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417160000_lawfirm_projection_mvs.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417160000_lawfirm_projection_mvs.down.sql"))
