"""hatsubai (発売) — console publishing pipeline schema.

11 vertex + 7 edge + 5 streaming MV + 8 indexes covering Nintendo
Switch 2 / PS5 / Xbox Series X|S / Steam partner→devkit→build→TRC
→cert→rating→listing→asset flow under one ``hatsubai.etzhayyim.com`` actor
(BPMN-as-actor; no CF Worker — see ``60-apps/etzhayyim-project-hatsubai``).

Per-platform variation is one ``platform_code`` column; cross-platform
queries (release calendar, blocker rollup, devkit utilization) stay
single-statement. AT Lexicon float ban → all monetary / proportional
fields are scaled BIGINT (``price_minor`` cents, ``revshare_bps``
basis-points 0-10000).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510160000_vertex_hatsubai_console_publishing"
down_revision = "r_20260510150000_alter_gsplat_job_imageids_hash"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510160000_vertex_hatsubai_console_publishing.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510160000_vertex_hatsubai_console_publishing.down.sql"),
    )
