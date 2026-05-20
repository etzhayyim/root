#!/usr/bin/env python3
"""
yobel dry-run: drive a fixture rite end-to-end through the BPMN orchestrator with stub ports.

Usage:
    PYTHONPATH=20-actors python3 20-actors/yobel/scripts/dry_run.py \
        --fixture 20-actors/yobel/fixtures/shmita_5786

The dry-run does NOT touch any external system (no Base L2, no MST anchor, no Council
deliberation). All 17 yobel ports are replaced with in-memory Fake* stubs. The output
is a JSON report listing what each cell would have done in production.

Exit code 0 = ran end-to-end (with or without rejections — rejections are expected by design).
Exit code 1 = orchestrator crash / fixture load error.
Exit code 2 = output diverged from expected.json (golden-file mismatch).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make 20-actors importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from langgraph.checkpoint.memory import MemorySaver

from yobel.orchestrator import YobelOrchestrator, YobelPorts
from yobel.ports import Rite


# ─── Lightweight Fake* port wiring (duplicates conftest.py for non-pytest entry) ──


from dataclasses import dataclass, field
from typing import Any
from yobel.ports import (
    AnchorResult, AuditAppendResult, AuditBatchStatus, BaseL2Tx, BatchedAnchorResult,
    DebtRow, EnvelopeCipher, LawfirmInvokeResult, NotificationResult, ProposalDecision,
    ReplicaConsensus, SignedTriple, WitnessKey,
)


@dataclass
class FakeRiteRegistry:
    rites: dict[str, Rite] = field(default_factory=dict)
    def get_rite(self, rite_id): return self.rites.get(rite_id)


@dataclass
class FakeCreditorEnrollment:
    debts_by_debtor: dict[tuple[str, str], list[DebtRow]] = field(default_factory=dict)
    debts_by_debt_id: dict[tuple[str, str, str], DebtRow] = field(default_factory=dict)
    def find_debts_for_debtor(self, rite_id, debtor_did):
        return self.debts_by_debtor.get((rite_id, debtor_did), [])
    def get_debt_for_release(self, rite_id, creditor_did, debt_id, decryptor):
        return self.debts_by_debt_id.get((rite_id, creditor_did, debt_id))


@dataclass
class FakeCouncilSbt:
    levels: dict[str, int] = field(default_factory=dict)
    entity_types: dict[str, str] = field(default_factory=dict)
    def balance_of_level(self, did): return self.levels.get(did, 0)
    def entity_type_of(self, did): return self.entity_types.get(did, "unknown")


@dataclass
class FakeCharterCompliance:
    aligned: set[str] = field(default_factory=set)
    jurisdictions: dict[str, str] = field(default_factory=dict)
    def is_aligned(self, did): return did in self.aligned
    def jurisdiction_of(self, did): return self.jurisdictions.get(did, "ALL")


@dataclass
class FakeErc725:
    valid_signers: set[tuple[str, str]] = field(default_factory=set)
    def verify_eip712_signed_consent(self, signer_did, payload, signature):
        return (signer_did, signature) in self.valid_signers


@dataclass
class FakeEnvelopeCrypto:
    counter: int = 0
    def envelope(self, plaintext, recipients, purpose):
        self.counter += 1
        return EnvelopeCipher(cid=f"ipfs://dryrun-cipher-{purpose}-{self.counter}")


@dataclass
class FakeBaseL2Paymaster:
    next_hash: str = "0xdryrun-tx-hash"
    revert: bool = False
    def release_usdc(self, from_did, to_did, amount_micro_usdc, tithe_neutral, rite_id):
        if self.revert:
            raise RuntimeError("paymaster revert (dry-run)")
        return BaseL2Tx(hash=self.next_hash)


@dataclass
class FakeAnchorBridge:
    writes: list[dict] = field(default_factory=list)
    def write_and_anchor(self, collection, rkey, payload, anchor_to_base_l2=True):
        self.writes.append(dict(collection=collection, rkey=rkey, payload=payload, anchored=anchor_to_base_l2))
        return AnchorResult(vertex_uri=f"at://dryrun/{collection}/{rkey}", anchor_tx_hash=("0xdry-anchor" if anchor_to_base_l2 else ""))
    def batched_anchor(self, contract, cids):
        return BatchedAnchorResult(tx_hash=f"0xdry-batch-{len(cids)}")


@dataclass
class FakeAuditWitnessEmit:
    events: list[dict] = field(default_factory=list)
    def __call__(self, *, event_type, **kw):
        self.events.append({"event_type": event_type, **kw})


@dataclass
class FakeWitnessKeystore:
    def current_key(self): return WitnessKey(id="dryrun-witness-key")
    def sign(self, key_id, payload): return b"\x00" * 32 + payload[:16]


@dataclass
class FakeAuditLog:
    tail: SignedTriple | None = None
    chain_ok: bool = True
    consensus: bool = True
    counter: int = 0
    appended: list[dict] = field(default_factory=list)
    batch: AuditBatchStatus = field(default_factory=lambda: AuditBatchStatus(0, 0, []))
    def tail_signed_triple(self, rite_id): return self.tail
    def verify_chain_link(self, prev_signed_cid, next_state_root_before): return self.chain_ok
    def poll_replica_consensus(self, rite_id, expected_prev_cid):
        return ReplicaConsensus(replicas_agree=self.consensus)
    def append(self, **kwargs):
        self.appended.append(kwargs)
        self.counter += 1
        cid = f"ipfs://dryrun-audit-{self.counter}"
        # Update tail so subsequent witnesses see continuity
        self.tail = SignedTriple(cid=cid)
        return AuditAppendResult(cid=cid, vertex_uri=f"at://dryrun/audit/{self.counter}")
    def batch_status(self): return self.batch
    def mark_anchored(self, cids, tx_hash): pass


@dataclass
class FakeCouncilRatification:
    next_decision: ProposalDecision = field(default_factory=lambda: ProposalDecision(ratified=True, signatures=[f"did:web:council/lv9-chair"] + [f"did:web:council/lv6-{c}" for c in "abc"]))
    proposals: list[dict] = field(default_factory=list)
    def submit_proposal(self, **kw):
        self.proposals.append(kw)
        return f"at://dryrun/proposal/{kw['rite_id']}"
    def await_decision(self, proposal_uri, timeout_days):
        return self.next_decision


@dataclass
class FakePublicFund:
    grants: list[dict] = field(default_factory=list)
    def request_audit_grant(self, reason, rite_id, chain_break_reason):
        self.grants.append({"reason": reason, "rite_id": rite_id})


@dataclass
class FakeCouncilNotifier:
    notifications: list[dict] = field(default_factory=list)
    def notify(self, targets, event_type, rite_id, severity, payload):
        self.notifications.append({"targets": targets, "event_type": event_type})
        return NotificationResult(incident_uri=f"at://dryrun/incident/{rite_id}")


@dataclass
class FakeLawfirmInvoke:
    def __call__(self, method, state):
        return LawfirmInvokeResult(ok=True, invoke_uri=f"at://dryrun/lawfirm/{method}")


@dataclass
class FakeLandRegistry:
    def find_overlapping_tenures(self, scope): return []


# ─── Dry-run driver ──────────────────────────────────────────────────


def load_fixture(fixture_dir: Path) -> dict:
    return {
        "rite": json.loads((fixture_dir / "rite.json").read_text()),
        "creditors": json.loads((fixture_dir / "creditors.json").read_text()),
        "debtors": json.loads((fixture_dir / "debtors.json").read_text()),
        "releases": json.loads((fixture_dir / "releases.json").read_text()),
        "expected": json.loads((fixture_dir / "expected.json").read_text()),
    }


def wire_ports(rite_input: dict, creditor_inputs: list[dict]) -> YobelPorts:
    """Wire the Fake ports based on fixture content (pre-populate SBT levels, community, signed-consent)."""
    ports = YobelPorts()
    ports.rite_registry = FakeRiteRegistry()
    ports.creditor_enrollment = FakeCreditorEnrollment()
    ports.council_sbt = FakeCouncilSbt()
    ports.charter_compliance = FakeCharterCompliance()
    ports.erc725 = FakeErc725()
    ports.envelope_crypto = FakeEnvelopeCrypto()
    ports.base_l2_paymaster = FakeBaseL2Paymaster()
    ports.anchor_bridge = FakeAnchorBridge()
    ports.audit_witness_emit = FakeAuditWitnessEmit()
    ports.witness_keystore = FakeWitnessKeystore()
    ports.audit_log = FakeAuditLog()
    ports.public_fund = FakePublicFund()
    ports.council_notifier = FakeCouncilNotifier()
    ports.council_ratification = FakeCouncilRatification()
    ports.lawfirm_invoke = FakeLawfirmInvoke()
    ports.land_registry = FakeLandRegistry()

    # Pre-register the rite so creditor/debtor cells can load it
    ports.rite_registry.rites[rite_input["rite_id"]] = Rite(
        rite_id=rite_input["rite_id"],
        rite_type=rite_input["rite_type"],
        status="active",
        effective_date=rite_input["effective_date"],
        expiry_date=rite_input.get("expiry_date"),
        scope=rite_input["scope"],
        scope_jurisdictions=["ALL"],
        issuer_did=rite_input["issuer_did"],
        doctrinal_basis=rite_input["doctrinal_basis"],
    )

    # Steward + creditors + community debtors get SBT Lv1+ AND entity_type='natural_person'
    # (legal-person entityType would trigger DMN R14 short-circuit per ADR-2605201800)
    ports.council_sbt.levels[rite_input["issuer_did"]] = 9
    ports.council_sbt.entity_types[rite_input["issuer_did"]] = "natural_person"
    for cred in creditor_inputs:
        ports.council_sbt.levels[cred["creditor_did"]] = 2
        ports.council_sbt.entity_types[cred["creditor_did"]] = "natural_person"
        ports.erc725.valid_signers.add((cred["creditor_did"], cred["signed_consent"]))
        for d in cred["debts"]:
            debtor = d["debtor_did"]
            if debtor.startswith("did:web:etzhayyim.com"):
                # Set SBT for community debtors; one debtor is intentionally not set (debtor-no-sbt)
                ports.council_sbt.levels.setdefault(debtor, 2)
                ports.council_sbt.entity_types.setdefault(debtor, "natural_person")
            elif debtor.startswith("did:web:secular.example"):
                # secular foreigner: no SBT but still a natural person; R3 (community) will reject
                ports.council_sbt.entity_types.setdefault(debtor, "natural_person")
            # Populate creditor-side ledger so cross-check finds them
            row = DebtRow(
                debt_id=d["debt_id"],
                debtor_did=d["debtor_did"],
                principal_micro_usdc=d["principal_micro_usdc"],
                accrued_micro_usdc=d.get("accrued_micro_usdc", 0),
                origination_date=d["origination_date"],
                instrument=d["instrument"],
            )
            key_debtor = (cred["rite_id"], d["debtor_did"])
            ports.creditor_enrollment.debts_by_debtor.setdefault(key_debtor, []).append(row)
            ports.creditor_enrollment.debts_by_debt_id[(cred["rite_id"], cred["creditor_did"], d["debt_id"])] = row

    # debtor-no-sbt must NOT have an SBT entry — explicitly clear if accidentally set
    if "did:web:no-sbt.example:debtor-no-sbt" in ports.council_sbt.levels:
        del ports.council_sbt.levels["did:web:no-sbt.example:debtor-no-sbt"]

    return ports


def main():
    ap = argparse.ArgumentParser(description="yobel dry-run")
    ap.add_argument("--fixture", required=True, type=Path)
    ap.add_argument("--check-golden", action="store_true", help="Compare output against expected.json")
    args = ap.parse_args()

    if not args.fixture.is_dir():
        print(f"fixture dir not found: {args.fixture}", file=sys.stderr)
        return 1

    fx = load_fixture(args.fixture)
    ports = wire_ports(fx["rite"], fx["creditors"])
    orchestrator = YobelOrchestrator(ports=ports, checkpointer=MemorySaver())

    snapshot = orchestrator.run_rite_lifecycle(
        rite_input=fx["rite"],
        creditor_enrollments=fx["creditors"],
        debtor_enrollments=fx["debtors"],
        release_inputs=fx["releases"],
    )

    report = {
        "fixture": args.fixture.name,
        "rite_id": snapshot.rite_id,
        "phase": snapshot.phase,
        "rite_status": snapshot.rite_status,
        "creditor_enrollments": [
            {
                "vertex_uri": e.get("enrollment_vertex_uri", ""),
                "debt_count": e.get("debt_count", 0),
                "accepted": bool(e.get("enrollment_vertex_uri")),
            }
            for e in snapshot.creditor_enrollments
        ],
        "debtor_enrollments": [
            {
                "vertex_uri": e.get("enrollment_vertex_uri", ""),
                "pairing_status": e.get("pairing_status", "unpaired"),
            }
            for e in snapshot.debtor_enrollments
        ],
        "releases": [
            {
                "release_vertex_uri": r.get("release_vertex_uri", ""),
                "settlement_ok": r.get("settlement_ok"),
                "base_l2_tx_hash": r.get("base_l2_tx_hash", ""),
                "settlement_error": r.get("settlement_error", ""),
            }
            for r in snapshot.releases
        ],
        "anchor_writes": len(ports.anchor_bridge.writes),
        "audit_appends": len(ports.audit_log.appended),
        "council_proposals": len(ports.council_ratification.proposals),
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.check_golden:
        expected = fx["expected"]
        ok = True

        # Rite status
        if report["rite_status"] != expected["rite_status"]:
            print(f"GOLDEN MISMATCH: rite_status {report['rite_status']} != {expected['rite_status']}", file=sys.stderr)
            ok = False

        # Successful releases
        actual_successes = sum(1 for r in report["releases"] if r["settlement_ok"])
        expected_successes = expected["summary"]["successful_releases"]
        if actual_successes != expected_successes:
            print(f"GOLDEN MISMATCH: successful_releases {actual_successes} != {expected_successes}", file=sys.stderr)
            ok = False

        if not ok:
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
