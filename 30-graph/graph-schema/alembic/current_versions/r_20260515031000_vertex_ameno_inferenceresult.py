"""vertex_ameno_inferenceresult — ameno browser inference result table (ADR-2605111200).

Phase 5i — Alembic counterpart of the Phase 2 Kysely file
`migrations/20260515031000_vertex_ameno_inferenceresult.ts`. The Kysely
file landed before the agent context surfaced
`30-graph/graph-schema/CLAUDE.md`'s rule that all new graph-schema DDL
must go through Alembic; this revision closes that gap so
`pnpm db:migrate` actually picks the table up. The Kysely file is kept
in place as historical lineage per the same CLAUDE.md.

Filename timestamp (20260515031000) mirrors the Kysely file for
traceability; `down_revision` chains off the current Alembic head, so
ordering on disk does not match logical ordering by design.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260515031000_vertex_ameno_inferenceresult"
down_revision = "r_20260515150000_vertex_akuma_redteam_scope"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260515031000_vertex_ameno_inferenceresult.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260515031000_vertex_ameno_inferenceresult.down.sql"))
