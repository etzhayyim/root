"""seed: 6 compose_scene_3d MCP tools in vertex_mcp_tool_def

P8 of ADR-2605141200. Registers loadPanelPlan / resolveAssets / placeScene /
simulateCharacter / renderKeyframes / persistScene3d so the LangGraph
topology resolver (pymagatama.langgraph_node_resolvers._resolve_mcp_nsid)
can route mcp://com.etzhayyim.apps.mangaka.tools.* to mangaka.etzhayyim.com/xrpc.

Phase A (current): `compose_scene_3d` runs via py_factory + in-tree
delegation to `lg_mangaka.tools`. These rows are inert until Phase C
flips the topology deployment (P10).
Phase C (P10): topology assistant node `kind=mcp_tool ref=mcp://...`
resolves via these rows. No new dispatch path — sync-mcp-registry.py
upserts when the lexicon JSON changes.

Revision ID: r_20260514140000_seed_mangaka_compose_scene_3d_mcp_tools
Revises: r_20260514130000_seed_mangaka_compose_scene_3d_assistant
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text as _text


revision = "r_20260514140000_seed_mangaka_compose_scene_3d_mcp_tools"
down_revision = "r_20260514130000_seed_mangaka_compose_scene_3d_assistant"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def _execute_sql_text(bind, sql: str) -> None:
    """RW lacks Postgres's full multi-statement DDL — split + execute. The
    seed body contains a single multi-row INSERT followed by FLUSH;
    splitting on `;` keeps both statements distinct."""
    for stmt in sql.split(";"):
        s = stmt.strip()
        if s:
            bind.execute(_text(s))


def upgrade() -> None:
    _execute_sql_text(
        op.get_bind(),
        _read("20260514140000_seed_mangaka_compose_scene_3d_mcp_tools.up.sql"),
    )


def downgrade() -> None:
    _execute_sql_text(
        op.get_bind(),
        _read("20260514140000_seed_mangaka_compose_scene_3d_mcp_tools.down.sql"),
    )
