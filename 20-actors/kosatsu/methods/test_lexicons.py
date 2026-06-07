"""test_lexicons.py — 高札 (kosatsu) lexicon well-formedness + NSID parity. ADR-2606072000."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import run

LEXDIR = pathlib.Path(__file__).resolve().parents[1] / "lex"
EXPECTED = ["assertingAuthority", "subjectEntity", "designationNotice",
            "competingClaimView", "delistingEvent", "networkPost"]


def test_all_lexicons_present():
    for name in EXPECTED:
        assert (LEXDIR / f"{name}.edn").exists(), f"missing lexicon {name}"


def test_lexicons_well_formed():
    for name in EXPECTED:
        lx = load_edn(LEXDIR / f"{name}.edn")
        assert lx[":lexicon"] == 1
        assert lx[":id"] == f"com.etzhayyim.kosatsu.{name}"
        rec = lx[":defs"][":main"][":record"]
        assert rec[":type"] == "object"
        assert isinstance(rec[":required"], list) and rec[":required"]
        assert isinstance(rec[":properties"], dict) and rec[":properties"]


def test_required_keys_are_properties():
    for name in EXPECTED:
        lx = load_edn(LEXDIR / f"{name}.edn")
        rec = lx[":defs"][":main"][":record"]
        props = set(rec[":properties"].keys())
        for r in rec[":required"]:
            assert f":{r}" in props, f"{name}: required {r} not in properties"


if __name__ == "__main__":
    run("lexicons", [(k, v) for k, v in sorted(globals().items())
                     if k.startswith("test_") and callable(v)])
