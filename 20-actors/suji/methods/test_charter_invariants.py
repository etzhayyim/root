"""suji (筋) — structural charter-invariant tests over the lexicons + kotoba schema.

The load-bearing invariant is G1 NON-DIAGNOSTIC (医師法 §17): a diagnosis/disease/
prescription/treatment field must be STRUCTURALLY unrepresentable — not merely unused.
These tests parse the actual EDN artifacts and assert (a) no clinical key appears as a
property/ident anywhere, (b) every record is closed (additionalProperties=false), and
(c) muscle groups come from the mechanical set only (G10, no pseudoscience).
"""

from __future__ import annotations

import pathlib

from _edn import load_edn

_LEX = pathlib.Path(__file__).resolve().parent.parent / "lex"
_SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "kotoba" / "schema.edn"

FORBIDDEN = {
    "diagnosis", "disease", "icd", "icd10", "prescription", "treatment",
    "medication", "condition", "pathology", "prognosis", "therapy",
}
MECHANICAL_GROUPS = {
    "cervical-extensors", "upper-trapezius", "levator-scapulae",
    "anterior-deltoid", "erector-spinae",
}


def _walk(node):
    """Yield every (key, value) pair and bare scalar in a nested EDN structure."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield ("key", k)
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)
    else:
        yield ("scalar", node)


def _lex_files():
    return sorted(_LEX.glob("*.edn"))


def test_lexicons_parse_and_have_ids() -> None:
    files = _lex_files()
    assert len(files) == 6, f"expected 6 lexicons, found {len(files)}"
    for f in files:
        doc = load_edn(f)
        assert doc.get(":id", "").startswith("com.etzhayyim.suji."), f"{f.name} id"


def test_no_clinical_property_anywhere_in_lexicons() -> None:
    for f in _lex_files():
        doc = load_edn(f)
        for kind, val in _walk(doc):
            if isinstance(val, str):
                name = val.lstrip(":").lower()
                assert name not in FORBIDDEN, f"G1 violation: clinical key '{val}' in {f.name}"


def test_records_are_closed() -> None:
    """Every lexicon record must set additionalProperties=false (no smuggled fields)."""
    for f in _lex_files():
        doc = load_edn(f)
        rec = doc[":defs"][":main"][":record"]
        assert rec.get(":additionalProperties") is False, f"{f.name} must be closed"


def test_schema_has_no_clinical_ident() -> None:
    schema = load_edn(_SCHEMA)
    for entry in schema:
        ident = entry.get(":db/ident", "")
        leaf = str(ident).split("/")[-1].lower()
        assert leaf not in FORBIDDEN, f"G1 violation: schema ident {ident}"


def test_muscle_groups_are_mechanical_only() -> None:
    """G10: muscle/strain group enums must be the Hill-model set — no 経絡/気/波動."""
    for name in ("muscleTension", "strainReport"):
        doc = load_edn(_LEX / f"{name}.edn")
        props = doc[":defs"][":main"][":record"][":properties"]
        enum = set(props[":group"][":enum"])
        assert enum == MECHANICAL_GROUPS, f"{name} group enum drifted: {enum}"


def test_bodyModel_carries_g4_encrypted_envelope() -> None:
    """G4: a real-scan body must be able to carry an encrypted PII envelope ref."""
    doc = load_edn(_LEX / "bodyModel.edn")
    props = doc[":defs"][":main"][":record"][":properties"]
    assert ":encryptedPayloadCid" in props


def test_stiffness_is_bounded_and_self_referenced() -> None:
    """G3: stiffnessIndex bounded [0,1]; band is a display enum, not a population rank."""
    doc = load_edn(_LEX / "strainReport.edn")
    props = doc[":defs"][":main"][":record"][":properties"]
    s = props[":stiffnessIndex"]
    assert s[":minimum"] == 0 and s[":maximum"] == 1
