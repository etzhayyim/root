"""test_lexicons.py — 系図 (keizu) lexicon well-formedness. ADR-2606066000."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import run

LEXDIR = pathlib.Path(__file__).resolve().parents[1] / "lex"
LEXES = ("relationEdge", "committeeComposition", "moneyFlowObservation", "networkPost")


def test_all_four_present():
    for name in LEXES:
        assert (LEXDIR / f"{name}.edn").exists(), name


def test_ids_namespaced():
    for name in LEXES:
        lx = load_edn(LEXDIR / f"{name}.edn")
        assert lx[":id"].startswith("com.etzhayyim.keizu."), lx[":id"]
        assert lx[":id"].endswith(name)


def test_each_is_a_record():
    for name in LEXES:
        lx = load_edn(LEXDIR / f"{name}.edn")
        main = lx[":defs"][":main"]
        assert main[":type"] == "record"
        assert ":record" in main and ":properties" in main[":record"]


def test_required_fields_exist_in_properties():
    for name in LEXES:
        lx = load_edn(LEXDIR / f"{name}.edn")
        rec = lx[":defs"][":main"][":record"]
        props = set(rec[":properties"].keys())
        for req in rec.get(":required", []):
            assert (":" + req) in props, f"{name}: required {req} missing from properties"


def test_committee_members_min_one():
    lx = load_edn(LEXDIR / "committeeComposition.edn")
    members = lx[":defs"][":main"][":record"][":properties"][":members"]
    assert members[":minLength"] == 1


if __name__ == "__main__":
    run("lexicons", [(k, v) for k, v in sorted(globals().items())
                     if k.startswith("test_") and callable(v)])
