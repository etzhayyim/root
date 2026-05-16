"""vertex_codebase_analysis — codebase feature audits as graph data."""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509070000_vertex_codebase_analysis"
down_revision = "live_risingwave_20260508"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509070000_vertex_codebase_analysis.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509070000_vertex_codebase_analysis.down.sql"))
