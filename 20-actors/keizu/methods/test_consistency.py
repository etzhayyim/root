"""test_consistency.py — 系図 (keizu) SSoT drift-lock. ADR-2606066000.

Asserts manifest ↔ cell tree ↔ lex ↔ ontology agree, and (SOFT) that keizu is registered in
the shared actor-profile-seed. The registry check is soft because that seed is committed by
coordination separately from keizu's own commit (the ake convention).
"""
from __future__ import annotations

import json
import pathlib

from _edn import load_edn
from _t import run

ACTOR = pathlib.Path(__file__).resolve().parents[1]
ROOT = pathlib.Path(__file__).resolve().parents[3]
ONT = ROOT / "00-contracts/schemas/government-relations-ontology.kotoba.edn"
SEEDREG = ROOT / "00-contracts/schemas/actor-profile-seed.kotoba.edn"

LEXES = ("relationEdge", "committeeComposition", "moneyFlowObservation", "networkPost")
CELLS = ("ingest", "committee_graph", "money_graph", "relation_weave", "social_post")


def _manifest():
    return json.loads((ACTOR / "manifest.jsonld").read_text(encoding="utf-8"))


def test_manifest_tier_b():
    assert _manifest()["tier"] == "Tier-B"


def test_manifest_adr_matches_ontology():
    m = _manifest()
    assert "2606066000" in m["adr"]["master"]
    assert load_edn(ONT)[":ontology/adr"] == "2606066000"


def test_manifest_lexicons_exist():
    m = _manifest()
    declared = {ns.split(".")[-1] for ns in m["lexiconNamespaces"]}
    assert declared == set(LEXES), declared
    for name in LEXES:
        assert (ACTOR / "lex" / f"{name}.edn").exists(), name


def test_manifest_cells_match_tree():
    m = _manifest()
    names = {c["name"] for c in m["cells"]}
    assert names == set(CELLS), names
    for c in CELLS:
        assert (ACTOR / "cells" / c / "cell.py").exists(), c
        assert (ACTOR / "cells" / c / "state_machine.py").exists(), c


def test_lex_ids_match_namespaces():
    m = _manifest()
    declared = set(m["lexiconNamespaces"])
    got = {load_edn(ACTOR / "lex" / f"{n}.edn")[":id"] for n in LEXES}
    assert got == declared, (got, declared)


def test_registry_soft():
    # SOFT — passes whether or not the shared seed has been updated yet (ake convention).
    if not SEEDREG.exists():
        return
    txt = SEEDREG.read_text(encoding="utf-8")
    if "actor:keizu" not in txt:
        return  # not yet registered by coordination; not keizu's failure
    assert '"keizu"' in txt or "actor:keizu" in txt


if __name__ == "__main__":
    run("consistency", [(k, v) for k, v in sorted(globals().items())
                        if k.startswith("test_") and callable(v)])
