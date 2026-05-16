"""Register site_common_crawl_ingest LangGraph assistant."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510100000_seed_site_common_crawl_langgraph"
down_revision = "r_20260509500000_organism_ecosystem_schema"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510100000_seed_site_common_crawl_langgraph.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260510100000_seed_site_common_crawl_langgraph.down.sql"))
