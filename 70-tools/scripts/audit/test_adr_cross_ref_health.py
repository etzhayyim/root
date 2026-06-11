"""Tests for adr-cross-ref-health.py.

Locks in the structural invariants of the ADR cross-reference audit
so that future refactors don't silently break the filter logic.

The audit grew through iters 40-45 with:
- 3 structural filters (range expr / forward-ref marker / historical orphan)
- 5 orphan categories (legacy-4digit / placeholder-0000-suffix /
  invalid-mm-overflow / quarter-hour-planned-slot / non-canonical-mm)

Each filter and each category has a representative case captured here.
If a regex tweak accidentally over- or under-matches, these tests fail.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


_SCRIPT = Path(__file__).resolve().parent / "adr-cross-ref-health.py"


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("adr_cross_ref_health", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["adr_cross_ref_health"] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── Category invariants (pure-function tests) ─────────────────────────

class TestCategorize:
    """Each ADR ID format should land in the expected category bucket."""

    def test_legacy_4digit(self, audit):
        assert audit.categorize("0031") == "legacy-4digit"
        assert audit.categorize("0098") == "legacy-4digit"

    def test_placeholder_0000_suffix(self, audit):
        # IDs ending in 0000 are obvious round-number stubs.
        assert audit.categorize("2604210000") == "placeholder-0000-suffix"
        assert audit.categorize("2604300000") == "placeholder-0000-suffix"

    def test_invalid_mm_overflow(self, audit):
        # MM >= 60 is a clock-impossibility (typo: +15 to :45 → :60).
        assert audit.categorize("2605250760") == "invalid-mm-overflow"
        assert audit.categorize("2605250860") == "invalid-mm-overflow"
        # MM = 99 also invalid.
        assert audit.categorize("2605250899") == "invalid-mm-overflow"

    def test_quarter_hour_planned_slot(self, audit):
        # MM in {00, 15, 30, 45} — typical authored timestamps.
        assert audit.categorize("2605250715") == "quarter-hour-planned-slot"
        assert audit.categorize("2605250730") == "quarter-hour-planned-slot"
        assert audit.categorize("2605250745") == "quarter-hour-planned-slot"
        assert audit.categorize("2605250800") == "quarter-hour-planned-slot"

    def test_non_canonical_mm(self, audit):
        # MM not in quarter set but < 60 — wave-numbering sub-index.
        assert audit.categorize("2605250004") == "non-canonical-mm"
        assert audit.categorize("2605250005") == "non-canonical-mm"
        assert audit.categorize("2605211653") == "non-canonical-mm"

    def test_other(self, audit):
        # 12-digit IDs (rare, with seconds) and odd lengths.
        assert audit.categorize("260427183045") == "other"
        assert audit.categorize("12345") == "other"


# ─── Regex pattern invariants ──────────────────────────────────────────

class TestRangeExpressionFilter:
    """`ADR-X..Y` range syntax should expand to two distinct IDs."""

    def test_matches_typical_range(self, audit):
        m = audit.ADR_RANGE_RE.search("Silicon Wave 2 (ADR-2605242700..2605242915)")
        assert m is not None
        assert m.group(1) == "2605242700"
        assert m.group(2) == "2605242915"

    def test_does_not_match_single_id(self, audit):
        m = audit.ADR_RANGE_RE.search("see ADR-2605242700")
        assert m is None

    def test_does_not_match_unrelated_dots(self, audit):
        # `..` outside an ADR ref pair shouldn't trigger.
        m = audit.ADR_RANGE_RE.search("..nothing ADR-2605242700 here..")
        assert m is None


class TestForwardRefMarkerFilter:
    """Citations followed by `(R1)` / `(planned)` / etc. are reservations."""

    def test_r_phase_marker(self, audit):
        assert audit.FORWARD_REF_MARKER_RE.search("(R0)") is not None
        assert audit.FORWARD_REF_MARKER_RE.search("(R1)") is not None
        assert audit.FORWARD_REF_MARKER_RE.search("(R3)") is not None

    def test_r_phase_with_qualifier(self, audit):
        # `(R0 scaffold)` should still match because R[0-9] + word chars.
        assert audit.FORWARD_REF_MARKER_RE.search("(R0 scaffold)") is not None
        assert audit.FORWARD_REF_MARKER_RE.search("(R2 charter)") is not None

    def test_keyword_markers(self, audit):
        for kw in ("(planned)", "(future)", "(reserved)", "(scaffold)", "(TBD)", "(tbd)"):
            assert audit.FORWARD_REF_MARKER_RE.search(kw) is not None, kw

    def test_does_not_match_unrelated_parens(self, audit):
        assert audit.FORWARD_REF_MARKER_RE.search("(see also)") is None
        assert audit.FORWARD_REF_MARKER_RE.search("(2026-05-26)") is None
        assert audit.FORWARD_REF_MARKER_RE.search("(R10000 too long)") is None


class TestHistoricalOrphanFilter:
    """Lines acknowledging 'drafted but not retained' are forensic notes."""

    def test_drafted_then_not_retained(self, audit):
        line = "(gate (c) standalone ADR-2605211653 was drafted but not retained)"
        assert audit.HISTORICAL_ORPHAN_RE.search(line) is not None

    def test_drafted_then_inline(self, audit):
        line = "ADR-2605211653 drafted but design documented inline"
        assert audit.HISTORICAL_ORPHAN_RE.search(line) is not None

    def test_standalone_drafted(self, audit):
        line = "An earlier-drafted standalone ADR-2605211653 (per-actor SQLite PVC)"
        assert audit.HISTORICAL_ORPHAN_RE.search(line) is not None

    def test_originally_drafted(self, audit):
        line = "originally-drafted standalone ADR-2605211653 was merged"
        assert audit.HISTORICAL_ORPHAN_RE.search(line) is not None

    def test_does_not_match_drafted_alone(self, audit):
        # Just "drafted" without one of the qualifiers shouldn't match —
        # avoids over-matching unrelated mentions like "drafted today".
        assert audit.HISTORICAL_ORPHAN_RE.search("ADR-2605000000 was drafted today") is None

    def test_does_not_match_qualifier_alone(self, audit):
        # And vice versa — qualifier without "drafted" shouldn't match.
        assert audit.HISTORICAL_ORPHAN_RE.search("see ADR-2605000000, originally proposed") is None


# ─── End-to-end smoke test ─────────────────────────────────────────────

class TestEndToEnd:
    """The script should produce coherent output against the live repo."""

    def test_finds_some_existing_adrs(self, audit):
        existing = audit.find_existing_adr_ids()
        # At least 100 ADRs should be on disk in the canonical dir.
        assert len(existing) > 100

    def test_existing_ids_are_strings(self, audit):
        existing = audit.find_existing_adr_ids()
        for adr_id in list(existing)[:5]:
            assert isinstance(adr_id, str)
            assert adr_id.isdigit()
            assert len(adr_id) in (4, 10, 12)
