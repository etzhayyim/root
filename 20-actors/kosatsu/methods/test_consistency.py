"""test_consistency.py — 高札 (kosatsu) seed/ontology consistency + integrity. ADR-2606072000."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import run
from weave import check_integrity, weave

ROOT = pathlib.Path(__file__).resolve().parents[3]
ONT = ROOT / "00-contracts/schemas/crime-sanctions-ontology.kotoba.edn"
SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-designation-graph.kotoba.edn"


def test_seed_no_dangling_refs():
    g = weave(load_edn(SEED))
    assert check_integrity(g)["dangling_count"] == 0


def test_seed_subject_kinds_in_ontology():
    ont = load_edn(ONT)
    kinds = {k.lstrip(":") for k in ont[":ontology/subject-kinds"]}
    for s in load_edn(SEED)[":subjects"]:
        assert s[":subject/kind"].lstrip(":") in kinds


def test_seed_authority_kinds_in_ontology():
    ont = load_edn(ONT)
    kinds = {k.lstrip(":") for k in ont[":ontology/authority-kinds"]}
    for a in load_edn(SEED)[":authorities"]:
        assert a[":authority/kind"].lstrip(":") in kinds


def test_every_designation_resolves():
    g = weave(load_edn(SEED))
    auth, subj = set(g["authorities"]), set(g["subjects"])
    for d in g["designations"]:
        assert d[":designation/asserter"] in auth
        assert d[":designation/subject"] in subj


def test_every_subject_has_a_designation():
    g = weave(load_edn(SEED))
    designated = {d[":designation/subject"] for d in g["designations"]}
    for sid in g["subjects"]:
        assert sid in designated, f"subject {sid} has no designation (G5: subjects exist only as targets)"


if __name__ == "__main__":
    run("consistency", [(k, v) for k, v in sorted(globals().items())
                        if k.startswith("test_") and callable(v)])
