"""vertex_maps_gsplat_job.cost_usd — record per-job RunPod cost.

ADR 2605092800 §D14. Adds nullable `cost_usd` column, recreates the
streaming MV `mv_maps_gsplat_job_latest` so the new column is in its
SELECT list. RisingWave does not support ALTER on a MV body — the
DROP + CREATE in the SQL is idempotent and matches the "Record-log
semantics" convention.

The dumper writes this from the RunPod response's
`stats.estimatedCostUsd` (handler computes
`runtime_ms × RUNPOD_COST_USD_PER_SEC`). Locking the cost at job-time
keeps month-over-month rollups stable when the rate env var changes.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260510140000_alter_gsplat_job_cost_usd"
down_revision = "r_20260510130000_vertex_maps_gsplat_job"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510140000_alter_gsplat_job_cost_usd.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260510140000_alter_gsplat_job_cost_usd.down.sql"),
    )
