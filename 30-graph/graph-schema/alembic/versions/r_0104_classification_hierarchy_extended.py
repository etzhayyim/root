"""Converted from Kysely migration 0104_classification_hierarchy_extended."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0104_classification_hierarchy_extended"
down_revision = 'r_0103_classification_hierarchy_bridges'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0104_classification_hierarchy_extended.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0104_classification_hierarchy_extended.down.sql"))
