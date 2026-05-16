"""P2 BigQuery target vertex tables — 10 new vertices per ADR-2605101000.

Reified targets for the Tier 1 binding decisions recorded in
`edge_dataset_produces_vertex_type`:

* `vertex_air_quality_observation` ← epa_historical_air_quality
* `vertex_taxi_trip` ← new_york_taxi_trips + chicago_taxi_trips (shared)
* `vertex_qa_post` ← stackoverflow (CC-BY-SA-4.0, ShareAlike propagates)
* `vertex_marine_observation` ← noaa_icoads
* `vertex_synthetic_patient` ← cms_synthetic_patient_data_omop
* `vertex_forest_inventory` ← usfs_fia
* `vertex_target_evidence` ← open_targets_platform
* `vertex_chemistry_patent` ← ebi_surechembl
* `vertex_blockchain_block` ← crypto_litecoin + crypto_dogecoin (shared,
  keyed on `chain_id`)
* `vertex_blockchain_tx` ← same

Persistence: record-log semantics, no ON CONFLICT, PK re-INSERT = upsert.
Adapters under `70-tools/scripts/projection/bigquery/<dataset>.mjs` are
the only sanctioned write path (plus the canonical Kysely export from
graph-schema).
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260511000000_p2_bq_target_vertices"
down_revision = "r_20260509610000_vertex_public_dataset_profile"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260511000000_p2_bq_target_vertices.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260511000000_p2_bq_target_vertices.down.sql"),
    )
