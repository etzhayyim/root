"""Jukyu legal entity, vessel, and transport graph links."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_202605150002_jukyu_entity_vessel_transport"
down_revision = "r_20260514193000_vertex_shinshi_aesthetic_review_cache"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("202605150002_jukyu_entity_vessel_transport.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("202605150002_jukyu_entity_vessel_transport.down.sql"))
