"""server — FastAPI HTTP entry exposing malak.surveillance LangGraph chains.

LangServe-style invoke pattern (POST /invoke with state dict, returns final
state dict). Compatible with `langchain_core.runnables.Runnable` protocol.

Routes:

  GET  /health                                  → {"status":"ok"}
  POST /invoke/exportSurveillanceEvidence       → run_export_evidence(**body)
  POST /invoke/agencyOutreachFullFlow            → run_outreach_flow(**body)
  POST /invoke/draftAgencyBriefing               → run_briefing(**body)
  GET  /chains                                   → list available chains + Pregel topology

Per ADR-2605080600 (LangGraph Server + Granian L3 Runtime), the production
deployment runs this app under Granian (`granian --interface asgi
pymagatama.malak.langgraph.server:app`).

Per ADR-2605082000 (LangGraph Graph-Definition-as-Data), the graph topology
is exposed as JSON via /chains/{name}/topology for inspection.

Per ADR-2605082200 (LangServer Handler Thin Dispatcher Contract), the LangServer
handler in `primitives/malak.py` is a thin dispatch only — orchestration
lives in LangGraph (this module).
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
except ImportError as exc:
    raise RuntimeError(
        "FastAPI required: install with `pip install fastapi` (already in pyproject)"
    ) from exc

from .agency_outreach_full_flow import (
    build_agency_outreach_graph,
    run_outreach_flow,
)
from .address_label_pursuit import (
    build_address_label_pursuit_graph,
    run_address_label_pursuit,
)
from .bitnest_exit_pursuit import (
    build_bitnest_exit_pursuit_graph,
    run_bitnest_exit_pursuit,
)
from .briefing import build_briefing_graph, run_briefing
from .chain_freeze_request_pursuit import (
    ALL_PACKET_KINDS,
    build_chain_freeze_request_graph,
    run_chain_freeze_request,
)
from .export_surveillance_evidence import (
    ALL_DOC_TYPES,
    build_export_evidence_graph,
    run_export_evidence,
)
from .wallet_deep_inspect_pursuit import (
    build_wallet_deep_inspect_graph,
    run_wallet_deep_inspect,
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="malak.surveillance LangGraph server",
    description=(
        "LangServe-style HTTP entry for malak.surveillance capability cluster. "
        "Replaces ai.gftd.apps.bpmn.processDef BPMN flow definitions with "
        "LangGraph + Pregel super-steps + FastAPI. ADR-2605080600 + "
        "ADR-2605082000 + ADR-2605082200."
    ),
    version="0.1.0",
)


CHAINS: Dict[str, Dict[str, Any]] = {
    "exportSurveillanceEvidence": {
        "module":  "pymagatama.malak.langgraph.export_surveillance_evidence",
        "factory": build_export_evidence_graph,
        "runner":  run_export_evidence,
        "nsid":    "ai.gftd.apps.malak.exportSurveillanceEvidence",
        "pregel": {
            "super_steps": 4,
            "fan_out_at":  "load_query → render_doc (Send × 4 doc_types)",
            "barrier_at":  "render_doc → emit_pegel_per_doc",
            "doc_types":   list(ALL_DOC_TYPES),
        },
        "gates": [
            {"name": "two_stage_approval", "kind": "edge+LangServer+langgraph",
             "field": "supervisor_did + section_chief_did"},
        ],
    },
    "agencyOutreachFullFlow": {
        "module":  "pymagatama.malak.langgraph.agency_outreach_full_flow",
        "factory": build_agency_outreach_graph,
        "runner":  run_outreach_flow,
        "nsid":    "ai.gftd.apps.malak.agencyOutreachFullFlow",
        "pregel": {
            "super_steps": 6,
            "fan_out_at":  None,  # sequential with 5 abort branches
            "barrier_at":  None,
        },
        "gates": [
            {"name": "opt_in_source", "kind": "edge+LangServer+langgraph",
             "field": "opt_in_source ∈ {exhibition_list,lecture_host,referral,inbound}"},
            {"name": "jurisdiction_cooperation_status", "kind": "langgraph",
             "field": "cooperation_status ≠ prohibited"},
            {"name": "safety_gates", "kind": "langgraph",
             "field": "SAFETY_GATES 11 種"},
            {"name": "sales_manager_approval", "kind": "langgraph",
             "field": "sales_manager_did present"},
            {"name": "business_hour", "kind": "edge+LangServer+langgraph",
             "field": "09:00-17:00 JST 平日 OR scheduleHint=nextBusinessHour"},
        ],
    },
    "draftAgencyBriefing": {
        "module":  "pymagatama.malak.langgraph.briefing",
        "factory": build_briefing_graph,
        "runner":  run_briefing,
        "nsid":    "ai.gftd.apps.malak.draftAgencyBriefing",
        "pregel": {
            "super_steps": 8,
            "fan_out_at":  None,
            "barrier_at":  None,
            "graph_native": True,
        },
        "gates": [],
    },
    "walletDeepInspect": {
        "module":  "pymagatama.malak.langgraph.wallet_deep_inspect_pursuit",
        "factory": build_wallet_deep_inspect_graph,
        "runner":  run_wallet_deep_inspect,
        "nsid":    "ai.gftd.apps.malak.walletDeepInspect",
        "pregel": {
            "super_steps": 7,
            "fan_out_at":  "fetch_address_meta → fetch_page_one (Send × max_pages); "
                            "collect_and_dedupe → label_counterparty_one (Send × top_k)",
            "barrier_at":  "after_fetch_pages_barrier; after_label_barrier",
            "anchors":     "case_id-aware (CASE_ANCHORS table)",
        },
        "gates": [
            {"name":  "input_validation",
             "kind":  "langgraph",
             "field": "target_address checksum-valid"},
            {"name":  "phase0_live_write_guard",
             "kind":  "langgraph",
             "field": "live_write defaults False"},
        ],
    },
    "chainFreezeRequest": {
        "module":  "pymagatama.malak.langgraph.chain_freeze_request_pursuit",
        "factory": build_chain_freeze_request_graph,
        "runner":  run_chain_freeze_request,
        "nsid":    "ai.gftd.apps.malak.chainFreezeRequest",
        "pregel": {
            "super_steps": 6,
            "fan_out_at":  "load_case_evidence → render_packet_one (Send × N packet kinds)",
            "barrier_at":  "after_render_barrier",
            "packet_kinds": list(ALL_PACKET_KINDS),
        },
        "gates": [
            {"name":  "case_known",
             "kind":  "langgraph",
             "field": "case_id must be in CASE_EVIDENCE table"},
            {"name":  "packet_kind_validation",
             "kind":  "langgraph",
             "field": "all packet kinds in PACKET_RENDERERS map"},
        ],
    },
    "addressLabelBatch": {
        "module":  "pymagatama.malak.langgraph.address_label_pursuit",
        "factory": build_address_label_pursuit_graph,
        "runner":  run_address_label_pursuit,
        "nsid":    "ai.gftd.apps.malak.addressLabelBatch",
        "pregel": {
            "super_steps": 5,
            "fan_out_at":  "gate_input → label_one (Send × N addresses)",
            "barrier_at":  "after_label_barrier",
        },
        "gates": [
            {"name":  "address_validation",
             "kind":  "langgraph",
             "field": "all addresses match ^0x[a-fA-F0-9]{40}$"},
            {"name":  "phase0_live_write_guard",
             "kind":  "langgraph",
             "field": "live_write defaults False"},
        ],
    },
    "bitnestExitPursuit": {
        "module":  "pymagatama.malak.langgraph.bitnest_exit_pursuit",
        "factory": build_bitnest_exit_pursuit_graph,
        "runner":  run_bitnest_exit_pursuit,
        "nsid":    "ai.gftd.apps.malak.bitnestExitPursuit",
        "pregel": {
            "super_steps": 7,
            "fan_out_at":  "gate_input → fetch_one (Send × N sources); "
                            "fetch_one → llm_extract_one (Send × N); "
                            "correlate → probe_wallet_one (Send × ≤12 targets)",
            "barrier_at":  "fetch_one → fan_out_extract; "
                            "llm_extract_one → correlate; "
                            "probe_wallet_one → link_back_to_takahashi",
            "anchors":     "case:takahashi-hiroyuki-20260512",
        },
        "gates": [
            {"name":  "input_validation",
             "kind":  "edge+LangServer+langgraph",
             "field": "case_id + sources non-empty"},
            {"name":  "phase0_live_write_guard",
             "kind":  "langgraph",
             "field": "live_write defaults False; Phase 1 G1+G2 GREEN required"},
        ],
    },
}


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "malak.surveillance.langgraph-server",
        "version": app.version,
        "chains": list(CHAINS.keys()),
    }


@app.get("/chains")
async def list_chains() -> Dict[str, Any]:
    """List all available chains and their NSID + Pregel topology summary."""
    return {
        "chains": [
            {
                "name":      name,
                "nsid":      cfg["nsid"],
                "module":    cfg["module"],
                "pregel":    cfg["pregel"],
                "gates":     cfg["gates"],
            }
            for name, cfg in CHAINS.items()
        ],
    }


@app.get("/chains/{chain_name}/topology")
async def chain_topology(chain_name: str) -> Dict[str, Any]:
    """Per ADR-2605082000 (Graph-Definition-as-Data): expose StateGraph node
    list + edges for inspection. Phase 0 returns the static graph metadata;
    Phase 1 introspects the compiled CompiledGraph for live edges."""
    if chain_name not in CHAINS:
        raise HTTPException(status_code=404, detail=f"unknown chain {chain_name!r}")
    cfg = CHAINS[chain_name]
    graph = cfg["factory"]()
    # CompiledGraph exposes get_graph() with nodes + edges
    try:
        viz = graph.get_graph()
        nodes = [{"id": n.id, "name": n.id} for n in viz.nodes.values()] if hasattr(viz, "nodes") else []
        edges = []
        if hasattr(viz, "edges"):
            for e in viz.edges:
                src = getattr(e, "source", None)
                dst = getattr(e, "target", None)
                cond = getattr(e, "data", None)
                edges.append({"source": src, "target": dst, "condition": cond})
    except Exception as e:  # noqa: BLE001
        logger.exception("topology introspection failed")
        nodes, edges = [], []
    return {
        "chain":  chain_name,
        "nsid":   cfg["nsid"],
        "pregel": cfg["pregel"],
        "nodes":  nodes,
        "edges":  edges,
    }


_NSID_TO_CHAIN: Dict[str, str] = {cfg["nsid"]: name for name, cfg in CHAINS.items()}


async def _run_chain(chain_name: str, request: Request) -> JSONResponse:
    if chain_name not in CHAINS:
        raise HTTPException(status_code=404, detail=f"unknown chain {chain_name!r}")
    cfg = CHAINS[chain_name]
    try:
        payload = await request.json()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"invalid JSON: {e}") from e
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="body must be a JSON object")

    runner = cfg["runner"]
    try:
        result = await runner(**payload)
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"bad payload: {e}") from e
    except Exception as e:  # noqa: BLE001
        logger.exception("chain %s failed", chain_name)
        raise HTTPException(status_code=500, detail=str(e)) from e

    trimmed = {k: v for k, v in result.items() if k not in {
        "rendered_docs", "rendered_md", "graph_rows", "query_record",
        "draft_body", "raw_url_citations",
    }}
    return JSONResponse(content=trimmed)


@app.post("/invoke/{chain_name}")
async def invoke_chain(chain_name: str, request: Request) -> JSONResponse:
    """LangServe-compatible invoke. Body is initial state dict, response is
    trimmed final state (PII channels stripped). Phase 0 = no auth; Phase 1
    gates by `X-Internal-Trust` + DID-bound ES256."""
    return await _run_chain(chain_name, request)


@app.post("/xrpc/{nsid:path}")
async def xrpc_invoke(nsid: str, request: Request) -> JSONResponse:
    """bpmn-dispatcher compat: `_proxy_to_lg_pod` constructs `{url}/xrpc/{nsid}`.
    Map known NSIDs back to the underlying chain runner."""
    chain_name = _NSID_TO_CHAIN.get(nsid)
    if chain_name is None:
        raise HTTPException(status_code=404, detail=f"unknown nsid {nsid!r}")
    return await _run_chain(chain_name, request)


if __name__ == "__main__":
    # Local dev convenience. Production uses Granian: see ADR-2605080600.
    import uvicorn  # type: ignore[import-not-found]
    port = int(os.environ.get("MALAK_LANGSERVER_PORT", "8765"))
    host = os.environ.get("MALAK_LANGSERVER_HOST", "127.0.0.1")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host=host, port=port)
