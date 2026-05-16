"""vertex_public_dataset_catalog — BigQuery P0 catalog/sample schema.

ADR 2605092700 §P0 Catalog/Sample. Adds the canonical RisingWave surface
for the BigQuery public dataset P0 pass:

* `vertex_public_dataset_catalog` — one row per (provider, dataset).
* `vertex_public_dataset_table`   — one row per BigQuery table.
* `vertex_public_dataset_sample`  — one row per bounded sample artifact.
* `vertex_bigquery_ingest_job`    — one row per BigQuery query job.
* `vertex_bigquery_export_artifact` — BigQuery-flavored export ledger
  (parallel to the generic `vertex_ingest_artifact` spine, kept separate
  per the ADR so BQ-specific cost/license fields stay typed).
* `vertex_bigquery_profile_run`   — per-batch run header (mode/budget).
* `mv_public_dataset_catalog_coverage` — provider rollup of missing
  metadata, license and review status. Bounded GROUP BY on `provider`
  (~50 distinct values) per CLAUDE.md MV memory guardrails.

P1 profile tables (`vertex_public_dataset_profile`,
`mv_public_dataset_profile_rank`, `mv_training_source_eligibility`,
`edge_dataset_*`) are explicitly out of scope for this revision and
land in a follow-up alembic step once P0 outputs have been reviewed.

Persistence model = root CLAUDE.md "Record-log semantics": no UPDATE,
no ON CONFLICT. PK re-INSERT = implicit upsert. Append-only.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509600000_vertex_public_dataset_catalog"
down_revision = "r_20260509220000_vertex_maps_gsplat_asset"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260509600000_vertex_public_dataset_catalog.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260509600000_vertex_public_dataset_catalog.down.sql"),
    )
