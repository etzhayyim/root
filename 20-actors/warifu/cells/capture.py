"""warifu.capture — full/partial capture of an approved hold.

kotoba-EAVT-native (ADR-2605262130). Substrate injected via SubstratePort. Converts an approved
`auth_hold` into a `capture` entity (full or partial). Zero fee. The `settle` cell performs the
on-chain USDC transfer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .substrate import SubstratePort, UnwiredSubstrate


@dataclass
class CaptureRequest:
    auth_id: str
    amount_usdc: int | None = None  # None -> full remaining authorized amount
    idempotency_key: str = ""


@dataclass
class CaptureResult:
    captured: bool
    capture_id: str | None = None
    amount_usdc: int = 0
    remaining_usdc: int = 0
    fee_usdc: int = 0  # always 0 — 決済手数料ゼロ
    reason: str | None = None
    eavt_facts: list[tuple] = field(default_factory=list)


class CaptureCell:
    def __init__(self, substrate: SubstratePort | None = None):
        self.substrate: SubstratePort = substrate or UnwiredSubstrate()

    def run(self, req: CaptureRequest) -> CaptureResult:
        hold = self.substrate.load_hold(req.auth_id)
        if hold is None:
            return CaptureResult(captured=False, reason="auth_hold not found / not approved")

        remaining = hold["amount_usdc"] - hold.get("captured_usdc", 0)
        if remaining <= 0:
            return CaptureResult(captured=False, reason="hold already fully captured")

        amount = req.amount_usdc if req.amount_usdc is not None else remaining
        if amount <= 0 or amount > remaining:
            return CaptureResult(captured=False, reason="capture exceeds remaining authorized amount")

        capture_id = self.substrate.record_capture(req.auth_id, amount)
        new_remaining = remaining - amount
        facts = [
            (capture_id, "warifu/kind", "capture", capture_id),
            (capture_id, "warifu/auth_id", req.auth_id, capture_id),
            (capture_id, "warifu/amount_usdc", amount, capture_id),
            (capture_id, "warifu/remaining_usdc", new_remaining, capture_id),
            (capture_id, "warifu/fee_usdc", 0, capture_id),
        ]
        self.substrate.write_facts(facts)
        return CaptureResult(
            captured=True, capture_id=capture_id, amount_usdc=amount,
            remaining_usdc=new_remaining, eavt_facts=facts,
        )


def capture(req: CaptureRequest, substrate: SubstratePort | None = None) -> CaptureResult:
    return CaptureCell(substrate).run(req)
