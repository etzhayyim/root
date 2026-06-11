"""
SiteSurveyCell — Phase 1 of kuni-umi 4-phase deployment workflow.

Per ADR-2605201400 §3 (kuni-umi master) + ADR-2605201500 (S1 solo survey) +
ADR-2605202200 (cell.py runtime contract).

Trigger:    MST listener on `com.etzhayyim.apps.etzhayyim.kuniUmi.defineDeploymentSite`
Effect:     Dispatch Giemon scout fleet → collect sensor blobs → DMN gate →
            N ≥ 2 witness signatures → emit `submitSiteSurvey` MST record.
Murakumo:   naphtali (leader)

Hardware deps (NotImplementedError until provisioned per S1 checklist):
  - Giemon Otete v1 with did:web:etzhayyim.com:kuniumi:robot:otete-001
  - Giemon Mimi base-station with did:web:etzhayyim.com:kuniumi:robot:mimi-base-001
  - LandRegistry plot (山中湖 candidate) registered
  - simeon IPFS endpoint reachable (12D3KooWMjzJdChBp9HqorSvxkrfSFfSNanjR8tJmtmJwVmZif16)
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import START, END, StateGraph

from kotodama.cell_runtime import (
    CellDeps,
    default_state_from_event,
    default_thread_id_from_event,
)


class SiteSurveyState(TypedDict, total=False):
    # Input (from defineDeploymentSite MST event)
    siteDid: str
    siteCode: str
    geo: str  # GeoJSON Feature
    utilityClass: Literal[
        "electric", "gas", "water", "network", "power", "rail", "airplane", "port", "multi"
    ]
    domain: Literal["terrestrial", "ocean", "river", "atmosphere", "orbit"]
    jurisdictionDid: str
    stewardDid: str
    intendedUse: str
    intendedBeneficiaryDids: list[str]
    localLawAttestationCid: str

    # Phase 1 outputs
    fleetId: str
    surveyBlobCids: list[str]
    ecologyBaseline: dict[str, Any]
    witnessAttestations: list[dict[str, Any]]
    accepted: bool
    rejectionReason: str | None

    # Audit
    _event_uri: str
    _event_cid: str
    _event_nsid: str


# ─── Nodes ──────────────────────────────────────────────────────────


def allocate_scout_fleet(state: SiteSurveyState, deps: CellDeps) -> SiteSurveyState:
    """Request N ≥ 2 Giemon scout robots from open-robo fleet."""
    raise NotImplementedError(
        "Requires Giemon Otete + Mimi base-station fleet operational. "
        "See ADR-2605201500 hardware/DID provisioning checklist."
    )


def collect_sensor_blob(state: SiteSurveyState, deps: CellDeps) -> SiteSurveyState:
    """Collect RGB-D / LIDAR / chem-sensor / multispectral blobs and pin to IPFS."""
    raise NotImplementedError(
        "Requires deps.sdk for IPFS pin via @etzhayyim/sdk and live Giemon fleet."
    )


def jurisdiction_eligibility(state: SiteSurveyState, deps: CellDeps) -> SiteSurveyState:
    """Run DMN: 20-actors/kuni-umi/dmn/jurisdiction-eligibility.md.

    Default scaffold returns accepted=True for syntax validation; real DMN
    integration requires ADR-2605201400 §5 Rego policy implementation.
    """
    state["accepted"] = True
    state["rejectionReason"] = None
    return state


def witness_attest(state: SiteSurveyState, deps: CellDeps) -> SiteSurveyState:
    """Collect Ed25519 signatures from N ≥ 2 robot DIDs over the survey blob hash."""
    raise NotImplementedError(
        "Requires per-robot DID keypair registration and signing endpoint. "
        "Constitutional invariant: N >= 2 must hold (ADR-2605201400 §9)."
    )


def emit_survey(state: SiteSurveyState, deps: CellDeps) -> SiteSurveyState:
    """Write `submitSiteSurvey` MST record via @etzhayyim/sdk."""
    raise NotImplementedError(
        "Requires deps.sdk (@etzhayyim/sdk subprocess RPC). "
        "Writes com.etzhayyim.apps.etzhayyim.kuniUmi.submitSiteSurvey to MST."
    )


# ─── Graph builder ──────────────────────────────────────────────────


def build_graph(deps: CellDeps):
    """Build the SiteSurveyCell LangGraph per ADR-2605202200 §1 contract."""
    g = StateGraph(SiteSurveyState)

    g.add_node("allocate_scout_fleet", lambda s: allocate_scout_fleet(s, deps))
    g.add_node("collect_sensor_blob", lambda s: collect_sensor_blob(s, deps))
    g.add_node("jurisdiction_eligibility", lambda s: jurisdiction_eligibility(s, deps))
    g.add_node("witness_attest", lambda s: witness_attest(s, deps))
    g.add_node("emit_survey", lambda s: emit_survey(s, deps))

    g.add_edge(START, "allocate_scout_fleet")
    g.add_edge("allocate_scout_fleet", "collect_sensor_blob")
    g.add_edge("collect_sensor_blob", "jurisdiction_eligibility")

    def router(state: SiteSurveyState) -> str:
        return "witness_attest" if state.get("accepted") else "emit_survey"

    g.add_conditional_edges("jurisdiction_eligibility", router)
    g.add_edge("witness_attest", "emit_survey")
    g.add_edge("emit_survey", END)

    return g.compile(checkpointer=deps.checkpointer)


def state_from_event(event_record: dict, nsid: str) -> dict:
    """Map defineDeploymentSite event to SiteSurveyState."""
    return default_state_from_event(event_record, nsid)


def thread_id_from_event(event_record: dict, nsid: str) -> str:
    """Thread id = siteDid (one survey per site, idempotent re-processing)."""
    value = event_record.get("value", {})
    site_did = value.get("siteDid") or value.get("siteCode") or event_record.get("rkey", "unknown")
    return f"SiteSurveyCell:{site_did}"


def healthz_extra(deps: CellDeps) -> dict:
    """Cell-specific healthz fields per ADR-2605202200 §5."""
    return {
        "phase": "1-survey",
        "fleet_required": ["otete", "mimi-base-station"],
        "witness_invariant_min": 2,
        "trigger_nsid": "com.etzhayyim.apps.etzhayyim.kuniUmi.defineDeploymentSite",
    }
