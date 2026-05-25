"""FastAPI router exposing BMC XRPC handlers.

The yatabase CF Worker forwards `/xrpc/app.etzhayyim.apps.yata.bmc{Verb}` over
HTTPS with an HMAC-SHA256 of the body in `x-internal-trust` and the
resolved identity in `x-gftd-actor-did` / `x-gftd-org-did`. The pod is
the only writer; the Worker holds no Hyperdrive binding.

NSID flat naming (`app.etzhayyim.apps.yata.bmcGetState` etc.) matches the
existing `app.etzhayyim.apps.yata.*` surface — see
`00-contracts/lexicons/ai/gftd/apps/yata/bmc*.json`.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from lg_yatabase.bmc import repository
from lg_yatabase.bmc.models import (
    AddHypothesisInput,
    AppendStateInput,
    IterateInput,
    SetHypothesisStatusInput,
)

_log = logging.getLogger(__name__)

router = APIRouter()


async def _verify_trust(request: Request, x_internal_trust: str | None) -> bytes:
    body = await request.body()
    secret = os.environ.get("DISPATCHER_INTERNAL_SECRET")
    if not secret:
        # In tunnel-trust dev mode (no shared secret) accept all.
        return body
    if not x_internal_trust:
        raise HTTPException(status_code=401, detail="missing x-internal-trust")
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, x_internal_trust):
        raise HTTPException(status_code=401, detail="x-internal-trust mismatch")
    return body


def _resolve_identity(
    actor_did: str | None,
    org_did: str | None,
) -> tuple[str, str]:
    return (actor_did or "anon"), (org_did or "anon")


def _float_str(x: float | None) -> str | None:
    if x is None:
        return None
    return repr(x)


# ── Read endpoints ─────────────────────────────────────────────────────


@router.get("/xrpc/app.etzhayyim.apps.yata.bmcGetState")
async def bmc_get_state(
    request: Request,
    org_did_param: str | None = None,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    _, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    org = org_did_param or org
    head = await repository.get_head(org)
    if head is None:
        return JSONResponse({"version": 0, "canvasJson": "{}", "source": "seed",
                             "createdBy": "system", "createdAt": "1970-01-01T00:00:00Z"})
    return JSONResponse({
        "vertexId": head["vertex_id"],
        "version": int(head["version"]),
        "canvasJson": head["canvas_json"],
        "rationale": head.get("rationale") or "",
        "source": head["source"],
        "createdBy": head["created_by"],
        "createdAt": head["created_at"],
    })


@router.get("/xrpc/app.etzhayyim.apps.yata.bmcListHypotheses")
async def bmc_list_hypotheses(
    request: Request,
    status: str | None = None,
    block: str | None = None,
    offset: int = 0,
    limit: int = 50,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    _, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    rows, total = await repository.list_hypotheses(
        org_did=org, status=status, block=block, offset=offset, limit=limit,
    )
    out = [{
        "vertexId": r["vertex_id"],
        "slug": r["slug"],
        "block": r["block"],
        "statement": r["statement"],
        "metric": r["metric"],
        "metricQuery": r["metric_query"],
        "threshold": repr(float(r["threshold"])),
        "baseline": repr(float(r["baseline"])),
        "deadlineIso": r["deadline_iso"],
        "minSample": int(r["min_sample"]),
        "authoredBy": r["authored_by"],
        "autoApplyPivot": bool(r.get("auto_apply_pivot")),
        "status": r["status"],
        "statusAt": r.get("status_at") or "",
        "createdAt": r["created_at"],
    } for r in rows]
    return JSONResponse({"hypotheses": out, "offset": offset, "limit": limit, "total": total})


@router.get("/xrpc/app.etzhayyim.apps.yata.bmcListIterations")
async def bmc_list_iterations(
    request: Request,
    hypothesisSlug: str | None = None,
    offset: int = 0,
    limit: int = 50,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    _, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    rows, total = await repository.list_iterations(
        org_did=org, hypothesis_slug=hypothesisSlug, offset=offset, limit=limit,
    )
    out = [{
        "vertexId": r["vertex_id"],
        "hypothesisSlug": r["hypothesis_slug"],
        "iterationNo": int(r["iteration_no"]),
        "bmcVersionIn": int(r["bmc_version_in"]),
        "bmcVersionOut": int(r["bmc_version_out"]),
        "measuredValue": repr(float(r["measured_value"])),
        "measuredAt": r["measured_at"],
        "measurementSource": r["measurement_source"],
        "passed": bool(int(r["passed"])),
        "notes": r.get("notes") or "",
        "createdAt": r["created_at"],
    } for r in rows]
    return JSONResponse({"iterations": out, "offset": offset, "limit": limit, "total": total})


@router.get("/xrpc/app.etzhayyim.apps.yata.bmcListDecisions")
async def bmc_list_decisions(
    request: Request,
    hypothesisSlug: str | None = None,
    action: str | None = None,
    offset: int = 0,
    limit: int = 50,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    _, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    rows, total = await repository.list_decisions(
        org_did=org, hypothesis_slug=hypothesisSlug, action=action,
        offset=offset, limit=limit,
    )
    out = [{
        "vertexId": r["vertex_id"],
        "iterationVertexId": r["iteration_vertex_id"],
        "hypothesisSlug": r["hypothesis_slug"],
        "action": r["action"],
        "rationale": r["rationale"],
        "authoredBy": r["authored_by"],
        "appliedAt": r["applied_at"],
        "createdAt": r["created_at"],
    } for r in rows]
    return JSONResponse({"decisions": out, "offset": offset, "limit": limit, "total": total})


@router.get("/xrpc/app.etzhayyim.apps.yata.bmcBlockHealth")
async def bmc_block_health(
    request: Request,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    await _verify_trust(request, x_internal_trust)
    _, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    rows = await repository.block_health(org)
    out = [{
        "block": r["block"],
        "hypTotal": int(r["hyp_total"] or 0),
        "hypActive": int(r["hyp_active"] or 0),
        "hypCompleted": int(r["hyp_completed"] or 0),
        "hypKilled": int(r["hyp_killed"] or 0),
        "avgMeasured": _float_str(r["avg_measured"]) or "",
        "lastIterAt": r.get("last_iter_at") or "",
    } for r in rows]
    return JSONResponse({"blocks": out})


# ── Write endpoints ────────────────────────────────────────────────────


@router.post("/xrpc/app.etzhayyim.apps.yata.bmcAppendState")
async def bmc_append_state(
    request: Request,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    raw = await _verify_trust(request, x_internal_trust)
    body = AppendStateInput.model_validate_json(raw)
    actor, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    try:
        res = await repository.append_state(
            canvas_json=body.canvas_json, rationale=body.rationale,
            source=body.source, actor_did=actor, org_did=org,
            created_by=body.created_by,
        )
        return JSONResponse({"ok": True, "vertexId": res["vertex_id"], "version": res["version"]})
    except Exception as e:
        _log.exception("[bmc.appendState] failed")
        return JSONResponse({"ok": False, "vertexId": "", "version": 0, "error": str(e)[:240]}, status_code=500)


@router.post("/xrpc/app.etzhayyim.apps.yata.bmcAddHypothesis")
async def bmc_add_hypothesis(
    request: Request,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    raw = await _verify_trust(request, x_internal_trust)
    body = AddHypothesisInput.model_validate_json(raw)
    actor, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    try:
        res = await repository.add_hypothesis(
            slug=body.slug, block=body.block, statement=body.statement,
            metric=body.metric, metric_query=body.metric_query,
            threshold=float(body.threshold), baseline=float(body.baseline),
            deadline_iso=body.deadline_iso, min_sample=body.min_sample,
            authored_by=body.authored_by or actor,
            auto_apply_pivot=body.auto_apply_pivot,
            actor_did=actor, org_did=org,
        )
        return JSONResponse({"ok": True, "vertexId": res["vertex_id"]})
    except Exception as e:
        _log.exception("[bmc.addHypothesis] failed")
        return JSONResponse({"ok": False, "vertexId": "", "error": str(e)[:240]}, status_code=500)


@router.post("/xrpc/app.etzhayyim.apps.yata.bmcSetHypothesisStatus")
async def bmc_set_hypothesis_status(
    request: Request,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    raw = await _verify_trust(request, x_internal_trust)
    body = SetHypothesisStatusInput.model_validate_json(raw)
    actor, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    try:
        res = await repository.append_hypothesis_event(
            slug=body.slug, next_status=body.next_status,
            authored_by=body.authored_by or actor,
            actor_did=actor, org_did=org,
            reason=body.reason,
            iteration_vertex_id=body.iteration_vertex_id,
        )
        return JSONResponse({"ok": True, "vertexId": res["vertex_id"]})
    except Exception as e:
        _log.exception("[bmc.setHypothesisStatus] failed")
        return JSONResponse({"ok": False, "vertexId": "", "error": str(e)[:240]}, status_code=500)


@router.post("/xrpc/app.etzhayyim.apps.yata.bmcIterate")
async def bmc_iterate(
    request: Request,
    x_gftd_actor_did: str | None = Header(default=None, alias="x-gftd-actor-did"),
    x_gftd_org_did: str | None = Header(default=None, alias="x-gftd-org-did"),
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    raw = await _verify_trust(request, x_internal_trust)
    body = IterateInput.model_validate_json(raw) if raw else IterateInput()
    actor, org = _resolve_identity(x_gftd_actor_did, x_gftd_org_did)
    # Lazy import: graph wiring keeps repository -> handlers acyclic.
    from lg_yatabase.graphs.bmc_iteration import GRAPH as BMC_GRAPH

    inp: dict[str, Any] = {
        "org_did": org,
        "actor_did": actor,
        "trigger": "on_demand",
        "dry_run": body.dry_run,
    }
    if body.hypothesis_slug:
        inp["forced_hypothesis_slug"] = body.hypothesis_slug
    try:
        result = await BMC_GRAPH.ainvoke(inp)
    except Exception as e:
        _log.exception("[bmc.iterate] graph failed")
        return JSONResponse({"ok": False, "firedAt": "", "error": str(e)[:240]}, status_code=500)
    return JSONResponse({
        "ok": True,
        "threadId": result.get("iteration_id", ""),
        "firedAt": result.get("started_at_iso", ""),
        "picked": result.get("picked_out"),
        "measurement": result.get("measurement_out"),
        "evaluation": result.get("evaluation_out"),
        "decision": result.get("decision_out"),
        "iterationVertexId": result.get("iteration_vertex_id", ""),
        "decisionVertexId": result.get("decision_vertex_id", ""),
        "notes": result.get("notes", ""),
    })
