"""warifu.authorize — authorize a card transaction (debit hold / credit reserve).

Deterministic settlement logic; no LLM. kotoba-EAVT-native (ADR-2605262130). Substrate access is
injected via `SubstratePort` (cells/substrate.py) — no platform key (ADR-2605231525).

Flow:
    1. enforce payment-purpose allow-list (Phase 1 = SBT<->SBT carve-out only)
    2. resolve card token -> holder ERC-4337 smart account
    3. debit:  balance >= amount -> on-chain hold (escrow lock)
       credit: CreditLine (0%) available -> reserve against wakai float
    4. write EAVT `auth_hold` fact; return approve/decline/gated
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .substrate import SubstratePort, UnwiredSubstrate

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
    eavt_facts: list[tuple] = field(default_factory=list)


class AuthorizeCell:
    """Pregel/LangGraph node. `phase2_enabled` is False until the Lv7+ gate is satisfied."""

    def __init__(self, substrate: SubstratePort | None = None, *, phase2_enabled: bool = False):
        self.substrate: SubstratePort = substrate or UnwiredSubstrate()
        self.phase2_enabled = phase2_enabled

    def _purpose_ok(self, purpose: str) -> Decision | None:
        if purpose in PHASE1_PURPOSES:
            return None
        if purpose in PHASE2_GATED_PURPOSES:
            return None if self.phase2_enabled else Decision.GATED
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

        account = self.substrate.resolve_card(req.card_token)
        if account is None:
            return AuthResult(decision=Decision.DECLINE, reason="card not found")

        if req.funding is Funding.DEBIT:
            ok = self.substrate.usdc_balance(account) >= req.amount_usdc
            note = "debit balance hold"
        else:
            ok = self.substrate.credit_available(account) >= req.amount_usdc  # CreditLine 0%
            note = "credit reserve (0% qard hasan)"
        if not ok:
            return AuthResult(decision=Decision.DECLINE, reason="insufficient funds/credit")

        auth_id = self.substrate.place_hold(
            account, card_token=req.card_token, amount_usdc=req.amount_usdc,
            funding=req.funding.value, purpose=req.purpose, merchant_did=req.merchant_did,
        )
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
        self.substrate.write_facts(facts)
        return AuthResult(decision=Decision.APPROVE, auth_id=auth_id, eavt_facts=facts)


def authorize(req: AuthRequest, substrate: SubstratePort | None = None, *, phase2_enabled: bool = False) -> AuthResult:
    return AuthorizeCell(substrate, phase2_enabled=phase2_enabled).run(req)
