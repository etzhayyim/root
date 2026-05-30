"""warifu.settle — capture an authorized hold and settle on-chain (T+0, zero fee).

R0 scaffold. kotoba-EAVT-native (ADR-2605262130).

Flow:
    1. load `auth_hold` fact by auth_id (must be APPROVE, not yet captured)
    2. SettlementRouter transfers USDC holder/wakai-float -> merchant smart account
       - debit:  from holder smart account
       - credit: from wakai float (holder repays later at 0%)
    3. gas sponsored by etzhayyim-paymaster (ERC-4337) <- Public Fund; merchant fee = 0
    4. TitheRouter 10% auto-split applies ONLY to tithe-eligible purposes (not to
       internal-purchase settlement); see purpose handling below
    5. write EAVT `settlement` fact; return settled (final T+0)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Purposes that flow through the 10% TitheRouter auto-split (ADR-2605192115/2605192130).
# A normal internal-purchase settlement to a merchant is NOT a donation and is not tithed here;
# tithe is applied to donation/kisha/grant/tithe streams elsewhere.
TITHE_ELIGIBLE = frozenset({"donation", "kisha", "grant", "tithe"})


@dataclass
class CaptureRequest:
    auth_id: str
    amount_usdc: int | None = None   # None -> full authorized amount
    idempotency_key: str = ""


@dataclass
class SettleResult:
    settled: bool
    settlement_id: str | None = None
    tx: str | None = None
    fee_usdc: int = 0                 # always 0 — 決済手数料ゼロ
    finality: str = "T+0"
    reason: str | None = None
    eavt_facts: list[tuple] = field(default_factory=list)


class SettleCell:
    def run(self, req: CaptureRequest) -> SettleResult:
        hold = self._load_hold(req.auth_id)            # R0 stub
        if hold is None:
            return SettleResult(settled=False, reason="auth_hold not found / not approved")

        amount = req.amount_usdc or hold["amount_usdc"]
        funding = hold["funding"]
        merchant = hold["merchant_did"]

        # On-chain transfer through SettlementRouter (Paymaster-sponsored gas).
        settlement_id, tx = self._settle(
            merchant=merchant, amount=amount, funding=funding, auth_id=req.auth_id
        )

        facts = [
            (settlement_id, "warifu/kind", "settlement", settlement_id),
            (settlement_id, "warifu/auth_id", req.auth_id, settlement_id),
            (settlement_id, "warifu/amount_usdc", amount, settlement_id),
            (settlement_id, "warifu/merchant_did", merchant, settlement_id),
            (settlement_id, "warifu/fee_usdc", 0, settlement_id),     # zero fee invariant
            (settlement_id, "warifu/finality", "T+0", settlement_id),
            (settlement_id, "warifu/tx", tx, settlement_id),
        ]
        return SettleResult(
            settled=True, settlement_id=settlement_id, tx=tx, fee_usdc=0, eavt_facts=facts
        )

    # --- substrate edges (R1) ----------------------------------------------------------
    def _load_hold(self, auth_id: str) -> dict | None:
        raise NotImplementedError("R0: query kotoba EAVT auth_hold by auth_id")

    def _settle(self, *, merchant: str, amount: int, funding: str, auth_id: str) -> tuple[str, str]:
        raise NotImplementedError(
            "R0: emit ERC-4337 UserOp via SettlementRouter.sol (Paymaster gas); return (id, tx)"
        )


def settle(req: CaptureRequest) -> SettleResult:
    return SettleCell().run(req)
