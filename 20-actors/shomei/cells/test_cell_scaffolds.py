"""test_cell_scaffolds.py — every shomei cell .solve() raises at R0 (G11 outward-gated).
ADR-2606072100."""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "methods"))
from _t import expect_raises, run  # noqa: E402

from shomei_challenge import ChallengeCell  # noqa: E402
from shomei_verify_claim import VerifyClaimCell  # noqa: E402
from shomei_aggregate import AggregateCell  # noqa: E402
from shomei_revoke import RevokeCell  # noqa: E402
from shomei_gov_attest import GovAttestCell  # noqa: E402

CELLS = [
    ("shomei_challenge", ChallengeCell),
    ("shomei_verify_claim", VerifyClaimCell),
    ("shomei_aggregate", AggregateCell),
    ("shomei_revoke", RevokeCell),
    ("shomei_gov_attest", GovAttestCell),
]


def _mk(cls):
    def t():
        expect_raises(lambda: cls().solve({}), contains="R0 scaffold")
    return t


def test_gov_attest_mentions_council_gate():
    expect_raises(lambda: GovAttestCell().solve({}), contains="Council-gated")


CASES = [(f"{name}_solve_raises", _mk(cls)) for name, cls in CELLS]
CASES.append(("gov_attest_council_gate", test_gov_attest_mentions_council_gate))

if __name__ == "__main__":
    run("cells", CASES)
