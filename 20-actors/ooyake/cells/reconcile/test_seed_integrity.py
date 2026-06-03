"""Tests for ooyake's registry integrity guard (scripts/check_seed_integrity.py).

Proves the guard (a) passes on the committed registry and (b) actually FIRES on the
class of bug it exists to catch — the 2026-06-03 QID-fabrication finding (duplicate
QIDs, malformed QIDs, missing G5 provenance, circular authority 'verification').

Run: python3 -m pytest 20-actors/ooyake/cells/reconcile/test_seed_integrity.py
 or: python3 20-actors/ooyake/cells/reconcile/test_seed_integrity.py
"""
from __future__ import annotations

import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(_HERE, "..", "..", "scripts")))
from check_seed_integrity import check  # noqa: E402


def test_committed_registry_is_clean():
    assert check() == []


def _write(tmp: str, name: str, body: str) -> str:
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


_GOOD_UNIT = (
    '{:gov.unit/id "gov.x" :gov.unit/wikidata "Q1" '
    ':gov.unit/official-url "https://x/" :gov.unit/sourcing :representative '
    ':gov.unit/provenance "https://x/" :gov.unit/last-verified "2026-06-03"}'
)


def test_duplicate_qid_fires():
    with tempfile.TemporaryDirectory() as tmp:
        seed = _write(
            tmp,
            "s.edn",
            '{:units [' + _GOOD_UNIT + ' '
            '{:gov.unit/id "gov.y" :gov.unit/wikidata "Q1" '  # <- same QID as gov.x
            ':gov.unit/official-url "https://y/" :gov.unit/sourcing :representative '
            ':gov.unit/provenance "https://y/" :gov.unit/last-verified "2026-06-03"}]}',
        )
        auth = _write(tmp, "a.edn", "{:authority-records []}")
        errs = check([seed], auth)
        assert any("duplicate-qid" in e for e in errs), errs


def test_malformed_qid_and_missing_g5_fire():
    with tempfile.TemporaryDirectory() as tmp:
        seed = _write(
            tmp,
            "s.edn",
            '{:units [{:gov.unit/id "gov.bad" :gov.unit/wikidata "1023766" '  # no Q prefix
            ':gov.unit/official-url "https://b/"}]}',  # missing sourcing/provenance/last-verified
        )
        auth = _write(tmp, "a.edn", "{:authority-records []}")
        errs = check([seed], auth)
        assert any("malformed-qid" in e for e in errs), errs
        assert any("g5-missing" in e for e in errs), errs


def test_authority_mismatch_and_dangling_fire():
    with tempfile.TemporaryDirectory() as tmp:
        seed = _write(tmp, "s.edn", "{:units [" + _GOOD_UNIT + "]}")
        auth = _write(
            tmp,
            "a.edn",
            '{:authority-records ['
            '{:unit "gov.x" :wikidata "Q999" :official-url "https://x/"} '  # QID mismatch
            '{:unit "gov.ghost" :wikidata "Q2" :official-url "https://g/"}]}',  # dangling
        )
        errs = check([seed], auth)
        assert any("authority-qid-mismatch" in e for e in errs), errs
        assert any("dangling-authority" in e for e in errs), errs


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(fns)} passed")
