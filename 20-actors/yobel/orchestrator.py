"""
Yobel BPMN orchestrator — maps bpmn/yobel-rite-lifecycle.bpmn ServiceTasks to LangGraph cells.

Per ADR-2605201800. This is a thin orchestrator that:
  1. Reads the BPMN definition (yobel-rite-lifecycle.bpmn)
  2. Maps each ServiceTask `implementation="cell:<name>"` to the corresponding cell.build_graph()
  3. Drives state through the BPMN flow (declare → ratify → enroll fan-out → release → audit)

This is NOT a full BPMN engine — it implements only the subset of BPMN constructs that
yobel uses: sequenceFlow, exclusiveGateway, parallelGateway, multiInstance loop on enrollment,
and event-subprocess for audit witness. For richer execution semantics, route through the
shared etzhayyim-bpmn-sdk (TS) at runtime; this orchestrator is the Python-side reference.

Use cases:
  - `dry_run.py` scripts (sample rite fixtures) drive end-to-end without external BPMN engine
  - integration tests verify cell sequencing matches BPMN sequenceFlow
  - operators inspect rite state mid-flow via the YobelOrchestrator.snapshot() method
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver

from yobel.cells.audit_witness.cell import build_graph as build_audit_witness
from yobel.cells.creditor_enrollment.cell import build_graph as build_creditor_enrollment
from yobel.cells.debtor_enrollment.cell import build_graph as build_debtor_enrollment
from yobel.cells.release_settlement.cell import build_graph as build_release_settlement
from yobel.cells.rite_declaration.cell import build_graph as build_rite_declaration


@dataclass
class YobelPorts:
    """All 17 ports collected for the orchestrator. None for stubbed dry runs."""

    rite_registry: Any = None
    creditor_enrollment: Any = None
    council_sbt: Any = None
    charter_compliance: Any = None
    erc725: Any = None
    envelope_crypto: Any = None
    tithe_router: Any = None
    base_l2_paymaster: Any = None
    lawfirm_invoke: Any = None
    anchor_bridge: Any = None
    audit_witness_emit: Any = None
    witness_keystore: Any = None
    audit_log: Any = None
    public_fund: Any = None
    council_notifier: Any = None
    council_ratification: Any = None
    land_registry: Any = None


@dataclass
class RiteLifecycleSnapshot:
    """Read-only mid-flow state snapshot for operators / tests."""

    rite_id: str
    phase: str  # "declared" / "ratified" / "enrolling" / "releasing" / "complete" / "rejected" / "tampered"
    rite_status: str  # from rite_declaration cell
    creditor_enrollments: list[dict] = field(default_factory=list)
    debtor_enrollments: list[dict] = field(default_factory=list)
    releases: list[dict] = field(default_factory=list)
    audit_events: list[dict] = field(default_factory=list)


class YobelOrchestrator:
    """Drive a rite through declare → ratify → enroll (fan-out) → release → audit.

    Matches the BPMN flow in bpmn/yobel-rite-lifecycle.bpmn 1:1:

        Start → rite_declaration → Council DMN gate → ExclusiveGateway(ratified?)
            ↓ratified=false: End_Rejected
            ↓ratified=true: ParallelGateway(fan-out)
                ├── creditor_enrollment (multi-instance)
                └── debtor_enrollment (multi-instance)
              ParallelGateway(join)
            → release_settlement (multi-instance) → End_RiteComplete
        SubProcess(audit_witness) — continuous, triggered on every super-step + every release MST event

    Cells are built lazily (only when needed) so a dry-run with no debtors doesn't waste
    setup time on release_settlement build_graph.
    """

    def __init__(self, ports: YobelPorts, checkpointer: BaseCheckpointSaver):
        self.ports = ports
        self.checkpointer = checkpointer
        self._declaration = None
        self._creditor = None
        self._debtor = None
        self._release = None
        self._audit = None

    # ─── cell lazy-build ────────────────────────────────────────────

    def declaration_graph(self):
        if self._declaration is None:
            self._declaration = build_rite_declaration(
                checkpointer=self.checkpointer,
                charter_compliance_port=self.ports.charter_compliance,
                council_sbt_port=self.ports.council_sbt,
                council_ratification_port=self.ports.council_ratification,
                land_registry_port=self.ports.land_registry,
                anchor_bridge=self.ports.anchor_bridge,
            )
        return self._declaration

    def creditor_graph(self):
        if self._creditor is None:
            self._creditor = build_creditor_enrollment(
                checkpointer=self.checkpointer,
                rite_registry_port=self.ports.rite_registry,
                council_sbt_port=self.ports.council_sbt,
                charter_compliance_port=self.ports.charter_compliance,
                erc725_port=self.ports.erc725,
                envelope_crypto=self.ports.envelope_crypto,
                anchor_bridge=self.ports.anchor_bridge,
            )
        return self._creditor

    def debtor_graph(self):
        if self._debtor is None:
            self._debtor = build_debtor_enrollment(
                checkpointer=self.checkpointer,
                rite_registry_port=self.ports.rite_registry,
                creditor_enrollment_port=self.ports.creditor_enrollment,
                council_sbt_port=self.ports.council_sbt,
                charter_compliance_port=self.ports.charter_compliance,
                envelope_crypto=self.ports.envelope_crypto,
                anchor_bridge=self.ports.anchor_bridge,
            )
        return self._debtor

    def release_graph(self):
        if self._release is None:
            self._release = build_release_settlement(
                checkpointer=self.checkpointer,
                creditor_enrollment_port=self.ports.creditor_enrollment,
                envelope_crypto=self.ports.envelope_crypto,
                tithe_router_port=self.ports.tithe_router,
                base_l2_paymaster=self.ports.base_l2_paymaster,
                lawfirm_invoke=self.ports.lawfirm_invoke,
                anchor_bridge=self.ports.anchor_bridge,
                audit_witness_emit=self.ports.audit_witness_emit,
            )
        return self._release

    def audit_graph(self):
        if self._audit is None:
            self._audit = build_audit_witness(
                checkpointer=self.checkpointer,
                audit_log_port=self.ports.audit_log,
                witness_keystore=self.ports.witness_keystore,
                anchor_bridge=self.ports.anchor_bridge,
                public_fund_port=self.ports.public_fund,
                council_notifier=self.ports.council_notifier,
            )
        return self._audit

    # ─── BPMN flow execution ────────────────────────────────────────

    def declare_rite(self, *, rite_id: str, rite_input: dict) -> dict:
        """Start_DeclareRequest → Task_RiteDeclaration → Gate_CouncilRatification → Gateway_CouncilDecision."""
        config = {"configurable": {"thread_id": f"declare-{rite_id}"}}
        result = self.declaration_graph().invoke(rite_input, config)
        self._witness_super_step(
            rite_id=rite_id,
            source_kind="super_step",
            state_root_before="genesis",
            state_root_after=result.get("rite_vertex_uri", ""),
            tx_digest=f"declare:{rite_id}",
            event_payload={"step": "declare_rite", "status": result.get("rite_status")},
        )
        return result

    def enroll_creditor(self, *, rite_id: str, enrollment_input: dict) -> dict:
        """Task_CreditorEnrollment (multiInstance loop iteration)."""
        config = {"configurable": {"thread_id": f"credit-{rite_id}-{enrollment_input.get('creditor_did','')}"}}
        result = self.creditor_graph().invoke(enrollment_input, config)
        self._witness_super_step(
            rite_id=rite_id,
            source_kind="super_step",
            state_root_before="enroll_creditor:before",
            state_root_after=result.get("enrollment_vertex_uri", ""),
            tx_digest=f"credit:{enrollment_input.get('creditor_did','')}",
            event_payload={"step": "enroll_creditor", "debt_count": result.get("debt_count", 0)},
        )
        return result

    def enroll_debtor(self, *, rite_id: str, enrollment_input: dict) -> dict:
        """Task_DebtorEnrollment (multiInstance loop iteration)."""
        config = {"configurable": {"thread_id": f"debt-{rite_id}-{enrollment_input.get('debtor_did','')}"}}
        result = self.debtor_graph().invoke(enrollment_input, config)
        self._witness_super_step(
            rite_id=rite_id,
            source_kind="super_step",
            state_root_before="enroll_debtor:before",
            state_root_after=result.get("enrollment_vertex_uri", ""),
            tx_digest=f"debt:{enrollment_input.get('debtor_did','')}",
            event_payload={
                "step": "enroll_debtor",
                "pairing_status": result.get("pairing_status", ""),
            },
        )
        return result

    def record_release(self, *, rite_id: str, release_input: dict) -> dict:
        """Task_ReleaseSettlement (multiInstance loop iteration). audit witness fires inside cell."""
        config = {"configurable": {"thread_id": f"rel-{rite_id}-{release_input.get('release_id','')}"}}
        result = self.release_graph().invoke(release_input, config)
        # release_settlement.cell.emit_audit_event already called audit_witness_emit;
        # we additionally witness the super-step transition for chain continuity.
        self._witness_super_step(
            rite_id=rite_id,
            source_kind="release_finalized",
            state_root_before="release:before",
            state_root_after=result.get("release_vertex_uri", ""),
            tx_digest=f"rel:{release_input.get('release_id','')}",
            event_payload={
                "step": "record_release",
                "settlement_ok": result.get("settlement_ok", False),
                "base_l2_tx_hash": result.get("base_l2_tx_hash", ""),
            },
        )
        return result

    def _witness_super_step(self, **kwargs) -> dict:
        """Invoke audit_witness cell on a super-step boundary."""
        if self.ports.audit_log is None and self.ports.witness_keystore is None:
            # Pure-stub mode: no audit witness needed
            return {}
        config = {"configurable": {"thread_id": f"audit-{kwargs.get('rite_id','')}-{kwargs.get('tx_digest','')[:16]}"}}
        try:
            return self.audit_graph().invoke(kwargs, config)
        except Exception:
            # Audit failure should not block primary flow (witness is observational)
            return {}

    # ─── Composite execution (the BPMN happy path) ───────────────────

    def run_rite_lifecycle(
        self,
        *,
        rite_input: dict,
        creditor_enrollments: list[dict],
        debtor_enrollments: list[dict],
        release_inputs: list[dict],
    ) -> RiteLifecycleSnapshot:
        """Drive a rite through the entire BPMN: declare → enroll fan-out → release.

        Releases are processed only if rite ratified. Enrollments and releases are processed
        sequentially in this Python orchestrator (real BPMN engine would parallelize the
        multiInstance loop); ordering is creditors-then-debtors-then-releases.
        """
        rite_id = rite_input["rite_id"]
        snapshot = RiteLifecycleSnapshot(
            rite_id=rite_id, phase="declared", rite_status="declared"
        )

        # Phase 0: declaration + Council ratification
        decl = self.declare_rite(rite_id=rite_id, rite_input=rite_input)
        snapshot.rite_status = decl.get("rite_status", "cancelled")
        if snapshot.rite_status != "active":
            snapshot.phase = "rejected"
            return snapshot
        snapshot.phase = "ratified"

        # Phase 1: enroll fan-out (creditors then debtors)
        snapshot.phase = "enrolling"
        accepted_creditor_dids: set[str] = set()
        for cred in creditor_enrollments:
            r = self.enroll_creditor(rite_id=rite_id, enrollment_input=cred)
            snapshot.creditor_enrollments.append(r)
            if r.get("enrollment_vertex_uri"):
                accepted_creditor_dids.add(cred["creditor_did"])

        eligible_debtor_dids: set[str] = set()
        for deb in debtor_enrollments:
            r = self.enroll_debtor(rite_id=rite_id, enrollment_input=deb)
            snapshot.debtor_enrollments.append(r)
            # debtor_enrollment cell sets pairing_status='paired' AND anchors with anchor=True only when eligible
            if r.get("pairing_status") == "paired":
                # Read back from anchor_bridge to check the eligible flag (defense against pairing-without-eligibility)
                if self.ports.anchor_bridge is not None and hasattr(self.ports.anchor_bridge, "writes"):
                    for w in self.ports.anchor_bridge.writes:
                        if (
                            w.get("collection") == "com.etzhayyim.apps.etzhayyim.yobel.debtorEnrollment"
                            and w["payload"].get("debtor_did") == deb["debtor_did"]
                            and w["payload"].get("rite_id") == rite_id
                            and w["payload"].get("eligible") is True
                        ):
                            eligible_debtor_dids.add(deb["debtor_did"])
                            break

        # Phase 2: releases (BPMN parallelGateway join — only execute for eligible pairs)
        snapshot.phase = "releasing"
        for rel in release_inputs:
            if rel.get("creditor_did") not in accepted_creditor_dids:
                snapshot.releases.append(
                    {
                        "release_vertex_uri": "",
                        "settlement_ok": False,
                        "settlement_error": f"creditor {rel.get('creditor_did')} not accepted (Charter Rider gate)",
                    }
                )
                continue
            if rel.get("debtor_did") not in eligible_debtor_dids:
                snapshot.releases.append(
                    {
                        "release_vertex_uri": "",
                        "settlement_ok": False,
                        "settlement_error": f"debtor {rel.get('debtor_did')} ineligible (DMN gate)",
                    }
                )
                continue
            r = self.record_release(rite_id=rite_id, release_input=rel)
            snapshot.releases.append(r)

        snapshot.phase = "complete"
        return snapshot

    # ─── Operator-facing snapshot ────────────────────────────────────

    def snapshot(self, rite_id: str) -> RiteLifecycleSnapshot:
        """Read-only state lookup. Reconstructs from anchor_bridge writes in stub mode."""
        snap = RiteLifecycleSnapshot(rite_id=rite_id, phase="unknown", rite_status="unknown")
        if self.ports.anchor_bridge is None or not hasattr(self.ports.anchor_bridge, "writes"):
            return snap
        for w in self.ports.anchor_bridge.writes:
            collection = w.get("collection", "")
            if collection.endswith(".rite") and w["payload"].get("rite_id") == rite_id:
                snap.rite_status = w["payload"].get("status", "unknown")
                snap.phase = "ratified" if snap.rite_status == "active" else "rejected"
            elif collection.endswith(".creditorEnrollment") and w["payload"].get("rite_id") == rite_id:
                snap.creditor_enrollments.append(w["payload"])
            elif collection.endswith(".debtorEnrollment") and w["payload"].get("rite_id") == rite_id:
                snap.debtor_enrollments.append(w["payload"])
            elif collection.endswith(".release") and w["payload"].get("rite_id") == rite_id:
                snap.releases.append(w["payload"])
        return snap
