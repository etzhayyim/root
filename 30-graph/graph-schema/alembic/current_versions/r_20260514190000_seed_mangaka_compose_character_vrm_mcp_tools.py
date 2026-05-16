"""seed: compose_character_vrm MCP tools (7 new rows)

P16-b of ADR-2605141200. Registers the 7 NEW MCP tools backing
`compose_character_vrm.topology.yaml`. attachCharacterVrm (P13) is
already registered by r_20260514180000 and is the 8th Pregel node;
this revision covers the upstream pipeline.

Self-hosted invariant: every tool's pod image is `ghcr.io/gftdcojp/*`
running open-weight / OSS models on the VKE pool. External commercial
APIs are train-only teacher signals — see
`data/ghosthacker/TRAINING_PIPELINE.md`.

Revision ID: r_20260514190000_seed_mangaka_compose_character_vrm_mcp_tools
Revises: r_20260514180000_seed_mangaka_attach_character_vrm_mcp_tool
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text as _text


revision = "r_20260514190000_seed_mangaka_compose_character_vrm_mcp_tools"
down_revision = "r_20260514180000_seed_mangaka_attach_character_vrm_mcp_tool"
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
        _read("20260514190000_seed_mangaka_compose_character_vrm_mcp_tools.up.sql"),
    )


def downgrade() -> None:
    _execute_sql_text(
        op.get_bind(),
        _read("20260514190000_seed_mangaka_compose_character_vrm_mcp_tools.down.sql"),
    )
