"""
Shared pytest fixtures for yobel cell tests.

Provides fake (stub) implementations of all 17 yobel ports defined in ports.py.
Each fixture is independent; tests compose them as needed.
"""

from __future__ import annotations


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: integration tests requiring anvil + web3.py (deselect with -m 'not integration')",
    )


import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

# Make the yobel package importable when tests are run from repo root.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "20-actors"))

from yobel.ports import (  # noqa: E402
    AnchorResult,
    AuditAppendResult,
    AuditBatchStatus,
    BaseL2Tx,
    BatchedAnchorResult,
    DebtRow,
    EnvelopeCipher,
    LawfirmInvokeResult,
    NotificationResult,
    ProposalDecision,
    ReplicaConsensus,
    Rite,
    SignedTriple,
    WitnessKey,
)


# ─── Fake implementations ────────────────────────────────────────────


@dataclass
class FakeRiteRegistry:
    rites: dict[str, Rite] = field(default_factory=dict)

    def get_rite(self, rite_id: str) -> Rite | None:
        return self.rites.get(rite_id)


@dataclass
class FakeCreditorEnrollment:
    debts_by_debtor: dict[tuple[str, str], list[DebtRow]] = field(default_factory=dict)
    debts_by_debt_id: dict[tuple[str, str, str], DebtRow] = field(default_factory=dict)

    def find_debts_for_debtor(self, rite_id: str, debtor_did: str) -> list[DebtRow]:
        return self.debts_by_debtor.get((rite_id, debtor_did), [])

    def get_debt_for_release(
        self, rite_id: str, creditor_did: str, debt_id: str, decryptor: Any
    ) -> DebtRow | None:
        return self.debts_by_debt_id.get((rite_id, creditor_did, debt_id))


@dataclass
class FakeCouncilSbt:
    levels: dict[str, int] = field(default_factory=dict)
    entity_types: dict[str, str] = field(default_factory=dict)  # DID → 'natural_person' / 'legal_person'

    def balance_of_level(self, did: str) -> int:
        return self.levels.get(did, 0)

    def entity_type_of(self, did: str) -> str:
        return self.entity_types.get(did, "unknown")


@dataclass
class FakeCharterCompliance:
    aligned: set[str] = field(default_factory=set)
    jurisdictions: dict[str, str] = field(default_factory=dict)

    def is_aligned(self, did: str) -> bool:
        return did in self.aligned

    def jurisdiction_of(self, did: str) -> str:
        return self.jurisdictions.get(did, "ALL")


@dataclass
class FakeErc725:
    valid_signers: set[tuple[str, str]] = field(default_factory=set)  # (signer_did, signature)

    def verify_eip712_signed_consent(
        self, signer_did: str, payload: dict, signature: str
    ) -> bool:
        return (signer_did, signature) in self.valid_signers


@dataclass
class FakeEnvelopeCrypto:
    counter: int = 0

    def envelope(self, plaintext: Any, recipients: list[str], purpose: str) -> EnvelopeCipher:
        self.counter += 1
        return EnvelopeCipher(cid=f"ipfs://fake-cipher-{purpose}-{self.counter}")


@dataclass
class FakeBaseL2Paymaster:
    next_hash: str = "0xfake-tx-hash"
    revert: bool = False

    def release_usdc(
        self,
        from_did: str,
        to_did: str,
        amount_micro_usdc: int,
        tithe_neutral: bool,
        rite_id: str,
    ) -> BaseL2Tx:
        if self.revert:
            raise RuntimeError(f"paymaster revert: insufficient vault balance for {from_did}")
        return BaseL2Tx(hash=self.next_hash)


@dataclass
class FakeLawfirmInvoke:
    next_result: LawfirmInvokeResult = field(
        default_factory=lambda: LawfirmInvokeResult(ok=True, invoke_uri="at://fake/lawfirm/result")
    )

    def __call__(self, method: str, state: dict) -> LawfirmInvokeResult:
        return self.next_result


@dataclass
class FakeAnchorBridge:
    writes: list[dict] = field(default_factory=list)

    def write_and_anchor(
        self,
        collection: str,
        rkey: str,
        payload: dict,
        anchor_to_base_l2: bool = True,
    ) -> AnchorResult:
        self.writes.append(
            {"collection": collection, "rkey": rkey, "payload": payload, "anchored": anchor_to_base_l2}
        )
        return AnchorResult(
            vertex_uri=f"at://fake/{collection}/{rkey}",
            anchor_tx_hash=("0xfake-anchor" if anchor_to_base_l2 else ""),
        )

    def batched_anchor(self, contract: str, cids: list[str]) -> BatchedAnchorResult:
        return BatchedAnchorResult(tx_hash=f"0xfake-batch-{len(cids)}")


@dataclass
class FakeAuditWitnessEmit:
    events: list[dict] = field(default_factory=list)

    def __call__(self, *, event_type: str, **kwargs: Any) -> None:
        self.events.append({"event_type": event_type, **kwargs})


