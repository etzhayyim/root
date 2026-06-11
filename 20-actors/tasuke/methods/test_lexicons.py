#!/usr/bin/env python3
"""Well-formedness + SSoT-consistency tests for the 助 (tasuke) lexicons and ontology."""
from __future__ import annotations

import pathlib

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_LEX = _ROOT / "lex"
_ONTOLOGY = _ROOT.parents[1] / "00-contracts" / "schemas" / "cybercrime-victim-support-ontology.kotoba.edn"

_LEXICONS = ["victimIntake", "evidenceItem", "policeReportDraft", "platformRequest",
             "recoveryPlan", "supportCase"]


def test_all_lexicons_parse_and_are_namespaced():
    for name in _LEXICONS:
        d = load_edn(_LEX / f"{name}.edn")
        assert d[":id"].startswith("com.etzhayyim.tasuke.")
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


def test_lexicon_count_is_six():
    assert len(_LEXICONS) == 6


def test_ontology_parses_with_closed_vocab():
    o = load_edn(_ONTOLOGY)
    assert o[":ontology/id"] == "com.etzhayyim.tasuke.cybercrime-victim-support"
    for key in (":ontology/scam-kinds", ":ontology/doc-kinds", ":ontology/doc-authors",
                ":ontology/support-roles", ":ontology/referral-windows", ":ontology/evidence-kinds"):
        assert isinstance(o[key], list) and o[key]


def test_ontology_sourcing_grades_present():
    o = load_edn(_ONTOLOGY)
    # registry rows carry :representative / :authoritative grading
    idents = {m.get(":db/ident") for m in o[":schema"] if isinstance(m, dict)}
    assert ":registry/sourcing" in idents


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
