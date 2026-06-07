"""shomei_challenge — issue a single-use verificationChallenge nonce. R0 scaffold. ADR-2606072100.

Live issuance (writing a com.etzhayyim.shomei.verificationChallenge to the kotoba Datom log) is
outward-gated (G11): the cell .solve() raises at R0. The offline nonce/binding logic is exercised
by methods/ (analyze + tests). G7: the server only issues + records consumption, never signs.
"""
from __future__ import annotations

from typing import Any


class ChallengeCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "shomei R0 scaffold: shomei_challenge issues nonces offline only; live issuance to the "
            "kotoba Datom log is outward-gated (G11). See methods/verify.py for the binding policy."
        )
