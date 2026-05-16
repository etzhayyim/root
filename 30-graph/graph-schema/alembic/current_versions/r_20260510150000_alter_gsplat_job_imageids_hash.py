"""vertex_maps_gsplat_job.imageids_hash — train idempotency hash.

ADR 2605092800 §D16. Adds nullable `imageids_hash VARCHAR` column,
recreates `mv_maps_gsplat_job_latest` to surface it. Dumper writes
the SHA-256 of the sorted, comma-joined Mapillary imageIds set; on
re-train of the same tile with the same image set, the dumper
short-circuits to a `phase=skipped-duplicate` row instead of
re-running COLMAP + gsplat ($-saving).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510150000_alter_gsplat_job_imageids_hash"
down_revision = "r_20260510140000_alter_gsplat_job_cost_usd"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510150000_alter_gsplat_job_imageids_hash.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510150000_alter_gsplat_job_imageids_hash.down.sql"),
    )
