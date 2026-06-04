"""topology: compose_scene_3d v2 (replace py_factory with kind=topology)

P10 of ADR-2605141200 — flip `com.etzhayyim.apps.mangaka.composeScene3d` from
the Phase A `py_factory` shape to the Phase C `topology` shape that the
RW-resident loader (`pymagatama.langgraph_loader._compile_topology`)
materialises into a LangGraph StateGraph at /runs activation time.

The topology spec comes from `compose_scene_3d.topology.yaml` (the SSoT
maintained alongside the lg_mangaka package). This revision loads the
YAML at upgrade time, derives the `vertex_langgraph_assistant.spec`
JSON (state_keys / entry / edges / conditional_edges) and emits one
`vertex_langgraph_assistant_node` row per topology node (binding kind +
ref + config). The `vertex_langgraph_deployment` row gets a fresh
`updated_at` so the watcher re-compiles.

Rollback (downgrade) re-applies the Phase A py_factory row content
(mirrors `r_20260514130000_seed_mangaka_compose_scene_3d_assistant`) and
deletes the per-node binding rows.

Revision ID: r_20260514170000_topology_compose_scene_3d
Revises: r_20260514160000_seed_mangaka_aggregate_critique_mcp_tool
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from alembic import op
from sqlalchemy import text as _text


revision = "r_20260514170000_topology_compose_scene_3d"
down_revision = "r_20260514160000_seed_mangaka_aggregate_critique_mcp_tool"
branch_labels = None
depends_on = None


# Repo-relative path to the topology SSoT. Resolved against the repo root
# at upgrade time. Keeping the YAML out of the migration body means future
# tweaks to the prompt bodies / state keys land in one place — the
# topology test (`tests/test_compose_scene_3d_topology.py`) guards drift.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_TOPOLOGY_YAML = (
    _REPO_ROOT
    / "60-apps"
    / "etzhayyim-project-mangaka"
    / "lg"
    / "lg_mangaka"
    / "graphs"
    / "compose_scene_3d.topology.yaml"
)

_ASSISTANT_ID = "com.etzhayyim.apps.mangaka.composeScene3d"
_NSID = "com.etzhayyim.apps.mangaka.composeScene3d"
_APP_DID = "did:web:mangaka.etzhayyim.com"
_NOW_ISO = "2026-05-14T17:00:00Z"
_NOW_DATE = "2026-05-14"


def _load_topology() -> dict[str, Any]:
    import yaml  # imported lazily so non-mangaka migrations don't need PyYAML

    raw = _TOPOLOGY_YAML.read_text(encoding="utf-8")
    spec = yaml.safe_load(raw)
    if not isinstance(spec, dict):
        raise RuntimeError(f"topology YAML at {_TOPOLOGY_YAML} did not parse as a mapping")
    return spec


def _spec_json(topology: dict[str, Any]) -> str:
    """Project the YAML down to just the fields `_compile_topology` reads."""
    spec_obj = {
        "state_keys": topology.get("state_keys") or [],
        "entry": topology["entry"],
        "edges": topology.get("edges") or [],
        "conditional_edges": topology.get("conditional_edges") or [],
    }
    return json.dumps(spec_obj, ensure_ascii=False, separators=(",", ":"))


def _node_rows(topology: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for n in topology.get("nodes") or []:
        node_id = n["id"]
        kind = n["kind"]
        ref = n.get("ref", "")
        config = n.get("config")
        rows.append(
            {
                "vertex_id": f"{_ASSISTANT_ID}:{node_id}",
                "assistant_id": _ASSISTANT_ID,
                "node_id": node_id,
                "kind": kind,
                "ref": ref,
                "config": json.dumps(config, ensure_ascii=False, separators=(",", ":"))
                if config is not None
                else None,
            }
        )
    return rows


def upgrade() -> None:
    topology = _load_topology()
    spec_json = _spec_json(topology)
    node_rows = _node_rows(topology)

    bind = op.get_bind()

    # 1. Replace the v1 py_factory assistant row with the v2 topology row.
    #    Same vertex_id → RW PK upsert (saikin.cycle.v1 pattern, same migration shape).
    bind.execute(
        _text(
            """
            INSERT INTO vertex_langgraph_assistant
              (vertex_id, _seq, sensitivity_ord, owner_did,
               assistant_id, version, kind, factory_path, spec,
               description, created_at)
            VALUES
              (:vertex_id, 0, 0, :owner_did,
               :assistant_id, 1, 'topology', NULL, :spec,
               :description, :created_at)
            """
        ),
        {
            "vertex_id": _ASSISTANT_ID,
            "owner_did": _APP_DID,
            "assistant_id": _ASSISTANT_ID,
            "spec": spec_json,
            "description": (
                "mangaka compose_scene_3d — Phase C topology (ADR-2605141200 P10). "
                "9 super-step Pregel + 2 P10.2 validators wired to MCP tools / vision LLM."
            ),
            "created_at": _NOW_ISO,
        },
    )

    # 2. Per-node bindings — one row per `nodes[]` entry from the YAML.
    for row in node_rows:
        bind.execute(
            _text(
                """
                INSERT INTO vertex_langgraph_assistant_node
                  (vertex_id, _seq, sensitivity_ord, owner_did,
                   assistant_id, node_id, kind, ref, config, created_at)
                VALUES
                  (:vertex_id, 0, 0, :owner_did,
                   :assistant_id, :node_id, :kind, :ref, :config, :created_at)
                """
            ),
            {
                "vertex_id": row["vertex_id"],
                "owner_did": _APP_DID,
                "assistant_id": row["assistant_id"],
                "node_id": row["node_id"],
                "kind": row["kind"],
                "ref": row["ref"],
                "config": row["config"],
                "created_at": _NOW_ISO,
            },
        )

    # 3. Bump the deployment row's updated_at so the watcher detects the change
    #    and re-compiles. PK = nsid → re-INSERT overwrites.
    bind.execute(
        _text(
            """
            INSERT INTO vertex_langgraph_deployment
              (vertex_id, _seq, sensitivity_ord, owner_did,
               nsid, assistant_id, version, status, replicas, updated_at)
            VALUES
              (:vertex_id, 0, 0, :owner_did,
               :nsid, :assistant_id, 1, 'active', 1, :updated_at)
            """
        ),
        {
            "vertex_id": _NSID,
            "owner_did": _APP_DID,
            "nsid": _NSID,
            "assistant_id": _ASSISTANT_ID,
            "updated_at": _NOW_ISO,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()

    # Re-apply the Phase A py_factory shape — mirrors the content of
    # r_20260514130000_seed_mangaka_compose_scene_3d_assistant. PK upsert.
    bind.execute(
        _text(
            """
            INSERT INTO vertex_langgraph_assistant
              (vertex_id, _seq, sensitivity_ord, owner_did,
               assistant_id, version, kind, factory_path, spec,
               description, created_at)
            VALUES
              (:vertex_id, 0, 0, :owner_did,
               :assistant_id, 1, 'py_factory',
               'lg_mangaka.graphs.compose_scene_3d:build_graph', NULL,
               :description, :created_at)
            """
        ),
        {
            "vertex_id": _ASSISTANT_ID,
            "owner_did": _APP_DID,
            "assistant_id": _ASSISTANT_ID,
            "description": (
                "mangaka compose_scene_3d — 9 super-step Pregel "
                "(P0–P5 of ADR-2605141200) — Phase A (rolled back from Phase C)."
            ),
            "created_at": _NOW_ISO,
        },
    )

    # Drop every per-node binding row.
    bind.execute(
        _text("DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = :aid"),
        {"aid": _ASSISTANT_ID},
    )

    # Bump deployment.updated_at so the watcher picks up the rollback.
    bind.execute(
        _text(
            """
            INSERT INTO vertex_langgraph_deployment
              (vertex_id, _seq, sensitivity_ord, owner_did,
               nsid, assistant_id, version, status, replicas, updated_at)
            VALUES
              (:vertex_id, 0, 0, :owner_did,
               :nsid, :assistant_id, 1, 'active', 1, :updated_at)
            """
        ),
        {
            "vertex_id": _NSID,
            "owner_did": _APP_DID,
            "nsid": _NSID,
            "assistant_id": _ASSISTANT_ID,
            "updated_at": _NOW_ISO,
        },
    )
