"""
Port Protocols for yobel cells.

Per ADR-2605201800. These Protocols define the minimal interface surface that
yobel cells call into. Concrete implementations live in kotodama / etzhayyim-sdk;
this file is the single source of truth for "what does a yobel cell require from
its environment". Tests, the BPMN orchestrator, and dry-run scripts mock these
protocols.

Naming convention: <Concept>Port. Callable ports are typed as Protocols with
`__call__` rather than `Callable[...]` so test mocks can be tagged by isinstance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable


# ─── Dataclasses (return types) ──────────────────────────────────────


@dataclass(frozen=True)
class Rite:
    rite_id: str
    rite_type: Literal["shmita_7yr", "yobel_50yr", "tokusei_rei", "religious_jubilee", "political_amnesty"]
    status: Literal["declared", "active", "completed", "cancelled", "superseded"]
    effective_date: str
    expiry_date: str | None
    scope: str
    scope_jurisdictions: list[str]
    issuer_did: str
    doctrinal_basis: str


@dataclass(frozen=True)
class DebtRow:
    debt_id: str
    debtor_did: str
    principal_micro_usdc: int
    accrued_micro_usdc: int
    origination_date: str
    instrument: str


@dataclass(frozen=True)
class AnchorResult:
    vertex_uri: str
    anchor_tx_hash: str


@dataclass(frozen=True)
class ProposalDecision:
    ratified: bool
    signatures: list[str]


@dataclass(frozen=True)
class BaseL2Tx:
    hash: str


@dataclass(frozen=True)
class LawfirmInvokeResult:
    ok: bool
    invoke_uri: str


@dataclass(frozen=True)
class SignedTriple:
    cid: str


@dataclass(frozen=True)
class AuditAppendResult:
    cid: str
    vertex_uri: str


@dataclass(frozen=True)
class AuditBatchStatus:
    event_count: int
    seconds_since_last_anchor: int
    pending_cids: list[str]


@dataclass(frozen=True)
class ReplicaConsensus:
    replicas_agree: bool


@dataclass(frozen=True)
class BatchedAnchorResult:
    tx_hash: str


@dataclass(frozen=True)
class WitnessKey:
    id: str


@dataclass(frozen=True)
class NotificationResult:
    incident_uri: str


@dataclass(frozen=True)
class EnvelopeCipher:
    cid: str


# ─── Port Protocols ──────────────────────────────────────────────────


@runtime_checkable
class RiteRegistryPort(Protocol):
    def get_rite(self, rite_id: str) -> Rite | None: ...


@runtime_checkable
class CreditorEnrollmentPort(Protocol):
    def find_debts_for_debtor(self, rite_id: str, debtor_did: str) -> list[DebtRow]: ...
    def get_debt_for_release(
        self, rite_id: str, creditor_did: str, debt_id: str, decryptor: Any
    ) -> DebtRow | None: ...


@runtime_checkable
class CouncilSbtPort(Protocol):
    def balance_of_level(self, did: str) -> int: ...
    def entity_type_of(self, did: str) -> str:
        """Return the SBT entityType claim: 'natural_person' / 'legal_person' / 'unknown'.

        Per ADR-2605201800: yobel debtor_enrollment DMN R14 short-circuits to ineligible if this
        is not 'natural_person'. Implementations resolve from on-chain CouncilSBT metadata.
        """
        ...


@runtime_checkable
class CharterCompliancePort(Protocol):
    def is_aligned(self, did: str) -> bool: ...
    def jurisdiction_of(self, did: str) -> str: ...


@runtime_checkable
class Erc725Port(Protocol):
    def verify_eip712_signed_consent(
        self, signer_did: str, payload: dict, signature: str
    ) -> bool: ...


@runtime_checkable
class EnvelopeCryptoPort(Protocol):
    def envelope(self, plaintext: Any, recipients: list[str], purpose: str) -> EnvelopeCipher: ...


@runtime_checkable
class TitheRouterPort(Protocol):
    def route(
        self, from_did: str, to_did: str, amount_micro_usdc: int, tithe_rate: int
    ) -> BaseL2Tx: ...


@runtime_checkable
class BaseL2PaymasterPort(Protocol):
    def release_usdc(
        self,
        from_did: str,
        to_did: str,
        amount_micro_usdc: int,
        tithe_neutral: bool,
        rite_id: str,
    ) -> BaseL2Tx: ...


@runtime_checkable
class LawfirmInvokePort(Protocol):
    def __call__(self, method: str, state: dict) -> LawfirmInvokeResult: ...


@runtime_checkable
class AnchorBridgePort(Protocol):
    def write_and_anchor(
        self,
        collection: str,
        rkey: str,
        payload: dict,
        anchor_to_base_l2: bool = True,
    ) -> AnchorResult: ...

    def batched_anchor(self, contract: str, cids: list[str]) -> BatchedAnchorResult: ...


@runtime_checkable
class AuditWitnessEmitPort(Protocol):
    def __call__(self, *, event_type: str, **kwargs: Any) -> None: ...


@runtime_checkable
class WitnessKeystorePort(Protocol):
    def current_key(self) -> WitnessKey: ...
    def sign(self, key_id: str, payload: bytes) -> bytes: ...


@runtime_checkable
class AuditLogPort(Protocol):
    def tail_signed_triple(self, rite_id: str) -> SignedTriple | None: ...
    def verify_chain_link(
        self, prev_signed_cid: str, next_state_root_before: str
    ) -> bool: ...
    def poll_replica_consensus(
        self, rite_id: str, expected_prev_cid: str
    ) -> ReplicaConsensus: ...
    def append(
        self,
        *,
        rite_id: str,
        source_kind: str,
        prev_cid: str,
        state_root_before: str,
        state_root_after: str,
        tx_digest: str,
        witness_key_id: str,
        signature_hex: str,
        event_payload: dict,
    ) -> AuditAppendResult: ...
    def batch_status(self) -> AuditBatchStatus: ...
    def mark_anchored(self, cids: list[str], tx_hash: str) -> None: ...


@runtime_checkable
class PublicFundPort(Protocol):
    def request_audit_grant(
        self, reason: str, rite_id: str, chain_break_reason: str
    ) -> None: ...


@runtime_checkable
class CouncilNotifierPort(Protocol):
    def notify(
        self,
        targets: list[str],
        event_type: str,
        rite_id: str,
        severity: str,
        payload: dict,
    ) -> NotificationResult: ...


@runtime_checkable
class CouncilRatificationPort(Protocol):
    def submit_proposal(
        self,
        topic: str,
        rite_id: str,
        rite_type: str,
        required_lv6_plus_count: int,
        required_lv9_chair_count: int,
        required_quorum_pct: int,
        additional_gates: list[str],
        doctrinal_basis: str,
        scope: str,
    ) -> str: ...

    def await_decision(self, proposal_uri: str, timeout_days: int) -> ProposalDecision: ...


@runtime_checkable
class LandRegistryPort(Protocol):
    def find_overlapping_tenures(self, scope: str) -> list[int]: ...
