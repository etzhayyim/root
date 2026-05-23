"""yatabase QA BMC graph — Business Model Canvas health checks.

Probes the BMC canvas and hypothesis pipeline without writing to the DB.
All three probe nodes are read-only; the full bmc_iteration dry-run is
the only node that invokes the write path (but skips persistence).

ReAct loop:
  probe_canvas → probe_hypotheses → run_bmc_dry → analyze_bmc → build_bmc_report

NSID: ai.gftd.apps.yata.lg.qaBmc.run
Graph ID: qa_bmc_react
Triggered: manually or as post-deploy gate

Input (QABmcState):
  org_did  — target org DID (default: "anon")
  host     — optional host label
"""

from __future__ import annotations

import logging
import time
import traceback
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc import repository
from lg_yatabase.graphs._llm import call_llm_json

_log = logging.getLogger(__name__)

_BMC_REQUIRED_BLOCKS = {
    "key_partners",
    "key_activities",
    "key_resources",
    "value_propositions",
    "customer_relationships",
    "channels",
    "customer_segments",
    "cost_structure",
    "revenue_streams",
}


class QABmcState(TypedDict, total=False):
    run_id: str
    org_did: str
    host: str

    # probe_canvas output
    canvas_status: str
    canvas_version: int
    canvas_blocks_present: list[str]
    canvas_blocks_missing: list[str]
    canvas_error: str

    # probe_hypotheses output
    hyp_status: str
    hyp_active_count: int
    hyp_total_count: int
    hyp_block_health: list[dict[str, Any]]
    hyp_error: str

    # run_bmc_dry output
    dry_run_status: str
    dry_run_idle: bool
    dry_run_notes: str
    dry_run_error: str
    dry_run_picked: dict[str, Any] | None
    dry_run_measurement: dict[str, Any] | None
    dry_run_decision: dict[str, Any] | None

    # analyze_bmc output
    analysis: str

    # final
    checks: list[dict[str, Any]]
    passed: int
    failed: int
    skipped: int
    report: dict[str, Any]


# ── Nodes ─────────────────────────────────────────────────────────────────────


async def probe_canvas(state: QABmcState) -> QABmcState:
    run_id = state.get("run_id") or str(uuid.uuid4())[:8]
    org = state.get("org_did") or "anon"
    try:
        head = await repository.get_head(org)
    except Exception as exc:
        _log.warning("[qa_bmc][%s] probe_canvas error: %s", run_id, exc)
        return {
            "run_id": run_id,
            "canvas_status": "ERROR",
            "canvas_error": traceback.format_exc(limit=4),
        }

    if head is None:
        return {
            "run_id": run_id,
            "canvas_status": "EMPTY",
            "canvas_version": 0,
            "canvas_blocks_present": [],
            "canvas_blocks_missing": sorted(_BMC_REQUIRED_BLOCKS),
            "canvas_error": "no canvas state found for org",
        }

    import json
    try:
        canvas = json.loads(head["canvas_json"])
    except Exception:
        canvas = {}

    present = [b for b in _BMC_REQUIRED_BLOCKS if b in canvas and canvas[b]]
    missing = sorted(_BMC_REQUIRED_BLOCKS - set(present))
    status = "PASS" if not missing else "WARN"
    _log.info("[qa_bmc][%s] canvas v%s present=%d missing=%d", run_id, head["version"], len(present), len(missing))
    return {
        "run_id": run_id,
        "canvas_status": status,
        "canvas_version": int(head["version"]),
        "canvas_blocks_present": sorted(present),
        "canvas_blocks_missing": missing,
    }


async def probe_hypotheses(state: QABmcState) -> QABmcState:
    org = state.get("org_did") or "anon"
    try:
        rows, total = await repository.list_hypotheses(org_did=org, status=None, block=None, offset=0, limit=100)
    except Exception as exc:
        _log.warning("[qa_bmc][%s] probe_hypotheses list error: %s", state.get("run_id"), exc)
        return {
            "hyp_status": "ERROR",
            "hyp_error": traceback.format_exc(limit=4),
        }

    active = [r for r in rows if r.get("status") == "active"]

    try:
        block_health = await repository.block_health(org)
    except Exception:
        block_health = []

    status = "PASS" if active else "WARN"
    _log.info("[qa_bmc][%s] hypotheses total=%d active=%d", state.get("run_id"), total, len(active))
    return {
        "hyp_status": status,
        "hyp_active_count": len(active),
        "hyp_total_count": total,
        "hyp_block_health": [
            {k: v for k, v in row.items() if k in ("block", "hyp_total", "hyp_active", "hyp_completed", "avg_measured")}
            for row in block_health
        ],
    }


async def run_bmc_dry(state: QABmcState) -> QABmcState:
    from lg_yatabase.graphs.bmc_iteration import GRAPH as bmc_graph

    org = state.get("org_did") or "anon"
    try:
        result = await bmc_graph.ainvoke({
            "org_did": org,
            "actor_did": "agent:qa-bmc",
            "trigger": "qa_smoke",
            "dry_run": True,
        })
    except Exception as exc:
        _log.warning("[qa_bmc][%s] dry run error: %s", state.get("run_id"), exc)
        return {
            "dry_run_status": "ERROR",
            "dry_run_error": traceback.format_exc(limit=6),
        }

    idle = bool(result.get("idle"))
    notes = str(result.get("notes") or "")
    _log.info("[qa_bmc][%s] dry run complete idle=%s notes=%s", state.get("run_id"), idle, notes)
    return {
        "dry_run_status": "PASS",
        "dry_run_idle": idle,
        "dry_run_notes": notes,
        "dry_run_picked": result.get("picked_out"),
        "dry_run_measurement": result.get("measurement_out"),
        "dry_run_decision": result.get("decision_out"),
    }


