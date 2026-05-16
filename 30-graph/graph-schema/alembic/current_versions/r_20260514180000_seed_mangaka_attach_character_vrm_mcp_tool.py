"""seed: attachCharacterVrm MCP tool

P13 of ADR-2605141200. Registers the VRM ingestion tool in the MCP
registry. Body lives in `lg_mangaka.tools.tool_attach_character_vrm`
and is dispatched via the pod XRPC `/xrpc/{nsid}` route (server.py P9).

Revision ID: r_20260514180000_seed_mangaka_attach_character_vrm_mcp_tool
Revises: r_20260514170000_topology_compose_scene_3d
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text as _text


revision = "r_20260514180000_seed_mangaka_attach_character_vrm_mcp_tool"
down_revision = "r_20260514170000_topology_compose_scene_3d"
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
        _read("20260514180000_seed_mangaka_attach_character_vrm_mcp_tool.up.sql"),
    )


def downgrade() -> None:
    _execute_sql_text(
        op.get_bind(),
        _read("20260514180000_seed_mangaka_attach_character_vrm_mcp_tool.down.sql"),
    )
