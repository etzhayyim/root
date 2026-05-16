"""Converted from Kysely migration 20260507850000_coverage_recipe_business_person_lei."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260507850000_coverage_recipe_business_person_lei"
down_revision = 'r_20260507840000_vertex_open_lei_s3_run'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507850000_coverage_recipe_business_person_lei.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507850000_coverage_recipe_business_person_lei.down.sql"))