def _make_check(name: str, status: str, detail: str) -> dict[str, Any]:
    return {"name": name, "status": status, "detail": detail}


def _collect_checks(state: QABmcState) -> list[dict[str, Any]]:
    checks = []

    cs = state.get("canvas_status", "SKIP")
    checks.append(_make_check(
        "canvas_load",
        "FAIL" if cs == "ERROR" else ("PASS" if cs == "PASS" else ("WARN" if cs == "WARN" else "SKIP")),
        (state.get("canvas_error") or
         f"v{state.get('canvas_version',0)} — {len(state.get('canvas_blocks_present',[]))} blocks present"
         + (f"; missing: {state.get('canvas_blocks_missing')}" if state.get("canvas_blocks_missing") else "")),
    ))

    hs = state.get("hyp_status", "SKIP")
    checks.append(_make_check(
        "hypotheses_active",
        "FAIL" if hs == "ERROR" else "PASS" if hs == "PASS" else "WARN",
        (state.get("hyp_error") or
         f"active={state.get('hyp_active_count',0)} total={state.get('hyp_total_count',0)}"),
    ))

    ds = state.get("dry_run_status", "SKIP")
    if ds == "SKIP":
        checks.append(_make_check("bmc_iteration_dry_run", "SKIP", "not executed"))
    elif ds == "ERROR":
        checks.append(_make_check("bmc_iteration_dry_run", "FAIL", state.get("dry_run_error", "")))
    else:
        note = state.get("dry_run_notes") or ""
        idle = state.get("dry_run_idle", False)
        checks.append(_make_check(
            "bmc_iteration_dry_run",
            "PASS",
            ("idle — no active hypotheses" if idle else f"pipeline OK: {note}"),
        ))

    return checks


async def analyze_bmc(state: QABmcState) -> QABmcState:
    checks = _collect_checks(state)
    failures = [c for c in checks if c["status"] in ("FAIL",)]

    if not failures:
        return {"checks": checks, "analysis": "All BMC checks passed or warned — no hard failures."}

    failure_lines = "\n".join(f"FAIL {c['name']}: {c['detail']}" for c in failures)
    prompt = (
        f"The following yatabase BMC health checks failed:\n\n{failure_lines}\n\n"
        "For each failure: (1) root cause, (2) business impact, (3) recommended fix priority (P1/P2/P3). "
        "Output JSON: {\"analyses\": [{\"check\": str, \"root_cause\": str, \"business_impact\": str, \"priority\": str}]}"
    )
    parsed, source = call_llm_json(prompt, max_tokens=512)
    if parsed and isinstance(parsed.get("analyses"), list):
        lines = [
            f"• {a['check']} [{a.get('priority','?')}]: {a['root_cause']} | impact: {a['business_impact']}"
            for a in parsed["analyses"]
        ]
        analysis = f"LLM analysis ({source}):\n" + "\n".join(lines)
    else:
        analysis = f"LLM unavailable ({source}). Manual review:\n" + failure_lines
    return {"checks": checks, "analysis": analysis}


async def build_bmc_report(state: QABmcState) -> QABmcState:
    checks = state.get("checks") or _collect_checks(state)
    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")
    skipped = sum(1 for c in checks if c["status"] in ("SKIP", "WARN"))
    report = {
        "run_id": state.get("run_id"),
        "host": state.get("host", "https://yatabase.gftd.ai"),
        "ts": int(time.time() * 1000),
        "org_did": state.get("org_did", "anon"),
        "summary": {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(checks),
            "ok": failed == 0,
        },
        "checks": checks,
        "canvas": {
            "version": state.get("canvas_version", 0),
            "blocks_present": state.get("canvas_blocks_present", []),
            "blocks_missing": state.get("canvas_blocks_missing", []),
        },
        "hypotheses": {
            "active": state.get("hyp_active_count", 0),
            "total": state.get("hyp_total_count", 0),
            "block_health": state.get("hyp_block_health", []),
        },
        "dry_run": {
            "status": state.get("dry_run_status", "SKIP"),
            "idle": state.get("dry_run_idle", False),
            "notes": state.get("dry_run_notes", ""),
            "picked": state.get("dry_run_picked"),
            "measurement": state.get("dry_run_measurement"),
            "decision": state.get("dry_run_decision"),
        },
        "analysis": state.get("analysis", ""),
    }
    _log.info(
        "[qa_bmc][%s] report: pass=%d fail=%d skip=%d ok=%s",
        state.get("run_id"), passed, failed, skipped, failed == 0,
    )
    return {"passed": passed, "failed": failed, "skipped": skipped, "report": report}


# ── Graph ─────────────────────────────────────────────────────────────────────

_g: StateGraph = StateGraph(QABmcState)
_g.add_node("probe_canvas", probe_canvas)
_g.add_node("probe_hypotheses", probe_hypotheses)
_g.add_node("run_bmc_dry", run_bmc_dry)
_g.add_node("analyze_bmc", analyze_bmc)
_g.add_node("build_bmc_report", build_bmc_report)
_g.add_edge(START, "probe_canvas")
_g.add_edge("probe_canvas", "probe_hypotheses")
_g.add_edge("probe_hypotheses", "run_bmc_dry")
_g.add_edge("run_bmc_dry", "analyze_bmc")
_g.add_edge("analyze_bmc", "build_bmc_report")
_g.add_edge("build_bmc_report", END)
GRAPH = _g.compile()
