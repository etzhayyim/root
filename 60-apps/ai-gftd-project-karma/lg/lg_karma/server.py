"""LangGraph OSS FastAPI server — lg-karma.

Wraps 45 task handlers from 8 pymagatama.primitives.karma* modules.
All handlers use **kwargs so no camelCase conversion is needed.
No postgres checkpointer — stateless request-response graphs only.

Build:
  docker buildx build --platform linux/amd64 \\
    --build-context py=../../../20-actors/magatama/py \\
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

from pymagatama.primitives.karma import (
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
from pymagatama.primitives.karma_agent import task_karma_agent_evaluate
from pymagatama.primitives.karma_dao import (
    task_karma_dao_cast_vote,
    task_karma_dao_finalize,
    task_karma_dao_find_voters,
    task_karma_dao_open_arbitration,
    task_karma_dao_sweep_expired,
)
from pymagatama.primitives.karma_filecoin import (
    task_karma_filecoin_propose_batch,
    task_karma_filecoin_renew_expiring,
    task_karma_filecoin_status_get,
)
from pymagatama.primitives.karma_resident import (
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
from pymagatama.primitives.karma_wbt import (
    task_karma_wbt_balance_get,
    task_karma_wbt_forfeit_to_commons,
    task_karma_wbt_transfer,
)
from pymagatama.primitives.karma_witness import (
    task_karma_witness_invite_fan_out,
    task_karma_witness_respond_to_invitation,
    task_karma_witness_sweep_expired,
)
from pymagatama.primitives.karma_zk import (
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
# TASKS dict: NSID → handler (task type karma.X.Y → ai.gftd.apps.karma.XY)
# ---------------------------------------------------------------------------

TASKS: dict[str, Any] = {
    # karma.py
    "ai.gftd.apps.karma.inputValidate":        task_karma_input_validate,
    "ai.gftd.apps.karma.floorGate":            task_karma_floor_gate,
    "ai.gftd.apps.karma.edgePersist":          task_karma_edge_persist,
    "ai.gftd.apps.karma.organismDissolve":     task_karma_organism_dissolve,
    "ai.gftd.apps.karma.witnessPersist":       task_karma_witness_persist,
    "ai.gftd.apps.karma.ipfsFindUnpinned":     task_karma_ipfs_find_unpinned,
    "ai.gftd.apps.karma.ipfsPinBatch":         task_karma_ipfs_pin_batch,
    "ai.gftd.apps.karma.atrepoFindUnlifted":   task_karma_atrepo_find_unlifted,
    "ai.gftd.apps.karma.atrepoLiftBatch":      task_karma_atrepo_lift_batch,
    "ai.gftd.apps.karma.anchorComputeRoot":    task_karma_anchor_compute_root,
    "ai.gftd.apps.karma.anchorSubmitTx":       task_karma_anchor_submit_tx,
    "ai.gftd.apps.karma.anchorBacklinkEdges":  task_karma_anchor_backlink_edges,
    "ai.gftd.apps.karma.ipfsVerifyRandom":     task_karma_ipfs_verify_random,
    "ai.gftd.apps.karma.coverageSnapshot":     task_karma_coverage_snapshot,
    "ai.gftd.apps.karma.rebirthPrecheck":      task_karma_rebirth_precheck,
    "ai.gftd.apps.karma.rebirthForfeit":       task_karma_rebirth_forfeit,
    "ai.gftd.apps.karma.rebirthSeverFollows":  task_karma_rebirth_sever_follows,
    "ai.gftd.apps.karma.rebirthWipeAgents":    task_karma_rebirth_wipe_agents,
    "ai.gftd.apps.karma.rebirthEmerge":        task_karma_rebirth_emerge,
    # karma_agent.py
    "ai.gftd.apps.karma.agentEvaluate":        task_karma_agent_evaluate,
    # karma_dao.py
    "ai.gftd.apps.karma.daoFindVoters":        task_karma_dao_find_voters,
    "ai.gftd.apps.karma.daoOpenArbitration":   task_karma_dao_open_arbitration,
    "ai.gftd.apps.karma.daoCastVote":          task_karma_dao_cast_vote,
    "ai.gftd.apps.karma.daoFinalize":          task_karma_dao_finalize,
    "ai.gftd.apps.karma.daoSweepExpired":      task_karma_dao_sweep_expired,
    # karma_wbt.py
    "ai.gftd.apps.karma.wbtBalanceGet":        task_karma_wbt_balance_get,
    "ai.gftd.apps.karma.wbtTransfer":          task_karma_wbt_transfer,
    "ai.gftd.apps.karma.wbtForfeitToCommons":  task_karma_wbt_forfeit_to_commons,
    # karma_witness.py
    "ai.gftd.apps.karma.witnessInviteFanOut":          task_karma_witness_invite_fan_out,
    "ai.gftd.apps.karma.witnessRespondToInvitation":   task_karma_witness_respond_to_invitation,
    "ai.gftd.apps.karma.witnessSweepExpired":          task_karma_witness_sweep_expired,
    # karma_zk.py
    "ai.gftd.apps.karma.zkRebirthVerify":      task_karma_zk_rebirth_verify,
    "ai.gftd.apps.karma.zkRebirthProofLookup": task_karma_zk_rebirth_proof_lookup,
    # karma_filecoin.py
    "ai.gftd.apps.karma.filecoinProposeBatch":  task_karma_filecoin_propose_batch,
    "ai.gftd.apps.karma.filecoinRenewExpiring": task_karma_filecoin_renew_expiring,
    "ai.gftd.apps.karma.filecoinStatusGet":     task_karma_filecoin_status_get,
    # karma_resident.py
    "ai.gftd.apps.karma.organismSpawn":            task_karma_organism_spawn,
    "ai.gftd.apps.karma.organismTick":             task_karma_organism_tick,
    "ai.gftd.apps.karma.organismTickBatch":        task_karma_organism_tick_batch,
    "ai.gftd.apps.karma.organismCheckpoint":       task_karma_organism_checkpoint,
    "ai.gftd.apps.karma.organismResume":           task_karma_organism_resume,
    "ai.gftd.apps.karma.organismHarvest":          task_karma_organism_harvest,
    "ai.gftd.apps.karma.organismDissolveRuntime":  task_karma_organism_dissolve_runtime,
    "ai.gftd.apps.karma.cohortFission":            task_karma_cohort_fission,
    "ai.gftd.apps.karma.cohortFissionScan":        task_karma_cohort_fission_scan,
}


# ---------------------------------------------------------------------------
# GRAPHS dict + NSID → assistant map
# ---------------------------------------------------------------------------

GRAPHS: dict[str, Any] = {"health": _make_health_graph()}
GRAPHS.update({
    nsid.rsplit(".", 1)[-1]: _make_single_node_graph(handler, nsid.rsplit(".", 1)[-1])
    for nsid, handler in TASKS.items()
})

_NSID_TO_ASSISTANT: dict[str, str] = {"ai.gftd.apps.karma.health": "health"}
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
