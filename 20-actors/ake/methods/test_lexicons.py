#!/usr/bin/env python3
"""Well-formedness + SSoT-consistency tests for the 朱 (ake) lexicons and ontology."""
from __future__ import annotations

import pathlib

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_LEX = _ROOT / "lex"
_ONTOLOGY = _ROOT.parents[1] / "00-contracts" / "schemas" / "community-edit-ontology.kotoba.edn"

_LEXICONS = [
    "editProposal", "editTriage", "editReview", "editPromotion", "revisionEntry", "councilEditReview",
]


def test_all_lexicons_parse_and_are_namespaced():
    for name in _LEXICONS:
        d = load_edn(_LEX / f"{name}.edn")
        assert d[":id"].startswith("com.etzhayyim.ake.")
        rec = d[":defs"][":main"][":record"]
        assert rec[":type"] == "object"
        assert isinstance(rec[":properties"], dict) and rec[":properties"]


def test_required_fields_are_declared_properties():
    for name in _LEXICONS:
        d = load_edn(_LEX / f"{name}.edn")
        rec = d[":defs"][":main"][":record"]
        props = {k.lstrip(":") for k in rec[":properties"]}
        for req in rec.get(":required", []):
            assert req in props, f"{name}: required {req!r} not a declared property"


def test_lexicon_count_matches_manifest_intent():
    # 6 lexicons = 5 cell-emitted + 1 Council attestation
    assert len(_LEXICONS) == 6


def test_ontology_parses_with_closed_vocab():
    o = load_edn(_ONTOLOGY)
    assert o[":ontology/id"] == "com.etzhayyim.ake.community-edit"
    for key in (":ontology/target-kinds", ":ontology/edit-ops", ":ontology/author-kinds",
                ":ontology/triage-risks", ":ontology/triage-routes", ":ontology/sourcing-grades"):
        assert isinstance(o[key], list) and o[key]


def test_sourcing_grades_are_representative_then_authoritative():
    assert load_edn(_ONTOLOGY)[":ontology/sourcing-grades"] == [":representative", ":authoritative"]


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_lexicons.py")
    sys.exit(1 if failed else 0)
