"""GuardedSubstrate — schema-enforcing decorator for any SubstratePort (ADR-2605302000).

The production write path. Wraps a backing `SubstratePort` (InMemorySubstrate for dev; a real
`@etzhayyim/sdk` + kotoba client in prod) and runs `eavt_schema.assert_valid()` on EVERY
`write_facts` before delegating — so malformed or fee-leaking datoms can never reach the kotoba
QuadStore (ADR-2605262130). All other operations (reads / holds / ERC-4337 settlement UserOps)
pass through unchanged. No platform key is introduced (ADR-2605231525): the guard is pure
validation; signing stays in the backend's chain client.

Usage:
    substrate = GuardedSubstrate(InMemorySubstrate())     # dev
    substrate = GuardedSubstrate(kotoba_sdk_client)       # prod (same cells, no changes)
"""

from __future__ import annotations

from .eavt_schema import assert_valid


class GuardedSubstrate:
    def __init__(self, backend):
        # bypass __getattr__ for our own attribute
        object.__setattr__(self, "backend", backend)

    def write_facts(self, facts) -> None:
        assert_valid(facts)            # kotoba write contract — fail-closed before persist
        self.backend.write_facts(facts)

    # Everything else (resolve_card, usdc_balance, credit_available, place_hold, load_hold,
    # record_capture, settle_transfer, load_settlement, reverse_settlement, open_dispute, …)
    # delegates to the backing port unchanged.
    def __getattr__(self, name):
        return getattr(self.backend, name)
