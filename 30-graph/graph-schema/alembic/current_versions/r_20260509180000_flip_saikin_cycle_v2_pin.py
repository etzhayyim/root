"""Flip saikin.cycle deployment pin v1 → v2 (ADR-2605082000 PoC go-live).

Operator gate: do NOT apply unless the 5 pre-conditions in
`sql_migrations/20260509180000_flip_saikin_cycle_v2_pin.up.sql` are verified.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509180000_flip_saikin_cycle_v2_pin"
down_revision = "r_20260509170000_topology_saikin_cycle_v2_mcp"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509180000_flip_saikin_cycle_v2_pin.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509180000_flip_saikin_cycle_v2_pin.down.sql"))
