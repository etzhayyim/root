"""organism_ecosystem_schema — Bonsai cultivar + Ecosystem-as-Model FP8 substrate.

Implements schema for ADRs:
  * 2605091300 Bonsai Cultivar Layer
  * 2605091400 MCP-as-Cell-Membrane (no schema, governance only)
  * 2605091500 Mycorrhizal Watering & Consent-Gated Mutation
    → edge_bonsai_water, vertex_water_consent_grant
  * 2605091600 Plasmid + Graft Horizontal Acquisition
    → vertex_kobo_plasmid, edge_kobo_plasmid_carry, edge_yoro_graft
  * 2605091800 Pruning Protocol (6-tier)
    → edge_yoro_prune
  * 2605091900 Yoro Flower→Fruit Lifecycle
    → vertex_yoro_flower, vertex_yoro_fruit, edge_yoro_pollinate
  * 2605092000 Ecosystem-as-Model Unified FP8 Vector Substrate
    → vertex_organism_embedding, vertex_model_checkpoint
  * 2605092100 LoRA-per-Cell (uses vertex_organism_embedding modality='adapter')
  * 2605092200 Continuous Metabolic Training
    → edge_gradient_flow + 3 streaming MVs
  * 2605092300 FP8 Train+Inference Colocation (runtime config; no schema)
  * 2605092400 Tool Weight as Learnable Plasmid Affinity
    → vertex_router_weight
  * 2605092500 Reasoning as Sap-Flow Walk (uses existing
    vertex_langgraph_graph_def + vertex_organism_checkpoint from prior
    karma migrations).

Persistence model = root CLAUDE.md "Record-log semantics":
  no UPDATE, no ON CONFLICT. PK re-INSERT = implicit upsert.
Field encryption for private text uses `signal:v1:{ciphertext}` per
  ADR-2605081300 vault zero-knowledge invariant.
FP8 tensor columns are BYTEA (D bytes E4M3) + REAL scale; dequant on read.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509500000_organism_ecosystem_schema"
down_revision = "r_20260509450000_copyright_ingest_v3_full_chain"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509500000_organism_ecosystem_schema.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509500000_organism_ecosystem_schema.down.sql"))
