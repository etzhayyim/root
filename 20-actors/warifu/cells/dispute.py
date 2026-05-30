"""warifu.dispute — open/advance a chargeback dispute over a settlement.

R0 scaffold. kotoba-EAVT-native (ADR-2605262130). A dispute is a record (not an automatic
reversal): resolution runs through chigiri 契 (legal procedure) / Council arbitration; any
loss is mutualised by wakai 和会 (ADR-2605263500). Evidence is stored encrypted
(app.etzhayyim.encrypted.*, ADR-2605181100), never plaintext.

Status machine: open -> evidence -> chigiri -> resolved | absorbed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

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
    def run(self, req: DisputeRequest) -> DisputeResult:
        if req.reason_code not in REASON_CODES:
            return DisputeResult(opened=False, reason=f"invalid reason_code '{req.reason_code}'")
        if self._load_settlement(req.settlement_id) is None:  # R0 stub
            return DisputeResult(opened=False, reason="settlement not found")

        dispute_id = self._open(req)  # R0 stub
        facts = [
            (dispute_id, "warifu/kind", "dispute", dispute_id),
            (dispute_id, "warifu/settlement_id", req.settlement_id, dispute_id),
            (dispute_id, "warifu/reason_code", req.reason_code, dispute_id),
            (dispute_id, "warifu/opened_by", req.opened_by_did, dispute_id),
            (dispute_id, "warifu/amount_usdc", req.amount_usdc, dispute_id),
            (dispute_id, "warifu/status", DisputeStatus.OPEN.value, dispute_id),
            # evidence stored as encrypted CIDs only (no plaintext PII)
            *[(dispute_id, "warifu/evidence_cid", cid, dispute_id) for cid in req.evidence_cids],
        ]
        return DisputeResult(
            opened=True, dispute_id=dispute_id, status=DisputeStatus.OPEN, eavt_facts=facts
        )

    # --- substrate edges (R1) ----------------------------------------------------------
    def _load_settlement(self, settlement_id: str) -> dict | None:
        raise NotImplementedError("R0: query kotoba EAVT settlement by settlement_id")

    def _open(self, req: DisputeRequest) -> str:
        raise NotImplementedError("R0: write kotoba EAVT dispute record; route to chigiri")


def dispute(req: DisputeRequest) -> DisputeResult:
    return DisputeCell().run(req)
