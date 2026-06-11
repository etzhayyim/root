"""warifu.dispute — open a chargeback dispute over a settlement.

kotoba-EAVT-native (ADR-2605262130). Substrate injected via SubstratePort. A dispute is a record,
not an auto-reversal: resolution routes through chigiri 契; loss is mutualised by wakai 和会
(ADR-2605263500). Evidence is stored as encrypted CIDs only (com.etzhayyim.encrypted.*,
ADR-2605181100), never plaintext.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .substrate import SubstratePort, UnwiredSubstrate

REASON_CODES = frozenset({"fraud", "not-received", "not-as-described", "duplicate", "other"})


class DisputeStatus(str, Enum):
    OPEN = "open"
    EVIDENCE = "evidence"
    CHIGIRI = "chigiri"
    RESOLVED = "resolved"
    ABSORBED = "absorbed"  # wakai-absorbed loss


@dataclass
class DisputeRequest:
    settlement_id: str
    reason_code: str
    opened_by_did: str
    amount_usdc: int
    evidence_cids: list[str] = field(default_factory=list)  # encrypted blob CIDs only


@dataclass
class DisputeResult:
    opened: bool
    dispute_id: str | None = None
    status: DisputeStatus | None = None
    reason: str | None = None
    eavt_facts: list[tuple] = field(default_factory=list)


class DisputeCell:
    def __init__(self, substrate: SubstratePort | None = None):
        self.substrate: SubstratePort = substrate or UnwiredSubstrate()

    def run(self, req: DisputeRequest) -> DisputeResult:
        if req.reason_code not in REASON_CODES:
            return DisputeResult(opened=False, reason=f"invalid reason_code '{req.reason_code}'")
        if self.substrate.load_settlement(req.settlement_id) is None:
            return DisputeResult(opened=False, reason="settlement not found")

        dispute_id = self.substrate.open_dispute(
            settlement_id=req.settlement_id, reason_code=req.reason_code,
            opened_by_did=req.opened_by_did, amount_usdc=req.amount_usdc,
            evidence_cids=req.evidence_cids,
        )
        facts = [
            (dispute_id, "warifu/kind", "dispute", dispute_id),
            (dispute_id, "warifu/settlement_id", req.settlement_id, dispute_id),
            (dispute_id, "warifu/reason_code", req.reason_code, dispute_id),
            (dispute_id, "warifu/opened_by", req.opened_by_did, dispute_id),
            (dispute_id, "warifu/amount_usdc", req.amount_usdc, dispute_id),
            (dispute_id, "warifu/status", DisputeStatus.OPEN.value, dispute_id),
            *[(dispute_id, "warifu/evidence_cid", cid, dispute_id) for cid in req.evidence_cids],
        ]
        self.substrate.write_facts(facts)
        return DisputeResult(
            opened=True, dispute_id=dispute_id, status=DisputeStatus.OPEN, eavt_facts=facts
        )


def dispute(req: DisputeRequest, substrate: SubstratePort | None = None) -> DisputeResult:
    return DisputeCell(substrate).run(req)
