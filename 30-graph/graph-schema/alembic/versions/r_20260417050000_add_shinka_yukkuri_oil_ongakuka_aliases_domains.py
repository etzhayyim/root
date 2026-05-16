"""Converted from Kysely migration 20260417050000_add_shinka_yukkuri_oil_ongakuka_aliases_domains."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260417050000_add_shinka_yukkuri_oil_ongakuka_aliases_domains"
down_revision = 'r_20260417040000_yoro_auth_domains_final_collection_mappings'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417050000_add_shinka_yukkuri_oil_ongakuka_aliases_domains.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260417050000_add_shinka_yukkuri_oil_ongakuka_aliases_domains.down.sql"))
