"""Converted from Kysely migration 0039_split_chizai_to_chosakuken_shohyo."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_0039_split_chizai_to_chosakuken_shohyo"
down_revision = 'r_0038_mv_world_vertex_per_host_ip_cluster'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0039_split_chizai_to_chosakuken_shohyo.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("0039_split_chizai_to_chosakuken_shohyo.down.sql"))
