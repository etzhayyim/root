"""warifu.authorize — authorize a card transaction (debit hold / credit reserve).

R0 scaffold. Deterministic settlement logic; no LLM. kotoba-EAVT-native (ADR-2605262130).

Flow:
    1. resolve card token -> holder ERC-4337 smart account (WarifuCard, soulbound ERC-5192)
    2. enforce payment-purpose allow-list (Phase 1 = SBT<->SBT carve-out only)
    3. debit:  check USDC balance >= amount, place on-chain hold (escrow lock)
       credit: check CreditLine (0% interest) available, reserve against wakai float
    4. write EAVT `auth_hold` fact; return approve/decline (ISO 8583 0110-equiv / REST 200)

This module intentionally raises NotImplementedError at the substrate edges: the actual
on-chain calls go through @etzhayyim/sdk (TS) / the kotoba client. R0 wires the decision logic
and the EAVT shape only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Phase 1 charter-clean purposes (ADR-2605192115 SBT<->SBT carve-out + escrow-refund).
PHASE1_PURPOSES = frozenset(
    {"internal-purchase", "internal-subscription", "internal-promo", "escrow-refund"}
)
# Gated until Council Lv7+ amendment of ADR-2605192115 + vendor merchant-of-record (ADR-2605301036).
PHASE2_GATED_PURPOSES = frozenset({"purchase", "subscription"})


class Funding(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class Decision(str, Enum):
    APPROVE = "approve"   # ISO 8583 RC 00
    DECLINE = "decline"   # ISO 8583 RC 05
    GATED = "gated"       # purpose constitutionally disabled (Phase 2)


@dataclass
class AuthRequest:
    card_token: str            # network token (no raw PAN — self TSP)
    amount_usdc: int           # minor units (6dp USDC)
    funding: Funding
    purpose: str               # must be in the active allow-list
    merchant_did: str          # SBT-bound merchant (Phase 1)
    idempotency_key: str
    surface: str = "rest"      # rest | iso8583 | nfc


@dataclass
class AuthResult:
    decision: Decision
    auth_id: str | None = None
    reason: str | None = None
    eavt_facts: list[tuple] = field(default_factory=list)  # (entity, attr, value, tx) facts


class AuthorizeCell:
    """Pregel/LangGraph node. `phase2_enabled` is False until the Lv7+ gate is satisfied."""

    def __init__(self, *, phase2_enabled: bool = False):
        self.phase2_enabled = phase2_enabled

    def _purpose_ok(self, purpose: str) -> Decision | None:
        if purpose in PHASE1_PURPOSES:
            return None
        if purpose in PHASE2_GATED_PURPOSES and not self.phase2_enabled:
            return Decision.GATED
        if purpose in PHASE2_GATED_PURPOSES and self.phase2_enabled:
            return None
        return Decision.DECLINE  # unknown / prohibited purpose

    def run(self, req: AuthRequest) -> AuthResult:
        gate = self._purpose_ok(req.purpose)
        if gate is not None:
            reason = (
                "purpose constitutionally gated — Phase 2 requires Council Lv7+ amendment "
                "(ADR-2605192115) + vendor merchant-of-record (ADR-2605301036)"
                if gate is Decision.GATED
                else f"purpose '{req.purpose}' not permitted"
            )
            return AuthResult(decision=gate, reason=reason)

        # --- substrate edge (R0 stubs) -------------------------------------------------
        holder_account = self._resolve_card(req.card_token)        # -> smart account addr
        if req.funding is Funding.DEBIT:
            ok = self._has_balance(holder_account, req.amount_usdc)
            note = "debit balance hold"
        else:
            ok = self._has_credit(holder_account, req.amount_usdc)  # CreditLine 0%, wakai float
            note = "credit reserve (0% qard hasan)"
        if not ok:
            return AuthResult(decision=Decision.DECLINE, reason="insufficient funds/credit")

        auth_id = self._place_hold(holder_account, req)             # on-chain escrow lock
        facts = [
            (auth_id, "warifu/kind", "auth_hold", auth_id),
            (auth_id, "warifu/card_token", req.card_token, auth_id),
            (auth_id, "warifu/amount_usdc", req.amount_usdc, auth_id),
            (auth_id, "warifu/funding", req.funding.value, auth_id),
            (auth_id, "warifu/purpose", req.purpose, auth_id),
            (auth_id, "warifu/merchant_did", req.merchant_did, auth_id),
            (auth_id, "warifu/fee_usdc", 0, auth_id),               # 決済手数料ゼロ
            (auth_id, "warifu/note", note, auth_id),
        ]
        return AuthResult(decision=Decision.APPROVE, auth_id=auth_id, eavt_facts=facts)

    # --- substrate edges: implemented via @etzhayyim/sdk + kotoba client in R1 ----------
    def _resolve_card(self, card_token: str) -> str:
        raise NotImplementedError("R0: resolve WarifuCard token -> ERC-4337 smart account")

    def _has_balance(self, account: str, amount: int) -> bool:
        raise NotImplementedError("R0: query USDC balance on Base L2 via SDK")

    def _has_credit(self, account: str, amount: int) -> bool:
        raise NotImplementedError("R0: query CreditLine.sol available (0%) + wakai float")

    def _place_hold(self, account: str, req: AuthRequest) -> str:
        raise NotImplementedError("R0: emit ERC-4337 UserOp escrow lock; return auth_id")


def authorize(req: AuthRequest, *, phase2_enabled: bool = False) -> AuthResult:
    return AuthorizeCell(phase2_enabled=phase2_enabled).run(req)
