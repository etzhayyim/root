"""warifu 割符 — Open Zero-Fee Card cells (kotoba-EAVT-native).

R0 scaffold. Cells are Pregel/LangGraph-style nodes that read/write the kotoba EAVT ledger
(ADR-2605262130) and emit ERC-4337 UserOperations via @etzhayyim/sdk. No platform-held key
(ADR-2605231525): signing is passkey / smart-account only.

Exposed cells:
    authorize  -- debit hold / credit reserve            -> EAVT `auth_hold`
    capture    -- full/partial capture of an auth_hold    -> EAVT `capture`
    settle     -- on-chain USDC transfer (T+0, fee 0)     -> EAVT `settlement`
    refund     -- reverse a settlement (escrow-refund)    -> EAVT `refund`
    dispute    -- chargeback record -> chigiri procedure  -> EAVT `dispute`
"""

from .substrate import SubstratePort, InMemorySubstrate, UnwiredSubstrate  # noqa: F401
from .eavt_schema import ATTRS as EAVT_ATTRS, validate_facts, assert_valid  # noqa: F401
from .guarded_substrate import GuardedSubstrate  # noqa: F401
from .authorize import AuthorizeCell, authorize  # noqa: F401
from .capture import CaptureCell, capture  # noqa: F401
from .settle import SettleCell, settle  # noqa: F401
from .refund import RefundCell, refund  # noqa: F401
from .dispute import DisputeCell, dispute  # noqa: F401

__all__ = [
    "SubstratePort", "InMemorySubstrate", "UnwiredSubstrate",
    "EAVT_ATTRS", "validate_facts", "assert_valid", "GuardedSubstrate",
    "AuthorizeCell", "authorize",
    "CaptureCell", "capture",
    "SettleCell", "settle",
    "RefundCell", "refund",
    "DisputeCell", "dispute",
]
