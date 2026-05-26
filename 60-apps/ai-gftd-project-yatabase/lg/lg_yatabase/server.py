"""Minimal OSS FastAPI server for lg-yatabase.

Surface:
  POST /runs                  → invoke {graph} graph synchronously
  GET  /health  /ok           → liveness
  GET  /graphs                → list graph IDs
  POST /xrpc/{nsid}           → XRPC NSID → graph ID compat shim

Auth: optional `LG_YATABASE_API_KEY` env enforces `x-api-key` on /runs.
The cron path (POST /runs with x-cron=1) is allowed anonymously when
served behind a cloudflared tunnel (trust at tunnel layer).

Graphs + cron schedule (all JST):
  bmc_agent         09:03  daily
  metrics_daily     09:00  daily     (Phase 2)
  activation        08:30  daily     (Phase 2)
  conversion        10:15  daily     (Phase 2)
  retention         11:00  daily     (Phase 2)
  lead_discovery    00:00/06:00/12:00/18:00  every 6h  (Phase 2)
  email_sender      every 5 min  (Phase 2 — Resend outbox drain)
  marketing         00:15/06:15/12:15/18:15  every 6h  (existing)
  sales             :15 hourly  (existing)
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Header, HTTPException

from lg_yatabase.bmc.db import close_pool, get_pool
from lg_yatabase.bmc.handlers import router as BMC_ROUTER
from lg_yatabase.auth.handlers import router as AUTH_ROUTER
from lg_yatabase.leads.handlers import router as LEADS_ROUTER
from lg_yatabase.outbox.handlers import router as OUTBOX_ROUTER
from lg_yatabase.query.handlers import router as QUERY_ROUTER
from lg_yatabase.meter.handlers import router as METER_ROUTER
from lg_yatabase.graphs.health import GRAPH as HEALTH_GRAPH
from lg_yatabase.graphs.marketing import GRAPH as MARKETING_GRAPH
from lg_yatabase.graphs.sales import GRAPH as SALES_GRAPH
from lg_yatabase.graphs.bmc_iteration import GRAPH as BMC_GRAPH
from lg_yatabase.graphs.bmc_agent import GRAPH as BMC_AGENT_GRAPH
from lg_yatabase.graphs.lead_discovery import GRAPH as LEAD_DISCOVERY_GRAPH
from lg_yatabase.graphs.activation import GRAPH as ACTIVATION_GRAPH
from lg_yatabase.graphs.conversion import GRAPH as CONVERSION_GRAPH
from lg_yatabase.graphs.retention import GRAPH as RETENTION_GRAPH
from lg_yatabase.graphs.email_sender import GRAPH as EMAIL_SENDER_GRAPH

_log = logging.getLogger(__name__)

GRAPHS: dict[str, Any] = {
    "health": HEALTH_GRAPH,
    "marketing": MARKETING_GRAPH,
    "sales": SALES_GRAPH,
    "bmc_iteration": BMC_GRAPH,
    "bmc_agent": BMC_AGENT_GRAPH,
    # Phase 2 — Autonomous Growth Engine (ADR-2605212000)
    "lead_discovery": LEAD_DISCOVERY_GRAPH,
    "activation": ACTIVATION_GRAPH,
    "conversion": CONVERSION_GRAPH,
    "retention": RETENTION_GRAPH,
    "email_sender": EMAIL_SENDER_GRAPH,
}

NSID_TO_GRAPH = {
    "app.etzhayyim.apps.yata.lg.health": "health",
    "app.etzhayyim.apps.yata.lg.marketing.run": "marketing",
    "app.etzhayyim.apps.yata.lg.sales.run": "sales",
    "app.etzhayyim.apps.yata.lg.bmc.iterate": "bmc_iteration",
    "app.etzhayyim.apps.yata.lg.bmc.agent.run": "bmc_agent",
    "app.etzhayyim.apps.yata.lg.leadDiscovery.run": "lead_discovery",
    "app.etzhayyim.apps.yata.lg.activation.run": "activation",
    "app.etzhayyim.apps.yata.lg.conversion.run": "conversion",
    "app.etzhayyim.apps.yata.lg.retention.run": "retention",
    "app.etzhayyim.apps.yata.lg.emailSender.run": "email_sender",
}

_scheduler = AsyncIOScheduler(timezone="Asia/Tokyo")

app = FastAPI(
    title="lg-yatabase",
    description="LangGraph Server: yatabase marketing + sales + BMC graphs.",
    version="0.0.2",
)

# BMC XRPC surface (`app.etzhayyim.apps.yata.bmc*`). Must be mounted before the
# `/xrpc/{nsid}` catch-all so explicit routes win in registration order.
app.include_router(BMC_ROUTER)

# Auth XRPC surface (`app.etzhayyim.apps.yata.{signup,invite,revoke}`).
# Owns vertex_api_key writes — Worker no longer touches Hyperdrive per
# ADR-2605111200. Same x-internal-trust HMAC + identity headers as BMC.
app.include_router(AUTH_ROUTER)

# Leads CRM XRPC surface (`app.etzhayyim.apps.yata.lead{Ingest,List,Get,
# SetOutreachStatus,SetContactEmail,SetEnrichment,MarkDrafted,Ready,
# Sendable,NeedsEnrichment}`). Owns vertex_lead writes.
app.include_router(LEADS_ROUTER)

# Outbox-review XRPC surface (`app.etzhayyim.apps.yata.outbox{List,Approve,
# Reject}`). Marketing + sales graphs emit drafts at status='queued-no-
# recipient'; reviewers flip them to 'queued' via these endpoints (P21).
# Same x-internal-trust HMAC; admin gate enforced by the yatabase Worker.
app.include_router(OUTBOX_ROUTER)

# Deploy-first query XRPC surface (ADR-2605210000).
# app.etzhayyim.apps.yata.{deployQuery,executeDeployedQuery,listDeployedQueries,deleteDeployedQuery}
app.include_router(QUERY_ROUTER)

# Meter event XRPC surface (app.etzhayyim.apps.yata.meterEvent).
# CF Worker emitMeter() calls this pod-side so billing events reach RisingWave
# (Worker cannot use Hyperdrive per ADR-2605111200).
app.include_router(METER_ROUTER)


@app.on_event("startup")
async def _startup() -> None:
    """Pre-warm pool and start BMC agent daily cron."""
    try:
        await get_pool()
    except Exception as e:  # noqa: BLE001 — startup tolerates pool miss
        _log.warning("[lg-yatabase] bmc pool pre-warm failed: %s", e)

    # BMC strategy agent: daily 09:03 JST
    async def _run_bmc_agent() -> None:
        try:
            result = await BMC_AGENT_GRAPH.ainvoke({})
            _log.info("[bmc_agent] cron done: %s", result.get("summary", "")[:120])
        except Exception as exc:
            _log.exception("[bmc_agent] cron failed: %s", exc)

    # Phase 2 — Autonomous Growth Engine (ADR-2605212000)
    async def _run_lead_discovery() -> None:
        try:
            result = await LEAD_DISCOVERY_GRAPH.ainvoke({})
            _log.info("[lead_discovery] cron done: %s", result.get("summary", "")[:120])
        except Exception as exc:
            _log.exception("[lead_discovery] cron failed: %s", exc)

    async def _run_activation() -> None:
        try:
            result = await ACTIVATION_GRAPH.ainvoke({})
            _log.info("[activation] cron done: %s", result.get("summary", "")[:120])
        except Exception as exc:
            _log.exception("[activation] cron failed: %s", exc)

    async def _run_conversion() -> None:
        try:
            result = await CONVERSION_GRAPH.ainvoke({})
            _log.info("[conversion] cron done: %s", result.get("summary", "")[:120])
        except Exception as exc:
            _log.exception("[conversion] cron failed: %s", exc)

    async def _run_retention() -> None:
        try:
            result = await RETENTION_GRAPH.ainvoke({})
            _log.info("[retention] cron done: %s", result.get("summary", "")[:120])
        except Exception as exc:
            _log.exception("[retention] cron failed: %s", exc)

    async def _run_email_sender() -> None:
        try:
            result = await EMAIL_SENDER_GRAPH.ainvoke({})
            _log.info("[email_sender] cron done: %s", result.get("summary", "")[:120])
        except Exception as exc:
            _log.exception("[email_sender] cron failed: %s", exc)

    _scheduler.add_job(_run_bmc_agent, "cron", hour=9, minute=3)
    _scheduler.add_job(_run_activation, "cron", hour=8, minute=30)
    _scheduler.add_job(_run_conversion, "cron", hour=10, minute=15)
    _scheduler.add_job(_run_retention, "cron", hour=11, minute=0)
    # lead_discovery every 6h
    _scheduler.add_job(_run_lead_discovery, "cron", hour="0,6,12,18", minute=0)
    # email_sender every 5 minutes (Resend outbox drain)
    _scheduler.add_job(_run_email_sender, "interval", minutes=5)
    _scheduler.start()
    _log.info(
        "[lg-yatabase] scheduler started: bmc_agent 09:03, activation 08:30, "
        "conversion 10:15, retention 11:00, lead_discovery */6h JST, "
        "email_sender every 5min"
    )


@app.on_event("shutdown")
async def _shutdown() -> None:
    _scheduler.shutdown(wait=False)
    await close_pool()


def _enforce_auth(x_api_key: str | None, *, exempt: bool = False) -> None:
    if exempt:
        return
    expected = os.environ.get("LG_YATABASE_API_KEY")
    if not expected:
        return  # auth disabled in dev / tunnel-trust mode
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="x-api-key mismatch")


@app.get("/health")
@app.get("/ok")
def _health() -> dict[str, Any]:
    return {
        "ok": True,
        "app": "lg-yatabase",
        "ts": int(time.time() * 1000),
        "graphs": list(GRAPHS.keys()),
    }


@app.get("/graphs")
def _list_graphs() -> dict[str, Any]:
    return {
        "graphs": list(GRAPHS.keys()),
        "nsidMap": NSID_TO_GRAPH,
    }


@app.post("/runs")
async def _runs(
    body: dict[str, Any],
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_cron: str | None = Header(default=None, alias="x-cron"),
) -> dict[str, Any]:
    _enforce_auth(x_api_key, exempt=(x_cron == "1"))
    graph_id = body.get("graph") or body.get("assistant_id")
    if graph_id not in GRAPHS:
        raise HTTPException(status_code=404, detail=f"unknown graph: {graph_id}")
    inp = body.get("input", {})
    config = body.get("config", {})
    t0 = time.time()
    try:
        result = await GRAPHS[graph_id].ainvoke(inp, config=config)
    except Exception as e:
        _log.exception("[lg-yatabase][runs] graph=%s failed", graph_id)
        raise HTTPException(status_code=500, detail=str(e)[:300])
    return {
        "ok": True,
        "graph": graph_id,
        "duration_ms": int((time.time() - t0) * 1000),
        "result": result,
    }


@app.post("/xrpc/{nsid}")
async def _xrpc(nsid: str, body: dict[str, Any]) -> dict[str, Any]:
    graph_id = NSID_TO_GRAPH.get(nsid)
    if not graph_id:
        raise HTTPException(status_code=404, detail=f"NSID {nsid} not mapped")
    return await _runs({"graph": graph_id, "input": body}, x_api_key=None, x_cron="1")
