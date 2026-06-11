"""LangGraph OSS FastAPI server — lg-karma.

Wraps 45 task handlers from 8 kotodama.primitives.karma* modules.
All handlers use **kwargs so no camelCase conversion is needed.
No postgres checkpointer — stateless request-response graphs only.

Build:
  docker buildx build --platform linux/amd64 \\
    --build-context py=../../../40-engine/kotoba/crates/kotoba-kotodama/py \\
    -t ghcr.io/etzhayyim/lg-karma:0.1.0-amd64 --push .
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from kotodama.primitives.karma import (
    task_karma_anchor_backlink_edges,
    task_karma_anchor_compute_root,
    task_karma_anchor_submit_tx,
    task_karma_atrepo_find_unlifted,
    task_karma_atrepo_lift_batch,
    task_karma_coverage_snapshot,
    task_karma_edge_persist,
    task_karma_floor_gate,
    task_karma_input_validate,
    task_karma_ipfs_find_unpinned,
    task_karma_ipfs_pin_batch,
    task_karma_ipfs_verify_random,
    task_karma_organism_dissolve,
    task_karma_rebirth_emerge,
    task_karma_rebirth_forfeit,
    task_karma_rebirth_precheck,
    task_karma_rebirth_sever_follows,
    task_karma_rebirth_wipe_agents,
    task_karma_witness_persist,
)
from kotodama.primitives.karma_agent import task_karma_agent_evaluate
from kotodama.primitives.karma_dao import (
    task_karma_dao_cast_vote,
    task_karma_dao_finalize,
    task_karma_dao_find_voters,
    task_karma_dao_open_arbitration,
    task_karma_dao_sweep_expired,
)
from kotodama.primitives.karma_filecoin import (
    task_karma_filecoin_propose_batch,
    task_karma_filecoin_renew_expiring,
    task_karma_filecoin_status_get,
)
from kotodama.primitives.karma_resident import (
    task_karma_cohort_fission,
    task_karma_cohort_fission_scan,
    task_karma_organism_checkpoint,
    task_karma_organism_dissolve_runtime,
    task_karma_organism_harvest,
    task_karma_organism_resume,
    task_karma_organism_spawn,
    task_karma_organism_tick,
    task_karma_organism_tick_batch,
)
from kotodama.primitives.karma_wbt import (
    task_karma_wbt_balance_get,
    task_karma_wbt_forfeit_to_commons,
    task_karma_wbt_transfer,
)
from kotodama.primitives.karma_witness import (
    task_karma_witness_invite_fan_out,
    task_karma_witness_respond_to_invitation,
    task_karma_witness_sweep_expired,
)
from kotodama.primitives.karma_zk import (
    task_karma_zk_rebirth_proof_lookup,
    task_karma_zk_rebirth_verify,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

class _State(TypedDict, total=False):
    input: dict
    result: dict | None
    error: str | None


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def _make_single_node_graph(handler: Any, name: str):
    async def _node(state: _State) -> dict:
        kwargs = state.get("input") or {}
        try:
            return {"result": await handler(**kwargs)}
        except Exception as exc:  # noqa: BLE001
            log.exception("graph %s node error", name)
            return {"error": str(exc)[:300]}

    g = StateGraph(_State)
    g.add_node("execute", _node)
    g.add_edge(START, "execute")
    g.add_edge("execute", END)
    return g.compile(name=name)


def _make_health_graph():
    async def _node(state: _State) -> dict:
        return {"result": {"status": "ok", "service": "lg-karma"}}

    g = StateGraph(_State)
    g.add_node("ping", _node)
    g.add_edge(START, "ping")
    g.add_edge("ping", END)
    return g.compile(name="health")


# ---------------------------------------------------------------------------
# TASKS dict: NSID → handler (task type karma.X.Y → com.etzhayyim.apps.karma.XY)
# ---------------------------------------------------------------------------

TASKS: dict[str, Any] = {
    # karma.py
    "com.etzhayyim.apps.karma.inputValidate":        task_karma_input_validate,
    "com.etzhayyim.apps.karma.floorGate":            task_karma_floor_gate,
    "com.etzhayyim.apps.karma.edgePersist":          task_karma_edge_persist,
    "com.etzhayyim.apps.karma.organismDissolve":     task_karma_organism_dissolve,
    "com.etzhayyim.apps.karma.witnessPersist":       task_karma_witness_persist,
    "com.etzhayyim.apps.karma.ipfsFindUnpinned":     task_karma_ipfs_find_unpinned,
    "com.etzhayyim.apps.karma.ipfsPinBatch":         task_karma_ipfs_pin_batch,
    "com.etzhayyim.apps.karma.atrepoFindUnlifted":   task_karma_atrepo_find_unlifted,
    "com.etzhayyim.apps.karma.atrepoLiftBatch":      task_karma_atrepo_lift_batch,
    "com.etzhayyim.apps.karma.anchorComputeRoot":    task_karma_anchor_compute_root,
    "com.etzhayyim.apps.karma.anchorSubmitTx":       task_karma_anchor_submit_tx,
    "com.etzhayyim.apps.karma.anchorBacklinkEdges":  task_karma_anchor_backlink_edges,
    "com.etzhayyim.apps.karma.ipfsVerifyRandom":     task_karma_ipfs_verify_random,
    "com.etzhayyim.apps.karma.coverageSnapshot":     task_karma_coverage_snapshot,
    "com.etzhayyim.apps.karma.rebirthPrecheck":      task_karma_rebirth_precheck,
    "com.etzhayyim.apps.karma.rebirthForfeit":       task_karma_rebirth_forfeit,
    "com.etzhayyim.apps.karma.rebirthSeverFollows":  task_karma_rebirth_sever_follows,
    "com.etzhayyim.apps.karma.rebirthWipeAgents":    task_karma_rebirth_wipe_agents,
    "com.etzhayyim.apps.karma.rebirthEmerge":        task_karma_rebirth_emerge,
    # karma_agent.py
    "com.etzhayyim.apps.karma.agentEvaluate":        task_karma_agent_evaluate,
    # karma_dao.py
    "com.etzhayyim.apps.karma.daoFindVoters":        task_karma_dao_find_voters,
    "com.etzhayyim.apps.karma.daoOpenArbitration":   task_karma_dao_open_arbitration,
    "com.etzhayyim.apps.karma.daoCastVote":          task_karma_dao_cast_vote,
    "com.etzhayyim.apps.karma.daoFinalize":          task_karma_dao_finalize,
    "com.etzhayyim.apps.karma.daoSweepExpired":      task_karma_dao_sweep_expired,
    # karma_wbt.py
    "com.etzhayyim.apps.karma.wbtBalanceGet":        task_karma_wbt_balance_get,
    "com.etzhayyim.apps.karma.wbtTransfer":          task_karma_wbt_transfer,
    "com.etzhayyim.apps.karma.wbtForfeitToCommons":  task_karma_wbt_forfeit_to_commons,
    # karma_witness.py
    "com.etzhayyim.apps.karma.witnessInviteFanOut":          task_karma_witness_invite_fan_out,
    "com.etzhayyim.apps.karma.witnessRespondToInvitation":   task_karma_witness_respond_to_invitation,
    "com.etzhayyim.apps.karma.witnessSweepExpired":          task_karma_witness_sweep_expired,
    # karma_zk.py
    "com.etzhayyim.apps.karma.zkRebirthVerify":      task_karma_zk_rebirth_verify,
    "com.etzhayyim.apps.karma.zkRebirthProofLookup": task_karma_zk_rebirth_proof_lookup,
    # karma_filecoin.py
    "com.etzhayyim.apps.karma.filecoinProposeBatch":  task_karma_filecoin_propose_batch,
    "com.etzhayyim.apps.karma.filecoinRenewExpiring": task_karma_filecoin_renew_expiring,
    "com.etzhayyim.apps.karma.filecoinStatusGet":     task_karma_filecoin_status_get,
    # karma_resident.py
    "com.etzhayyim.apps.karma.organismSpawn":            task_karma_organism_spawn,
    "com.etzhayyim.apps.karma.organismTick":             task_karma_organism_tick,
    "com.etzhayyim.apps.karma.organismTickBatch":        task_karma_organism_tick_batch,
    "com.etzhayyim.apps.karma.organismCheckpoint":       task_karma_organism_checkpoint,
    "com.etzhayyim.apps.karma.organismResume":           task_karma_organism_resume,
    "com.etzhayyim.apps.karma.organismHarvest":          task_karma_organism_harvest,
    "com.etzhayyim.apps.karma.organismDissolveRuntime":  task_karma_organism_dissolve_runtime,
    "com.etzhayyim.apps.karma.cohortFission":            task_karma_cohort_fission,
    "com.etzhayyim.apps.karma.cohortFissionScan":        task_karma_cohort_fission_scan,
}


# ---------------------------------------------------------------------------
# GRAPHS dict + NSID → assistant map
# ---------------------------------------------------------------------------

GRAPHS: dict[str, Any] = {"health": _make_health_graph()}
GRAPHS.update({
    nsid.rsplit(".", 1)[-1]: _make_single_node_graph(handler, nsid.rsplit(".", 1)[-1])
    for nsid, handler in TASKS.items()
})

_NSID_TO_ASSISTANT: dict[str, str] = {"com.etzhayyim.apps.karma.health": "health"}
for _nsid in TASKS:
    _NSID_TO_ASSISTANT[_nsid] = _nsid.rsplit(".", 1)[-1]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_json(obj: Any) -> Any:
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(_app: FastAPI):
    log.info("lg-karma startup — %d graphs loaded", len(GRAPHS))
    yield
    log.info("lg-karma shutdown")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="lg-karma", lifespan=_lifespan)


@app.get("/ok")
async def ok():
    return {"ok": True}


@app.get("/health")
async def health():
    state = await GRAPHS["health"].ainvoke({"input": {}})
    return JSONResponse(state.get("result") or {"status": "ok"})


# ---------------------------------------------------------------------------
# /runs
# ---------------------------------------------------------------------------

@app.post("/runs")
async def runs(request: Request):
    body = await request.json()
    assistant_id: str = body.get("assistant_id", "health")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    graph_input = {"input": body.get("input") or {}}

    t0 = time.monotonic()
    state = await graph.ainvoke(graph_input)
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse(
            {"error": state["error"], "elapsed_s": round(elapsed, 3)},
            status_code=500,
        )
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})


# ---------------------------------------------------------------------------
# /xrpc/{nsid}
# ---------------------------------------------------------------------------

@app.post("/xrpc/{nsid:path}")
async def xrpc_post(nsid: str, request: Request):
    assistant_id = _NSID_TO_ASSISTANT.get(nsid)
    if assistant_id is None:
        raise HTTPException(status_code=501, detail=f"NSID not mapped: {nsid}")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    ct = request.headers.get("content-type", "")
    body = await request.json() if "application/json" in ct else {}

    graph_input = {"input": body or {}}

    t0 = time.monotonic()
    state = await graph.ainvoke(graph_input)
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse(
            {"error": state["error"], "elapsed_s": round(elapsed, 3)},
            status_code=500,
        )
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})


@app.get("/xrpc/{nsid:path}")
async def xrpc_get(nsid: str, request: Request):
    assistant_id = _NSID_TO_ASSISTANT.get(nsid)
    if assistant_id is None:
        raise HTTPException(status_code=501, detail=f"NSID not mapped: {nsid}")
    graph = GRAPHS.get(assistant_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"graph '{assistant_id}' not found")

    graph_input = {"input": dict(request.query_params)}

    t0 = time.monotonic()
    state = await graph.ainvoke(graph_input)
    elapsed = time.monotonic() - t0

    if state.get("error"):
        return JSONResponse(
            {"error": state["error"], "elapsed_s": round(elapsed, 3)},
            status_code=500,
        )
    return JSONResponse({"output": _safe_json(state.get("result")), "elapsed_s": round(elapsed, 3)})
