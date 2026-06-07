"""shomei_verify_claim — verify a subject-signed identityClaim. R0 scaffold. ADR-2606072100.

Wires proofKind → kotoba-auth (eth/btc/cacao + Ed25519) per methods/verify.py PROOF_ROUTING.
Live verification against the real kotoba-auth surface + writing the verified claim to the kotoba
Datom log is outward-gated (G11); the cell .solve() raises at R0. The verification POLICY (challenge
binding, single-use nonce, gov gate, subject-sig) is fully implemented + tested in methods/verify.py.
"""
from __future__ import annotations

from typing import Any


class VerifyClaimCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "shomei R0 scaffold: shomei_verify_claim runs the verification policy offline "
            "(methods/verify.py); live kotoba-auth verification + Datom write is outward-gated (G11)."
        )
