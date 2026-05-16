"""Converted from Kysely migration 20260507770000_agent_minimax_uncertainty."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260507770000_agent_minimax_uncertainty"
down_revision = 'r_20260507765000_seed_ki_bpmn'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507770000_agent_minimax_uncertainty.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260507770000_agent_minimax_uncertainty.down.sql"))
