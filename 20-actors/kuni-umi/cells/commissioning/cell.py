"""
CommissioningCell — Phase 4 of kuni-umi 4-phase deployment workflow.

Per ADR-2605201400 §3 + ADR-2605202200 (cell.py contract).

Trigger:    MST listener on terminal recordConstructionProgress with phase=handoff-ready
Effect:     Register assets with open-* utility lexicons → register loops with
            open-ot defineLoop → run acceptance test → emit `commissionDeployment`
            → site transitions to `operational`.
Murakumo:   simeon (leader)

After commissionDeployment, kuni-umi is observer-only for that site (except
AuditWitnessCell continues continuous coverage, DecommissionCell activates
at lifespan expiry).
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any, Literal, TypedDict

from langgraph.graph import START, END, StateGraph

from kotodama.cell_runtime import (
    CellDeps,
    default_state_from_event,
    default_thread_id_from_event,
)

# Runnable 3-layer handoff reference (tested offline; see robotics/commissioning.py).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "robotics"))
from commissioning import run_microgrid_acceptance  # noqa: E402


class CommissioningState(TypedDict, total=False):
    # Input (from terminal recordConstructionProgress)
    planDid: str
    siteDid: str
    handoffBlobCid: str

    # Commissioning workflow
    utilityAssetDids: list[str]
    openOtLoopDids: list[str]
    acceptanceTest: dict[str, Any]
    stewardOperatorDid: str

    # Output
    commissionDid: str
    siteState: Literal["operational", "punch-list", "rejected"]
    commissionedAt: str

    # Audit
    _event_uri: str
    _event_nsid: str


# ─── Nodes ──────────────────────────────────────────────────────────


def register_with_utility(state: CommissioningState, deps: CellDeps) -> CommissioningState:
    """For each commissioned asset, call the relevant open-* utility lexicon.

    S2 single-utility (electric): open-denki defineGenerationNode / defineSubstation /
        defineFeeder / registerSmartMeter / recordRenewableOutput.
    S3 multi-utility: + open-water defineReservoir/defineMain + open-network defineSite/defineLink.
    """
    raise NotImplementedError(
        "Requires deps.sdk + open-* utility XRPC calls (open-denki/open-gas/open-water/open-network/...)."
    )


def register_with_open_ot(state: CommissioningState, deps: CellDeps) -> CommissioningState:
    """For each control loop, call open-ot defineDevice / defineCell / defineLoop.

    Per ADR-2605151200 — open-ot WASM PLC takes over steady-state operation here.
    S2 has 7 loops to register; S3 + may add water/network control loops in future.

    The loop-DID set is recorded here (the dry-run, no-XRPC reference is
    robotics/commissioning.py). The LIVE XRPC write still requires deps.sdk and is
    gated; when deps.sdk is absent (R0 / offline), we record the intent only.
    """
    loop_dids = state.get("openOtLoopDids") or [
        "did:web:etzhayyim.com:openot:loop:droop-p-f",
        "did:web:etzhayyim.com:openot:loop:anti-islanding-rocof",
    ]
    state["openOtLoopDids"] = loop_dids
    if getattr(deps, "sdk", None) is None:
        return state  # R0 offline: loop DIDs recorded, no live XRPC (G15/G8)
    raise NotImplementedError(
        "Live open-ot XRPC (com.etzhayyim.apps.openOt.defineDevice/defineCell/defineLoop) "
        "requires deps.sdk — gated until S2 Council ratify."
    )


def enrol_stream(state: CommissioningState, deps: CellDeps) -> CommissioningState:
    """Start telemetry stream (smart-meter / pressure-log / quality-sample / utilization)."""
    raise NotImplementedError(
        "Requires per-utility-class telemetry binding (open-denki recordMeterReading, "
        "open-water recordReading, open-network recordUtilization, etc.)."
    )


def commission_test(state: CommissioningState, deps: CellDeps) -> CommissioningState:
    """Run short acceptance test (e.g., S2 microgrid: black-start + droop-P-f response).

    Reuses open-ot reference BFB cells: ANTI_ISLANDING_ROCOF, DROOP_P_F, BLACK_START_SEQ.
    The deterministic acceptance test is robotics/commissioning.run_microgrid_acceptance
    (the open-ot field-tier loop's :representative twin). R1: when the committed
    device-in-the-loop golden trace (robotics/golden/device_loop_trace.json — the
    REAL wasm cells under Wasmtime, see robotics/device_loop.py) is present and
    consistent, the acceptance tier is recorded as "device-wasm"; absent or
    inconsistent evidence stays "python-twin". Live device-in-the-loop against
    field hardware remains gated behind deps.sdk + the certified safety PLC.
    """
    load_step_kw = float(state.get("acceptanceTest", {}).get("loadStepKw", 140.0))
    result = run_microgrid_acceptance(load_step_kw=load_step_kw)

    tier = "python-twin"
    golden = pathlib.Path(__file__).resolve().parents[2] / "robotics" / "golden" / "device_loop_trace.json"
    if golden.exists():
        import json
        normal = next(
            (r for r in json.loads(golden.read_text()).get("results", [])
             if r.get("scenario") == "normal-load-step"),
            None,
        )
        if (
            normal
            and normal.get("freq_restored")
            and not normal.get("rocof_trip", True)
            and normal.get("twin_verdict_match")
            and normal.get("server_held_key") is False
        ):
            tier = "device-wasm"

    state["acceptanceTest"] = {
        "passed": result["passed"],
        "acceptanceTier": tier,
        "finalFreqHz": result["final_freq_hz"],
        "rocofTripped": result["rocof_tripped"],
        "loadStepKw": load_step_kw,
        "dryRun": True,
    }
    return state


def commission(state: CommissioningState, deps: CellDeps) -> CommissioningState:
    """Emit `commissionDeployment` MST record + site state → operational."""
    raise NotImplementedError(
        "Requires deps.sdk for MST write of com.etzhayyim.apps.etzhayyim.kuniUmi.commissionDeployment."
    )


def transfer_stewardship(state: CommissioningState, deps: CellDeps) -> CommissioningState:
    """Formal transfer of day-to-day operation to steward + open-ot orchestrator."""
    raise NotImplementedError(
        "Requires Steward Lv5+ attestation chain + open-ot stewardOperatorDid binding."
    )


# ─── Graph builder ──────────────────────────────────────────────────


def build_graph(deps: CellDeps):
    g = StateGraph(CommissioningState)

    g.add_node("register_with_utility", lambda s: register_with_utility(s, deps))
    g.add_node("register_with_open_ot", lambda s: register_with_open_ot(s, deps))
    g.add_node("enrol_stream", lambda s: enrol_stream(s, deps))
    g.add_node("commission_test", lambda s: commission_test(s, deps))
    g.add_node("commission", lambda s: commission(s, deps))
    g.add_node("transfer_stewardship", lambda s: transfer_stewardship(s, deps))

    g.add_edge(START, "register_with_utility")
    g.add_edge("register_with_utility", "register_with_open_ot")
    g.add_edge("register_with_open_ot", "enrol_stream")
    g.add_edge("enrol_stream", "commission_test")

    def test_router(state: CommissioningState) -> str:
        passed = state.get("acceptanceTest", {}).get("passed", False)
        if not passed:
            # Punch list — return to construction phase (separate ADR for re-entry handling)
            return END
        return "commission"

    g.add_conditional_edges("commission_test", test_router)
    g.add_edge("commission", "transfer_stewardship")
    g.add_edge("transfer_stewardship", END)

    return g.compile(checkpointer=deps.checkpointer)


def state_from_event(event_record: dict, nsid: str) -> dict:
    return default_state_from_event(event_record, nsid)


def thread_id_from_event(event_record: dict, nsid: str) -> str:
    value = event_record.get("value", {})
    plan_did = value.get("planDid") or event_record.get("rkey", "unknown")
    return f"CommissioningCell:{plan_did}"


def healthz_extra(deps: CellDeps) -> dict:
    return {
        "phase": "4-commissioning",
        "trigger_nsid": "com.etzhayyim.apps.etzhayyim.kuniUmi.recordConstructionProgress",
        "trigger_filter": "phase=handoff-ready",
        "hand_off_targets": ["open-ot WASM PLC", "open-* utility lexicons"],
    }
