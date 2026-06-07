"""test_analyze.py — end-to-end membrane over the representative seed. ADR-2606072100."""
from __future__ import annotations

import tempfile
import pathlib

from _t import run
import analyze


def _results():
    with tempfile.TemporaryDirectory() as d:
        return analyze.run(out_dir=pathlib.Path(d))["results"]


def test_runs_all_members():
    rs = _results()
    assert len(rs) == 4
    by = {r["subjectDid"].split(":")[-1]: r for r in rs}
    assert set(by) == {"demo-aaron", "demo-miriam", "demo-noah", "demo-esther"}


def test_aaron_is_multi_class_pop():
    by = {r["subjectDid"].split(":")[-1]: r for r in _results()}
    aaron = by["demo-aaron"]["credential"]
    # device + key + social + covenant verified → IAL3 covenant-bound, PoP true
    assert aaron["assuranceLevel"] == 3 and aaron["proofOfPersonhood"] is True
    assert aaron["distinctClasses"] >= 3


def test_miriam_two_key_wallets_not_pop():
    by = {r["subjectDid"].split(":")[-1]: r for r in _results()}
    m = by["demo-miriam"]["credential"]
    assert m["factorCount"] == 2 and m["distinctClasses"] == 1
    assert m["proofOfPersonhood"] is False  # two 'key' factors = one class


def test_noah_single_factor_ial1():
    by = {r["subjectDid"].split(":")[-1]: r for r in _results()}
    n = by["demo-noah"]["credential"]
    assert n["assuranceLevel"] == 1 and n["proofOfPersonhood"] is False


def test_esther_gov_factor_gated_not_counted():
    by = {r["subjectDid"].split(":")[-1]: r for r in _results()}
    e = by["demo-esther"]
    # the gov-mynumber possession hit the Council gate → reported gated, NOT verified
    assert any(g["factorKind"] == "gov-mynumber" for g in e["gated"])
    assert "gov-mynumber" not in e["credential"]["verifiedFactors"]
    # without the gov factor she is still covenant-bound (webauthn+sbt+oath)
    assert e["credential"]["assuranceLevel"] == 3


def test_no_pii_or_handles_in_output_credentials():
    # G3: no EXTERNAL identifiers leak into the credential (handles/addresses). The subject's own
    # DID may appear as the self-issued VC issuer; what must never appear are external identifiers.
    for r in _results():
        blob = repr(r["credential"])
        assert "0x" not in blob and "@" not in blob and "bc1q" not in blob
        assert r["credential"]["subjectDidHash"]  # linkage via hash


def test_vc_is_w3c_shaped():
    for r in _results():
        vc = r["vc"]
        assert vc["type"][0] == "VerifiableCredential"
        assert "EtzhayyimPersonhoodCredential" in vc["type"]


CASES = [
    ("runs_all_members", test_runs_all_members),
    ("aaron_multi_class_pop", test_aaron_is_multi_class_pop),
    ("miriam_two_wallets_not_pop", test_miriam_two_key_wallets_not_pop),
    ("noah_single_factor", test_noah_single_factor_ial1),
    ("esther_gov_gated", test_esther_gov_factor_gated_not_counted),
    ("no_pii_in_output", test_no_pii_or_handles_in_output_credentials),
    ("vc_w3c_shaped", test_vc_is_w3c_shaped),
]

if __name__ == "__main__":
    run("analyze", CASES)