@dataclass
class FakeWitnessKeystore:
    def current_key(self) -> WitnessKey:
        return WitnessKey(id="fake-witness-key-001")

    def sign(self, key_id: str, payload: bytes) -> bytes:
        return b"\x00" * 32 + payload[:16]


@dataclass
class FakeAuditLog:
    tail: SignedTriple | None = None
    chain_ok: bool = True
    consensus: bool = True
    batch: AuditBatchStatus = field(
        default_factory=lambda: AuditBatchStatus(event_count=0, seconds_since_last_anchor=0, pending_cids=[])
    )
    appended: list[dict] = field(default_factory=list)
    anchored_marks: list[tuple[list[str], str]] = field(default_factory=list)
    counter: int = 0

    def tail_signed_triple(self, rite_id: str) -> SignedTriple | None:
        return self.tail

    def verify_chain_link(self, prev_signed_cid: str, next_state_root_before: str) -> bool:
        return self.chain_ok

    def poll_replica_consensus(self, rite_id: str, expected_prev_cid: str) -> ReplicaConsensus:
        return ReplicaConsensus(replicas_agree=self.consensus)

    def append(self, **kwargs: Any) -> AuditAppendResult:
        self.appended.append(kwargs)
        self.counter += 1
        return AuditAppendResult(
            cid=f"ipfs://fake-audit-{self.counter}",
            vertex_uri=f"at://fake/audit/{self.counter}",
        )

    def batch_status(self) -> AuditBatchStatus:
        return self.batch

    def mark_anchored(self, cids: list[str], tx_hash: str) -> None:
        self.anchored_marks.append((cids, tx_hash))


@dataclass
class FakePublicFund:
    grants: list[dict] = field(default_factory=list)

    def request_audit_grant(self, reason: str, rite_id: str, chain_break_reason: str) -> None:
        self.grants.append({"reason": reason, "rite_id": rite_id, "chain_break_reason": chain_break_reason})


@dataclass
class FakeCouncilNotifier:
    notifications: list[dict] = field(default_factory=list)

    def notify(
        self,
        targets: list[str],
        event_type: str,
        rite_id: str,
        severity: str,
        payload: dict,
    ) -> NotificationResult:
        self.notifications.append(
            {"targets": targets, "event_type": event_type, "rite_id": rite_id, "severity": severity}
        )
        return NotificationResult(incident_uri=f"at://fake/incident/{rite_id}")


@dataclass
class FakeCouncilRatification:
    next_decision: ProposalDecision = field(
        default_factory=lambda: ProposalDecision(ratified=True, signatures=["did:web:council/lv9-chair"])
    )
    proposals: list[dict] = field(default_factory=list)

    def submit_proposal(self, **kwargs: Any) -> str:
        self.proposals.append(kwargs)
        return f"at://fake/proposal/{kwargs['rite_id']}"

    def await_decision(self, proposal_uri: str, timeout_days: int) -> ProposalDecision:
        return self.next_decision


@dataclass
class FakeLandRegistry:
    overlapping: list[int] = field(default_factory=list)

    def find_overlapping_tenures(self, scope: str) -> list[int]:
        return self.overlapping


# ─── Pytest fixtures ─────────────────────────────────────────────────


@pytest.fixture
def rite_registry() -> FakeRiteRegistry:
    return FakeRiteRegistry()


@pytest.fixture
def creditor_enrollment_port() -> FakeCreditorEnrollment:
    return FakeCreditorEnrollment()


@pytest.fixture
def council_sbt() -> FakeCouncilSbt:
    return FakeCouncilSbt()


@pytest.fixture
def charter_compliance() -> FakeCharterCompliance:
    return FakeCharterCompliance()


@pytest.fixture
def erc725() -> FakeErc725:
    return FakeErc725()


@pytest.fixture
def envelope_crypto() -> FakeEnvelopeCrypto:
    return FakeEnvelopeCrypto()


@pytest.fixture
def base_l2_paymaster() -> FakeBaseL2Paymaster:
    return FakeBaseL2Paymaster()


@pytest.fixture
def lawfirm_invoke() -> FakeLawfirmInvoke:
    return FakeLawfirmInvoke()


@pytest.fixture
def anchor_bridge() -> FakeAnchorBridge:
    return FakeAnchorBridge()


@pytest.fixture
def audit_witness_emit() -> FakeAuditWitnessEmit:
    return FakeAuditWitnessEmit()


@pytest.fixture
def witness_keystore() -> FakeWitnessKeystore:
    return FakeWitnessKeystore()


@pytest.fixture
def audit_log() -> FakeAuditLog:
    return FakeAuditLog()


@pytest.fixture
def public_fund() -> FakePublicFund:
    return FakePublicFund()


@pytest.fixture
def council_notifier() -> FakeCouncilNotifier:
    return FakeCouncilNotifier()


@pytest.fixture
def council_ratification() -> FakeCouncilRatification:
    return FakeCouncilRatification()


@pytest.fixture
def land_registry() -> FakeLandRegistry:
    return FakeLandRegistry()


@pytest.fixture
def checkpointer():
    """In-memory checkpointer for tests (avoids MST anchor side-effects)."""
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
