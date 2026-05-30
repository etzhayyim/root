"""warifu.capture — partial/deferred capture of an authorized hold.

R0 scaffold. kotoba-EAVT-native (ADR-2605262130). Sits between `authorize` (manual
capture_method) and `settle`: it converts an approved `auth_hold` into a `capture` entity
(full or partial), leaving the residual hold for void/expiry. Zero fee.

Flow:
    1. load APPROVE `auth_hold` by auth_id; reject if already fully captured / voided
    2. amount defaults to remaining authorized amount; partial capture allowed (<= remaining)
    3. write EAVT `capture` fact; the `settle` cell performs the on-chain USDC transfer
"""

from __future__ import annotations

from dataclasses import dataclass, field


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
    def run(self, req: CaptureRequest) -> CaptureResult:
        hold = self._load_hold(req.auth_id)  # R0 stub
        if hold is None:
            return CaptureResult(captured=False, reason="auth_hold not found / not approved")

        already = hold.get("captured_usdc", 0)
        remaining = hold["amount_usdc"] - already
        if remaining <= 0:
            return CaptureResult(captured=False, reason="hold already fully captured")

        amount = req.amount_usdc or remaining
        if amount > remaining:
            return CaptureResult(captured=False, reason="capture exceeds remaining authorized amount")

        capture_id = self._record_capture(req.auth_id, amount)  # R0 stub
        new_remaining = remaining - amount
        facts = [
            (capture_id, "warifu/kind", "capture", capture_id),
            (capture_id, "warifu/auth_id", req.auth_id, capture_id),
            (capture_id, "warifu/amount_usdc", amount, capture_id),
            (capture_id, "warifu/remaining_usdc", new_remaining, capture_id),
            (capture_id, "warifu/fee_usdc", 0, capture_id),
        ]
        return CaptureResult(
            captured=True,
            capture_id=capture_id,
            amount_usdc=amount,
            remaining_usdc=new_remaining,
            eavt_facts=facts,
        )

    # --- substrate edges (R1) ----------------------------------------------------------
    def _load_hold(self, auth_id: str) -> dict | None:
        raise NotImplementedError("R0: query kotoba EAVT auth_hold by auth_id")

    def _record_capture(self, auth_id: str, amount: int) -> str:
        raise NotImplementedError("R0: write kotoba EAVT capture entity; return capture_id")


def capture(req: CaptureRequest) -> CaptureResult:
    return CaptureCell().run(req)
