"""vertex_maps_gsplat_mesh — splat→mesh bake artifact registry.

ADR 2605092800 §D6. Adds 1 vertex table that stores the baked GLB
metadata (b2_key, triangle_count, baked_at) for each splat asset
that has been mesh-extracted. The lineage edge
`edge_maps_gsplat_baked_to` (shipped in `r_20260509220000_*`) joins
this mesh row's `vertex_id` to the source splat's `vertex_id`.

Persistence model = root CLAUDE.md "Record-log semantics": no UPDATE,
no ON CONFLICT. PK re-INSERT = implicit upsert. Append-only.

Worker contract: bulk-ingest gsplat_train_dumper.py mode=bake writes
1 row here + 1 edge row per successful RunPod bake response.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510120000_vertex_maps_gsplat_mesh"
down_revision = "r_20260509220000_vertex_maps_gsplat_asset"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510120000_vertex_maps_gsplat_mesh.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510120000_vertex_maps_gsplat_mesh.down.sql"),
    )
