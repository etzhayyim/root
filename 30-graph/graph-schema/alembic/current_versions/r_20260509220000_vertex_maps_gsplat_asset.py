"""vertex_maps_gsplat_asset — KAMI Gsplat preview asset registry.

ADR 2605092800. Adds 1 vertex + 1 edge table backing the splat preview /
QC path in maps.etzhayyim.com. The asset binary lives in B2 (`b2_key`); this
row holds metadata only. Lineage to baked mesh tiles is captured by
`edge_maps_gsplat_baked_to`.

Persistence model = root CLAUDE.md "Record-log semantics": no UPDATE,
no ON CONFLICT. PK re-INSERT = implicit upsert. Append-only.

Spec / runtime separation: this migration creates *only* metadata
tables. The bake pipeline that populates them runs as a Vultr k8s pod
(ADR 2604251830 L8) and is gated by ops bring-up — see
`60-apps/etzhayyim-project-maps/CLAUDE.md` §Gsplat Preview / Bake.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509220000_vertex_maps_gsplat_asset"
down_revision = "r_20260510100000_seed_site_common_crawl_langgraph"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260509220000_vertex_maps_gsplat_asset.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260509220000_vertex_maps_gsplat_asset.down.sql"),
    )
