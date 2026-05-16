"""Convert 8 single-task wrappers to kind=single_task (P3, ADR-2605080600)."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509160000_topology_single_task_8"
down_revision = "r_20260509150000_topology_bulk_51"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509160000_topology_single_task_8.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509160000_topology_single_task_8.down.sql"))
