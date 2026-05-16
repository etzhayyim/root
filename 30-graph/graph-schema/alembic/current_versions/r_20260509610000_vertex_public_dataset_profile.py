"""vertex_public_dataset_profile — BigQuery P1 profiling schema.

ADR 2605092700 §P1 Profiling. Adds the canonical RisingWave surface for
the BigQuery public dataset P1 pass. P1 only runs against P0 candidates
that have a `vertex_public_dataset_catalog` row with `review_status`
advanced past 'pending'; this migration provisions the tables but does
not seed any rows.

Tables added:
* `vertex_public_dataset_profile` — per (table, profile_run) summary of
  keys, null rates, distinct estimates, top values, text/language
  distribution, geo coverage, PII signal, license + training decision,
  dedupe + delta strategy, recommended RisingWave targets, refresh-cost
  estimate, profile artifact URI.
* `edge_public_dataset_profiles_table` — profile → table lineage.
* `edge_public_dataset_candidate_for_vertex_type` — profile → target
  RisingWave vertex label candidate (many-to-many, with mapping_quality
  and column_mapping_json).
* `edge_public_dataset_candidate_for_training_task` — profile → training
  task candidate. License + PII gates inherit from the parent profile.
* `edge_dataset_produces_vertex_type` — decided binding (catalog →
  target vertex label) after P1 review. Promoted from candidate.
* `edge_dataset_allowed_for_training_task` — decided allowlist (catalog
  → training task). Default-deny; only rows in this table feed the
  training eligibility MV.
* `mv_public_dataset_profile_rank` — per-dataset rank by review status
  and refresh cost.
* `mv_training_source_eligibility` — default-deny eligibility surface;
  exposes the join over `edge_dataset_allowed_for_training_task` plus
  catalog state.
* `mv_public_dataset_ingest_status` — provider × ingest_mode rollup.

P2 production projection (writing into domain `vertex_*` / `edge_*`)
remains explicitly out of scope per the ADR; this migration only
expresses the design surface that P2 must pull from.

Persistence model = root CLAUDE.md "Record-log semantics": no UPDATE,
no ON CONFLICT. PK re-INSERT = implicit upsert. Append-only.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509610000_vertex_public_dataset_profile"
down_revision = "r_20260509600000_vertex_public_dataset_catalog"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260509610000_vertex_public_dataset_profile.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260509610000_vertex_public_dataset_profile.down.sql"),
    )
