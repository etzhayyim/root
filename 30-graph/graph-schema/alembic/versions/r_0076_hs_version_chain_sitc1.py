"""Converted from Kysely migration 0076_hs_version_chain_sitc1."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0076_hs_version_chain_sitc1"
down_revision = 'r_0075_cofog_isic31_isic2'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0076_hs_version_chain_sitc1.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0076_hs_version_chain_sitc1.down.sql"))
