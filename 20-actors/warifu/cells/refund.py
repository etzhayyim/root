"""warifu.refund — reverse a settled transaction (purpose always escrow-refund).

kotoba-EAVT-native (ADR-2605262130). Substrate injected via SubstratePort. Reverses USDC from
merchant back to holder (debit) or repays the 0% CreditLine (credit). Zero fee.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .substrate import SubstratePort, UnwiredSubstrate

REFUND_PURPOSE = "escrow-refund"  # the only permitted refund purpose


@dataclass
class RefundRequest:
    settlement_id: str
    amount_usdc: int | None = None  # None -> full refundable
    idempotency_key: str = ""
    reason: str | None = None


@dataclass
class RefundResult:
    refunded: bool
    refund_id: str | None = None
    amount_usdc: int = 0
    tx: str | None = None
    fee_usdc: int = 0  # always 0
    reason: str | None = None
    eavt_facts: list[tuple] = field(default_factory=list)


class RefundCell:
    def __init__(self, substrate: SubstratePort | None = None):
        self.substrate: SubstratePort = substrate or UnwiredSubstrate()

    def run(self, req: RefundRequest) -> RefundResult:
        s = self.substrate.load_settlement(req.settlement_id)
        if s is None:
            return RefundResult(refunded=False, reason="settlement not found")

        refundable = s["amount_usdc"] - s.get("refunded_usdc", 0)
        if refundable <= 0:
            return RefundResult(refunded=False, reason="already fully refunded")

        amount = req.amount_usdc if req.amount_usdc is not None else refundable
        if amount <= 0 or amount > refundable:
            return RefundResult(refunded=False, reason="refund exceeds refundable amount")

        refund_id, tx = self.substrate.reverse_settlement(req.settlement_id, amount)
        facts = [
            (refund_id, "warifu/kind", "refund", refund_id),
            (refund_id, "warifu/settlement_id", req.settlement_id, refund_id),
            (refund_id, "warifu/amount_usdc", amount, refund_id),
            (refund_id, "warifu/purpose", REFUND_PURPOSE, refund_id),
            (refund_id, "warifu/fee_usdc", 0, refund_id),
            (refund_id, "warifu/tx", tx, refund_id),
        ]
        self.substrate.write_facts(facts)
        return RefundResult(
            refunded=True, refund_id=refund_id, amount_usdc=amount, tx=tx, eavt_facts=facts
        )


def refund(req: RefundRequest, substrate: SubstratePort | None = None) -> RefundResult:
    return RefundCell(substrate).run(req)
