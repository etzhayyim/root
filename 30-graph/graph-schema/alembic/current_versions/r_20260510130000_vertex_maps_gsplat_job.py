"""vertex_maps_gsplat_job — gsplat job-state log + latest-state MV.

ADR 2605092800 §D7. Append-only. One row per phase transition
(emitted by `gsplat_train_dumper.py`). The streaming MV
`mv_maps_gsplat_job_latest` projects DISTINCT ON (job_id) so the
worker's `cmdGetGsplatJobStatus` is a single sub-ms index lookup.

Persistence model = "Record-log semantics": no UPDATE, no
ON CONFLICT. Each phase is a new row keyed by (job_id, ts) — the
MV deduplicates by latest ts per job_id. Window cap = 7 days so
the agg state stays bounded.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510130000_vertex_maps_gsplat_job"
down_revision = "r_20260510120000_vertex_maps_gsplat_mesh"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510130000_vertex_maps_gsplat_job.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510130000_vertex_maps_gsplat_job.down.sql"),
    )
