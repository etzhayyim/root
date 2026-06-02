"""FastAPI server for lg-lawfirm-intake.

Surface:
  GET  /health /ok
  POST /runs
  POST /xrpc/com.etzhayyim.apps.lawfirm.triageIntake   ← main XRPC entry

Auth: DISPATCHER_INTERNAL_SECRET in x-internal-trust header.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from lg_lawfirm_intake.graph import build_graph  # type: ignore[import-untyped]

_log = logging.getLogger(__name__)

_GRAPH = build_graph()
_NSID_TRIAGE = "/xrpc/com.etzhayyim.apps.lawfirm.triageIntake"


def _enforce_auth(
    x_internal_trust: str | None,
    *,
    exempt: bool = False,
) -> None:
    if exempt:
        return
    expected = os.environ.get("DISPATCHER_INTERNAL_SECRET")
    if not expected:
        return
    if not x_internal_trust or x_internal_trust != expected:
        raise HTTPException(status_code=401, detail="x-internal-trust mismatch")


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    _log.info("lg-lawfirm-intake startup")
    yield
    _log.info("lg-lawfirm-intake shutdown")


app = FastAPI(title="lg-lawfirm-intake", lifespan=_lifespan)


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {
        "ok": True,
        "app": "lg-lawfirm-intake",
        "ts": int(time.time() * 1000),
        "graph": "lawfirm_intake",
    }


@app.post("/runs")
async def _runs(
    body: dict[str, Any],
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
    x_cron: str | None = Header(default=None, alias="x-cron"),
) -> dict[str, Any]:
    _enforce_auth(x_internal_trust, exempt=(x_cron == "1"))
    inp = body.get("input") or {}
    t0 = time.time()
    try:
        result = await _GRAPH.ainvoke(inp)
    except Exception as exc:
        _log.exception("[runs] graph failed")
        raise HTTPException(status_code=500, detail=str(exc)[:300])
    return {
        "ok": True,
        "graph": "lawfirm_intake",
        "duration_ms": int((time.time() - t0) * 1000),
        "result": result,
    }


@app.post(_NSID_TRIAGE)
async def _xrpc_triage_intake(
    request: Request,
    x_internal_trust: str | None = Header(default=None, alias="x-internal-trust"),
) -> JSONResponse:
    """Triage + match for an intake case.

    Body: {
      case_id, case_did, lang, domain, state, urgency,
      jurisdiction, owner_did, actor_did, summary_plain
    }
    """
    _enforce_auth(x_internal_trust)
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON")

    case_did = str(body.get("case_did") or "").strip()
    summary_plain = str(body.get("summary_plain") or "").strip()
    if not summary_plain:
        raise HTTPException(status_code=400, detail="summary_plain required")

    inp: dict[str, Any] = {
        "case_id": str(body.get("case_id") or ""),
        "case_did": case_did,
        "lang": str(body.get("lang") or "en"),
        "domain": str(body.get("domain") or ""),
        "state": str(body.get("state") or ""),
        "urgency": str(body.get("urgency") or ""),
        "jurisdiction": str(body.get("jurisdiction") or ""),
        "owner_did": str(body.get("owner_did") or ""),
        "actor_did": str(body.get("actor_did") or ""),
        "summary_plain": summary_plain,
    }

    t0 = time.time()
    try:
        result = await _GRAPH.ainvoke(inp)
    except Exception as exc:
        _log.exception("[triageIntake] graph failed")
        raise HTTPException(status_code=500, detail=str(exc)[:300])

    return JSONResponse({
        "ok": True,
        "duration_ms": int((time.time() - t0) * 1000),
        "case_id": result.get("case_id"),
        "case_did": result.get("case_did"),
        "domain": result.get("domain"),
        "urgency": result.get("urgency"),
        "jurisdiction": result.get("jurisdiction"),
        "summary_cipher": result.get("summary_cipher"),
        "triage_result": result.get("triage_result"),
        "lawyers_found": len(result.get("lawyers") or []),
        "grants": result.get("grants") or [],
    })
