"""
DecommissionCell — End-of-life cell.

Per ADR-2605201400 §3 + Open Question 5 + ADR-2605202200 (cell.py contract).

Trigger:    cron + governance-vote + lifespan-expiry-monitor
            Monthly cron (0 0 1 * *) checks lifespanYears expiry.
Effect:     Decommission plan → disconnect from utility → physical teardown
            (reverse construction Pregel) → land return → release stewardship
            → archive site → permanent L2 anchor for multi-generational record.
Murakumo:   dan (leader)

Constitutional alignment: ADR-2605192100 §mission.land_as_religious_trust —
land does not belong to the project, the project was stewarded by the land.
End-of-life is a religious ritual return.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import START, END, StateGraph

from kotodama.cell_runtime import (
    CellDeps,
    default_state_from_event,
    default_thread_id_from_event,
)


class DecommissionState(TypedDict, total=False):
    # Input (from cron OR explicit governance vote)
    siteDid: str
    planDid: str
    triggerReason: Literal["lifespan-expiry", "governance-vote", "force-majeure"]
    governanceProposalUri: str | None

    # Decommission workflow
    decommissionBomCid: str  # teardown BoM (reverse construction)
    recyclableMaterials: list[dict[str, Any]]
    urbanMiningRoutingCid: str  # → open-robo urban-mining cell

    # Physical teardown
    teardownProgress: list[dict[str, Any]]
    witnessAttestations: list[dict[str, Any]]

    # Land return
    ecologyRestorationCid: str
    landReturnAttested: bool

    # Stewardship release
    landRegistryUpdated: bool
    siteState: Literal["decommissioned", "in-progress", "ecology-debt"]

    # Audit
    _event_uri: str
    _event_nsid: str


# ─── Nodes ──────────────────────────────────────────────────────────


def decommission_plan(state: DecommissionState, deps: CellDeps) -> DecommissionState:
    """Generate teardown BoM (reverse construction) + identify recyclable materials.

    Routes recyclable to open-robo urban-mining cell per
    60-apps/etzhayyim-project-open-robo/docs/urban-mining-automation-v1.md.
    """
    raise NotImplementedError(
        "Requires reverse-BoM derivation from original planDid + open-robo urban-mining cell binding."
    )


def disconnect_from_utility(state: DecommissionState, deps: CellDeps) -> DecommissionState:
    """Coordinate with open-ot to retire defineLoop + mark utility assets retired."""
    raise NotImplementedError(
        "Requires open-ot retireLoop XRPC + per-utility lexicon retired-state update."
    )


def physical_teardown(state: DecommissionState, deps: CellDeps) -> DecommissionState:
    """Re-dispatch Giemon fleet for disassembly. Witness audit applies."""
    raise NotImplementedError(
        "Requires kotodama.open_robo.fleet + AuditWitnessCell coordination."
    )


def land_return(state: DecommissionState, deps: CellDeps) -> DecommissionState:
    """Restore ecology to baseline per original submitSiteSurvey snapshot.

    Emits recordPhysicalAuditEvent class=community-event subtype=land-return.
    """
    raise NotImplementedError(
        "Requires post-restoration survey + ecology delta comparison + audit emission."
    )


def release_stewardship(state: DecommissionState, deps: CellDeps) -> DecommissionState:
    """Update LandRegistry (or OceanStewardship / RiverStewardship / etc.).

    Site returns to commons OR transfers to new stewardship per governance choice.
    """
    raise NotImplementedError(
        "Requires deps.geth_private_port + LandRegistry.sol releaseSteward()."
    )


def archive_site(state: DecommissionState, deps: CellDeps) -> DecommissionState:
    """Finalize site DID state → decommissioned. Permanent L2 anchor for
    multi-generational record per ADR-2605192100 §mission.multi_generational_priority.
    """
    raise NotImplementedError(
        "Requires deps.sdk for final MST snapshot + Base L2 EtzhayyimAnchor commit."
    )


# ─── Graph builder ──────────────────────────────────────────────────


def build_graph(deps: CellDeps):
    g = StateGraph(DecommissionState)

    g.add_node("decommission_plan", lambda s: decommission_plan(s, deps))
    g.add_node("disconnect_from_utility", lambda s: disconnect_from_utility(s, deps))
    g.add_node("physical_teardown", lambda s: physical_teardown(s, deps))
    g.add_node("land_return", lambda s: land_return(s, deps))
    g.add_node("release_stewardship", lambda s: release_stewardship(s, deps))
    g.add_node("archive_site", lambda s: archive_site(s, deps))

    g.add_edge(START, "decommission_plan")
    g.add_edge("decommission_plan", "disconnect_from_utility")
    g.add_edge("disconnect_from_utility", "physical_teardown")
    g.add_edge("physical_teardown", "land_return")
    g.add_edge("land_return", "release_stewardship")
    g.add_edge("release_stewardship", "archive_site")
    g.add_edge("archive_site", END)

    return g.compile(checkpointer=deps.checkpointer)


def state_from_event(event_record: dict, nsid: str) -> dict:
    """Cron-triggered: synthesize event from siteDid + lifespan expiry detection.

    For governance-vote trigger: event_record carries proposal URI in value.
    """
    return default_state_from_event(event_record, nsid)


def thread_id_from_event(event_record: dict, nsid: str) -> str:
    value = event_record.get("value", {})
    site_did = value.get("siteDid") or event_record.get("rkey", "unknown")
    return f"DecommissionCell:{site_did}"


def healthz_extra(deps: CellDeps) -> dict:
    return {
        "phase": "end-of-life",
        "trigger": "cron-monthly + governance-vote + lifespan-expiry",
        "religious_invariant": "land_as_religious_trust — return is ritual (ADR-2605192100 §mission)",
        "feeds_urban_mining": "60-apps/etzhayyim-project-open-robo/docs/urban-mining-automation-v1.md",
    }
