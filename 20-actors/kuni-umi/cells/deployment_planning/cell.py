"""
DeploymentPlanningCell — Phase 2 of kuni-umi 4-phase deployment workflow.

Per ADR-2605201400 §3 + ADR-2605202200 (cell.py contract).

Trigger:    MST listener on `com.etzhayyim.apps.etzhayyim.kuniUmi.submitSiteSurvey`
            (accepted=true)
Effect:     Derive target topology → invoke UNSPSC fleet for BoM →
            counterparty filter → proportionality DMN → optional governance
            vote → payment plan → fleet allocation → emit
            `proposeDeploymentPlan` (BoM encrypted).
Murakumo:   zebulun (leader, treasury-adjacent for BoM cost calc)

BoM consolidation MIP solver (S3): see
20-actors/kuni-umi/cells/deployment_planning/bom_consolidation.py (future).
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import START, END, StateGraph

from kotodama.cell_runtime import (
    CellDeps,
    default_state_from_event,
    default_thread_id_from_event,
)


class DeploymentPlanningState(TypedDict, total=False):
    # Input (from submitSiteSurvey MST event)
    siteDid: str
    surveyDid: str
    surveyBlobCids: list[str]
    ecologyBaseline: dict[str, Any]
    populationImpacted: int
    reversibilityScore: int

    # Phase 2 outputs
    planCode: str
    targetTopologyDids: list[str]
    bomEnvelopeCid: str
    fleetAllocation: dict[str, Any]
    paymentPlanCid: str
    timeline: dict[str, Any]
    lifespanYears: int
    requiresGovernance: bool
    governanceProposalUri: str | None
    requiresPublicFund: bool
    publicFundProposalUri: str | None
    accepted: bool
    decision: Literal[
        "accept", "reject", "awaiting-governance", "awaiting-force-authorization", "awaiting-public-fund"
    ]
    rejectionReason: str | None

    # Audit
    _event_uri: str
    _event_nsid: str


# ─── Nodes ──────────────────────────────────────────────────────────


def derive_target_topology(state: DeploymentPlanningState, deps: CellDeps) -> DeploymentPlanningState:
    """Translate utilityClass + survey blob into open-* CIM record target DIDs."""
    raise NotImplementedError(
        "Requires utilityClass-to-CIM mapper (open-denki/open-gas/open-water/open-network/...). "
        "S2 single-utility scope = open-denki defineGenerationNode/defineSubstation/defineFeeder/registerSmartMeter."
    )


def bom_generation(state: DeploymentPlanningState, deps: CellDeps) -> DeploymentPlanningState:
    """Parallel dispatch UNSPSC agent fleet for each commodity in target topology.

    Per ADR-2605171300 — fleet has 18,345 specialized agents indexed by UNSPSC code.
    """
    raise NotImplementedError(
        "Requires kotodama.unispsc.dispatch helper + 18,345 specialized agents at "
        "40-engine/kotoba/crates/kotoba-kotodama/unispsc_agents/. Currently MCP server exists but Python "
        "dispatch wrapper does not (per session residency audit 2026-05-20)."
    )


def counterparty_classification(state: DeploymentPlanningState, deps: CellDeps) -> DeploymentPlanningState:
    """DMN: 20-actors/kuni-umi/dmn/counterparty-classification.md.

    Reject suppliers flagged Non-Aligned in ChartersComplianceRegistry per ADR-2605192230.
    """
    raise NotImplementedError(
        "Requires deps.base_l2_port + ChartersComplianceRegistry.sol address; "
        "currently deployed only on local Anvil (per deps.toml [platform.l2.anchor_contract])."
    )


def proportionality_check(state: DeploymentPlanningState, deps: CellDeps) -> DeploymentPlanningState:
    """DMN: 20-actors/kuni-umi/dmn/proportionality-check.md.

    Sets requiresGovernance / requiresPublicFund based on:
      - populationImpacted > 100  → governance vote
      - estimatedCostUsdc > 1M    → Public Fund grant evaluation
      - ecologyImpactScore > 30   → ecologist Council review
      - reversibilityScore < 50   → Council supermajority
      - domain != terrestrial     → Extended Sovereignty vote (ADR-2605192330)
      - intendedUse=transparent-force-rd → ForceAuthorization vote (ADR-2605192315)
    """
    pop = state.get("populationImpacted", 0)
    state["requiresGovernance"] = pop > 100
    # estimatedCostUsdc not yet wired in this scaffold; leave requiresPublicFund false
    state["requiresPublicFund"] = False
    return state


def payment_plan(state: DeploymentPlanningState, deps: CellDeps) -> DeploymentPlanningState:
    """Schedule USDC milestone disbursements via Etzhayyim.pay() + TitheRouter 90/10."""
    raise NotImplementedError(
        "Requires deps.base_l2_port + MilestoneEscrow.sol + TitheRouter.sol addresses. "
        "MilestoneEscrow not yet authored (ADR-2605192145 §future)."
    )


def fleet_allocation(state: DeploymentPlanningState, deps: CellDeps) -> DeploymentPlanningState:
    """Request Giemon fleet from open-robo + estimate robot-hours."""
    raise NotImplementedError(
        "Requires kotodama.open_robo.fleet (does not exist yet — see session residency audit)."
    )


def propose_plan(state: DeploymentPlanningState, deps: CellDeps) -> DeploymentPlanningState:
    """Write encrypted `proposeDeploymentPlan` MST record + governance proposals if needed."""
    raise NotImplementedError(
        "Requires deps.sdk for XChaCha20-Poly1305 envelope (ADR-2605181100) + MST write."
    )


# ─── Graph builder ──────────────────────────────────────────────────


def build_graph(deps: CellDeps):
    g = StateGraph(DeploymentPlanningState)

    g.add_node("derive_target_topology", lambda s: derive_target_topology(s, deps))
    g.add_node("bom_generation", lambda s: bom_generation(s, deps))
    g.add_node("counterparty_classification", lambda s: counterparty_classification(s, deps))
    g.add_node("proportionality_check", lambda s: proportionality_check(s, deps))
    g.add_node("payment_plan", lambda s: payment_plan(s, deps))
    g.add_node("fleet_allocation", lambda s: fleet_allocation(s, deps))
    g.add_node("propose_plan", lambda s: propose_plan(s, deps))

    g.add_edge(START, "derive_target_topology")
    g.add_edge("derive_target_topology", "bom_generation")
    g.add_edge("bom_generation", "counterparty_classification")
    g.add_edge("counterparty_classification", "proportionality_check")
    g.add_edge("proportionality_check", "payment_plan")
    g.add_edge("payment_plan", "fleet_allocation")
    g.add_edge("fleet_allocation", "propose_plan")
    g.add_edge("propose_plan", END)

    return g.compile(checkpointer=deps.checkpointer)


def state_from_event(event_record: dict, nsid: str) -> dict:
    return default_state_from_event(event_record, nsid)


def thread_id_from_event(event_record: dict, nsid: str) -> str:
    """One plan per site (planCode is derived). Idempotency via siteDid."""
    value = event_record.get("value", {})
    site_did = value.get("siteDid") or event_record.get("rkey", "unknown")
    return f"DeploymentPlanningCell:{site_did}"


def healthz_extra(deps: CellDeps) -> dict:
    return {
        "phase": "2-planning",
        "trigger_nsid": "com.etzhayyim.apps.etzhayyim.kuniUmi.submitSiteSurvey",
        "depends_on_fleet": ["kotodama.unispsc.dispatch", "kotodama.open_robo.fleet"],
        "depends_on_contracts": [
            "ChartersComplianceRegistry",
            "TitheRouter",
            "MilestoneEscrow",
        ],
    }
