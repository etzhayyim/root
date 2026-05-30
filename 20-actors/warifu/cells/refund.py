"""warifu.refund — reverse a settled transaction (purpose always escrow-refund).

R0 scaffold. kotoba-EAVT-native (ADR-2605262130). Reverses USDC from merchant back to the
holder (debit) or back to the wakai float with a CreditLine repay (credit). Zero fee; refunds
never net the holder less than the captured amount.

Flow:
    1. load `settlement` by settlement_id; compute refundable = amount - already_refunded
    2. amount defaults to full refundable; partial allowed (<= refundable)
    3. SettlementRouter reverse transfer; for credit, also CreditLine.repay(holder, amount)
    4. write EAVT `refund` fact (purpose escrow-refund)
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
    def run(self, req: RefundRequest) -> RefundResult:
        s = self._load_settlement(req.settlement_id)  # R0 stub
        if s is None:
            return RefundResult(refunded=False, reason="settlement not found")

        refundable = s["amount_usdc"] - s.get("refunded_usdc", 0)
        if refundable <= 0:
            return RefundResult(refunded=False, reason="already fully refunded")

        amount = req.amount_usdc or refundable
        if amount > refundable:
            return RefundResult(refunded=False, reason="refund exceeds refundable amount")

        refund_id, tx = self._reverse(s, amount)  # R0 stub: SettlementRouter + (credit) repay
        facts = [
            (refund_id, "warifu/kind", "refund", refund_id),
            (refund_id, "warifu/settlement_id", req.settlement_id, refund_id),
            (refund_id, "warifu/amount_usdc", amount, refund_id),
            (refund_id, "warifu/purpose", REFUND_PURPOSE, refund_id),
            (refund_id, "warifu/fee_usdc", 0, refund_id),
            (refund_id, "warifu/tx", tx, refund_id),
        ]
        return RefundResult(
            refunded=True, refund_id=refund_id, amount_usdc=amount, tx=tx, eavt_facts=facts
        )

    # --- substrate edges (R1) ----------------------------------------------------------
    def _load_settlement(self, settlement_id: str) -> dict | None:
        raise NotImplementedError("R0: query kotoba EAVT settlement by settlement_id")

    def _reverse(self, settlement: dict, amount: int) -> tuple[str, str]:
        raise NotImplementedError(
            "R0: SettlementRouter reverse transfer (+ CreditLine.repay for credit); return (id, tx)"
        )


def refund(req: RefundRequest) -> RefundResult:
    return RefundCell().run(req)
