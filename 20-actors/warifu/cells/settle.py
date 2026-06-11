"""warifu.settle — capture an authorized hold and settle on-chain (T+0, zero fee).

kotoba-EAVT-native (ADR-2605262130). Substrate injected via SubstratePort.

Flow:
    1. load `auth_hold` by auth_id (must exist / approved)
    2. SettlementRouter transfers USDC holder/wakai-float -> merchant smart account
    3. gas sponsored by etzhayyim-paymaster; merchant fee = 0
    4. write EAVT `settlement` fact; return settled (T+0 final)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .substrate import SubstratePort, UnwiredSubstrate

# Purposes that flow through the 10% TitheRouter auto-split (donation streams, not merchant sales).
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
    def __init__(self, substrate: SubstratePort | None = None):
        self.substrate: SubstratePort = substrate or UnwiredSubstrate()

    def run(self, req: CaptureRequest) -> SettleResult:
        hold = self.substrate.load_hold(req.auth_id)
        if hold is None:
            return SettleResult(settled=False, reason="auth_hold not found / not approved")

        remaining = hold["amount_usdc"] - hold.get("captured_usdc", 0)
        amount = req.amount_usdc if req.amount_usdc is not None else remaining
        if amount <= 0 or amount > remaining:
            return SettleResult(settled=False, reason="amount exceeds remaining authorized amount")

        settlement_id, tx = self.substrate.settle_transfer(
            merchant_did=hold["merchant_did"], amount_usdc=amount,
            funding=hold["funding"], auth_id=req.auth_id,
        )
        facts = [
            (settlement_id, "warifu/kind", "settlement", settlement_id),
            (settlement_id, "warifu/auth_id", req.auth_id, settlement_id),
            (settlement_id, "warifu/amount_usdc", amount, settlement_id),
            (settlement_id, "warifu/merchant_did", hold["merchant_did"], settlement_id),
            (settlement_id, "warifu/fee_usdc", 0, settlement_id),     # zero fee invariant
            (settlement_id, "warifu/finality", "T+0", settlement_id),
            (settlement_id, "warifu/tx", tx, settlement_id),
        ]
        self.substrate.write_facts(facts)
        return SettleResult(
            settled=True, settlement_id=settlement_id, tx=tx, fee_usdc=0, eavt_facts=facts
        )


def settle(req: CaptureRequest, substrate: SubstratePort | None = None) -> SettleResult:
    return SettleCell(substrate).run(req)
