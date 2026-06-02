"""seed: vrmBindRetry DMN decision

P16-e of ADR-2605141200. Registers the DMN decision referenced by
`compose_character_vrm.topology.yaml` conditional_edges:
  condition_ref: dmn:com.etzhayyim.policies.mangaka.vrmBindRetry@1.0.0

Routing logic (FIRST):
  valid=true            -> accept (attach_vrm)
  valid=false, iter<2   -> retry  (bind_vrm)
  otherwise             -> reject (END, state.status='error')

SSoT XML lives at
`00-contracts/dmn/com/etzhayyim/policies/mangaka/vrmBindRetry.dmn` and is
duplicated verbatim inside `vertex_dmn_model.dmn_xml` for in-DB audit.

Revision ID: r_20260514200000_seed_mangaka_vrm_bind_retry_dmn
Revises: r_20260514190000_seed_mangaka_compose_character_vrm_mcp_tools
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text as _text


revision = "r_20260514200000_seed_mangaka_vrm_bind_retry_dmn"
down_revision = "r_20260514190000_seed_mangaka_compose_character_vrm_mcp_tools"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    # Single statement (INSERT … SELECT WHERE NOT EXISTS) — execute as
    # one block instead of split-on-semicolon, because the embedded
    # `$$ … $$` dollar-quoted JSON / XML bodies contain literal `;`
    # characters that would corrupt the SQL.
    op.get_bind().execute(
        _text(_read("20260514200000_seed_mangaka_vrm_bind_retry_dmn.up.sql"))
    )


def downgrade() -> None:
    op.get_bind().execute(
        _text(_read("20260514200000_seed_mangaka_vrm_bind_retry_dmn.down.sql"))
    )
