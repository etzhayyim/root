"""Converted from Kysely migration 20260430500000_idx_bpmn_lexicon_binding_nsid."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260430500000_idx_bpmn_lexicon_binding_nsid"
down_revision = 'r_20260430404000_rw_stability_probe_noop_2'
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260430500000_idx_bpmn_lexicon_binding_nsid.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260430500000_idx_bpmn_lexicon_binding_nsid.down.sql"))
