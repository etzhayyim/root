"""BMC lean iteration loop graph — record-log SSoT for lg-yatabase.

5 vertex tables + 5 edge tables + 4 streaming MVs supporting the
`bmc_iteration` LangGraph running inside the lg-yatabase Granian pod
(mitama-yata-pool). The pod is the single writer; yatabase CF Worker
is a stateless XRPC forwarder.

Vertices:

* `vertex_bmc_state`              — canvas snapshot, append-only versioned
* `vertex_bmc_hypothesis`         — immutable spec keyed by slug
* `vertex_bmc_hypothesis_event`   — status transition log (UPDATE-free)
* `vertex_bmc_iteration`          — one row per Build-Measure-Learn cycle
* `vertex_bmc_decision`           — persevere / pivot / kill / extend
* `vertex_bmc_metric_sample`      — measurement raw sidecar (replay)

Edges (GraphAr-native, CSR via idx on src_vid):

* `edge_bmc_state_supersedes`         — version chain (v_n -> v_{n-1})
* `edge_bmc_hypothesis_in_block`      — hyp -> 9 BMC blocks
* `edge_bmc_iteration_of_hypothesis`  — iter -> hyp
* `edge_bmc_decision_of_iteration`    — dec -> iter
* `edge_bmc_pivot_applied_to_state`   — decision -> new bmc_state row

Materialized views (all cardinality-bounded, MV-safe):

* `mv_bmc_state_head`        — 1 row per org_did (current canvas)
* `mv_bmc_hypothesis_status` — DISTINCT ON (slug, org) status latest
* `mv_bmc_iteration_latest`  — DISTINCT ON (slug, org) iteration latest
* `mv_bmc_block_health`      — block x org rollup (Studio left pane)
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

from graph_schema.db import execute_sql_text


revision = "r_20260512000000_bmc_lean_iteration"
down_revision = "r_20260511000000_p2_bq_target_vertices"
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]


def _read(name: str) -> str:
    return (ROOT / "sql_migrations" / name).read_text(encoding="utf-8")


def upgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260512000000_bmc_lean_iteration.up.sql"),
    )


def downgrade() -> None:
    execute_sql_text(
        op.get_bind(),
        _read("20260512000000_bmc_lean_iteration.down.sql"),
    )
