"""Akuma authorized red team scope/probe/finding/audit graph (ADR-2605151400)."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260515150000_vertex_akuma_redteam_scope"
down_revision = "r_202605150002_jukyu_entity_vessel_transport"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260515150000_vertex_akuma_redteam_scope.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260515150000_vertex_akuma_redteam_scope.down.sql"))
