"""seed: validateCameraPlan MCP tool

P10.2 of ADR-2605141200 — plugs the cinematography-output validator
between the LLM node (`kind=llm`) and the simulate_one fan-out. The
validator body lives in `lg_mangaka.tools.tool_validate_camera_plan` and
is dispatched via the pod XRPC `/xrpc/{nsid}` route (server.py P9).

Revision ID: r_20260514150000_seed_mangaka_validate_camera_plan_mcp_tool
Revises: r_20260514140000_seed_mangaka_compose_scene_3d_mcp_tools
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text as _text


revision = "r_20260514150000_seed_mangaka_validate_camera_plan_mcp_tool"
down_revision = "r_20260514140000_seed_mangaka_compose_scene_3d_mcp_tools"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def _execute_sql_text(bind, sql: str) -> None:
    for stmt in sql.split(";"):
        s = stmt.strip()
        if s:
            bind.execute(_text(s))


def upgrade() -> None:
    _execute_sql_text(
        op.get_bind(),
        _read("20260514150000_seed_mangaka_validate_camera_plan_mcp_tool.up.sql"),
    )


def downgrade() -> None:
    _execute_sql_text(
        op.get_bind(),
        _read("20260514150000_seed_mangaka_validate_camera_plan_mcp_tool.down.sql"),
    )
