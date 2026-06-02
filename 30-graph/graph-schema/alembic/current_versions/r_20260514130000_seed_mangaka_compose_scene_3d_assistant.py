"""seed: mangaka compose_scene_3d assistant + deployment

Registers `com.etzhayyim.apps.mangaka.composeScene3d` in the RW-resident LangGraph
SSoT (ADR-2605082000) so the bpmn-dispatcher → /runs router can route NSID
→ assistant. Phase A uses kind='py_factory'; Phase B/C switches to
kind='topology' from compose_scene_3d.topology.yaml once the 6 pending MCP
tools land.

Revision ID: r_20260514130000_seed_mangaka_compose_scene_3d_assistant
Revises: r_20260514120000
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text as _text


revision = "r_20260514130000_seed_mangaka_compose_scene_3d_assistant"
down_revision = "r_20260514120000"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def _execute_sql_text(bind, sql: str) -> None:
    """RW lacks Postgres's full multi-statement DDL — split + execute."""
    for stmt in sql.split(";"):
        s = stmt.strip()
        if s:
            bind.execute(_text(s))


def upgrade() -> None:
    _execute_sql_text(
        op.get_bind(),
        _read("20260514130000_seed_mangaka_compose_scene_3d_assistant.up.sql"),
    )


def downgrade() -> None:
    _execute_sql_text(
        op.get_bind(),
        _read("20260514130000_seed_mangaka_compose_scene_3d_assistant.down.sql"),
    )
