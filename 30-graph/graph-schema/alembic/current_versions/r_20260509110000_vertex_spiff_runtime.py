"""vertex_spiff_runtime — SpiffWorkflow runtime state on RisingWave.

ADR 2605081200 (PoC Phase 1). Adds 4 vertex tables + 1 streaming MV for the
SpiffWorkflow BPMN engine adopted as the Zeebe replacement. Spec layer
(`vertex_bpmn_process_def` / `vertex_bpmn_lexicon_binding`) is engine-agnostic
and reused as-is from `migrations/20260423000000_vertex_bpmn_actor_def.ts`.

Namespace `vertex_spiff_*` (NOT `vertex_bpmn_*`) is intentional: the legacy
Camunda 8 (Zeebe) runtime tables `vertex_bpmn_instance` /
`vertex_bpmn_activity_event` / `vertex_bpmn_signal_log` exist with a
different schema and active consumers (`50-infra/cloudflare/workers/graph`).
Both runtimes coexist; legacy retires after Zeebe broker decommission.

Persistence model = root CLAUDE.md "Record-log semantics": no UPDATE,
no ON CONFLICT. PK re-INSERT = implicit upsert. Engine host serializes
BpmnWorkflow → JSON, writes 1 row per instance per token transition.
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260509110000_vertex_spiff_runtime"
down_revision = "r_20260509100000_vertex_langgraph_assistant_registry"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509110000_vertex_spiff_runtime.up.sql"))


def downgrade() -> None:
    execute_sql_text(op.get_bind(), _read("20260509110000_vertex_spiff_runtime.down.sql"))
