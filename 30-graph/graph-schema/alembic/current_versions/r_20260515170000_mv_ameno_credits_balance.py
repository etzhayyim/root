"""mv_ameno_credits_balance — per-user credit balance for ameno Tier 2 reward loop.

Phase 5j — closes the read side of Phase 5c. Streams an aggregate from
vertex_credits_af_event so listMyCredits can answer
"how many credits has this actor earned from browser inference?" in
O(1) instead of scanning the AF event log per call.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260515170000_mv_ameno_credits_balance"
down_revision = "r_20260515031000_vertex_ameno_inferenceresult"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260515170000_mv_ameno_credits_balance.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260515170000_mv_ameno_credits_balance.down.sql"))
