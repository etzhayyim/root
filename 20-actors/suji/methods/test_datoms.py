"""suji (筋) — analyze→kotoba Datom emitter tests (G9 drift-lock + G1)."""

from __future__ import annotations

import pathlib

from _edn import load_edn
from analyze import analyze_all
from datoms import render_edn, results_to_datoms

_SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "kotoba" / "schema.edn"

FORBIDDEN = {
    "diagnosis", "disease", "icd", "icd10", "prescription", "treatment",
    "medication", "condition", "pathology", "prognosis",
}


def _schema_idents() -> set[str]:
    return {e[":db/ident"] for e in load_edn(_SCHEMA) if ":db/ident" in e}


def _datoms():
    return results_to_datoms(analyze_all(session_minutes=120.0))


def test_every_attribute_is_declared_in_schema() -> None:
    """G9 drift-lock: no emitted attribute may be absent from kotoba/schema.edn."""
    declared = _schema_idents()
    for d in _datoms():
        for attr in d:
            assert attr in declared, f"undeclared attribute emitted: {attr}"


def test_no_clinical_attribute_can_be_emitted() -> None:
    """G1: emitted attributes carry no clinical leaf (structurally a force/moment/dose)."""
    for d in _datoms():
        for attr in d:
            leaf = attr.split("/")[-1].lower()
            assert leaf not in FORBIDDEN, f"G1 violation: {attr}"


def test_refs_resolve() -> None:
    datoms = _datoms()
    bodies = {d[":body/id"] for d in datoms if ":body/id" in d}
    postures = {d[":posture/id"] for d in datoms if ":posture/id" in d}
    assert bodies and postures
    for d in datoms:
        if ":posture/body" in d:
            assert d[":posture/body"] in bodies
        for ref in (":load/posture", ":muscle/posture", ":strain/posture"):
            if ref in d:
                assert d[ref] in postures, f"dangling {ref}={d[ref]}"


def test_cervical_load_datom_complete() -> None:
    datoms = _datoms()
    cerv = [d for d in datoms if d.get(":load/joint") == ":cervicothoracic"]
    assert cerv, "expected a cervicothoracic load datom per posture"
    for d in cerv:
        assert ":load/compressive-kgf" in d and ":load/mult-vs-head" in d
        assert d[":load/compressive-kgf"] > 0


def test_endurance_infinity_encoded_as_minus_one() -> None:
    # the eye-level monitor posture is low-load → some muscles have infinite endurance
    strains = [d for d in _datoms() if ":strain/endurance-min" in d]
    assert any(d[":strain/endurance-min"] == -1.0 for d in strains)
    assert all(d[":strain/endurance-min"] == -1.0 or d[":strain/endurance-min"] > 0 for d in strains)


def test_rendered_edn_reparses_to_same_datoms() -> None:
    """The EDN we write must round-trip back through the reader (well-formed seed)."""
    datoms = _datoms()
    text = render_edn(datoms)
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".edn", delete=False) as fh:
        fh.write(text)
        tmp = fh.name
    back = load_edn(pathlib.Path(tmp))
    assert isinstance(back, list) and len(back) == len(datoms)
    # spot-check a known boolean + keyword survived the round-trip
    body = next(d for d in back if ":body/id" in d)
    assert body[":body/representative"] is True
    cerv = next(d for d in back if d.get(":load/joint") == ":cervicothoracic")
    assert cerv[":load/joint"] == ":cervicothoracic"
