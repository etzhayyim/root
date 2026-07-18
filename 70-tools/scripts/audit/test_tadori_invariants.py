"""Lock-in tests for the tadori (辿) constitutional invariants.

Pins the structural properties designed in ADR-2605301400 (tadori — authorized
on-chain transaction-tracing + actor-attribution actor, kotoba-EAVT-native) so a
future refactor cannot silently weaken a constitutional invariant. None of these
are amendable without Council process (§1.12 items Lv7+); this suite fails fast
if any artifact drifts.

Invariants under test:

  1. silenTadoriReview pins 9 structural zero-counters `const: 0`, all required —
     the on-chain audit proof that the §D1 gates hold (no caseless write, no
     plaintext PII, no proprietary system-of-record, no enforcement, no
     platform-held key, no Murakumo-bypass, no mass surveillance, no adherent
     de-anon, no non-kotoba store).
  2. caseMandate.transparentForceLogged is `const: true` (G5 on-chain-monitorable)
     and `phase` is the dry-run/live pair {0,1} with 0 the default posture (G3).
  3. attributionFinding.encrypted is required and objectKind carries the PII
     classes person/ip-obs/device that force encryption (G6).
  4. No `type: number` (float) anywhere — Lexicon v1 integer-with-implied-units
     (ADR-2605190900); confidence is integer per-mille.
  5. The 6 R0 Pregel cell stubs raise at import time until T1 (no accidental
     activation before Council ratification).
  6. The manifest pins 12 immutable gates G1..G12 and the evidence-only /
     no-enforcement ceiling.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_TADORI_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "tadori"
_CASE = _TADORI_LEX / "caseMandate.json"
_ATTR = _TADORI_LEX / "attributionFinding.json"
_TRACE = _TADORI_LEX / "traceReport.json"
_SILEN = _TADORI_LEX / "silenTadoriReview.json"
# manifest invariants moved to orgs/etzhayyim/com-etzhayyim-tadori/methods/test_manifest_invariants.cljc
# (reads manifest.edn; the jsonld is retired). This suite keeps the lexicon + Python
# cell-scaffold invariants, which do not read the manifest.
_CELLS = _REPO / "20-actors" / "kotodama" / "cells"

_CELL_NAMES = [
    "tadori_case_intake",
    "tadori_tx_trace",
    "tadori_address_label",
    "tadori_attribution_join",
    "tadori_transparent_force_log",
    "tadori_silen_tadori_review",
]

_ZERO_COUNTERS = [
    "noncaseWriteCount",
    "plaintextPiiCount",
    "proprietarySorCount",
    "enforcementActionCount",
    "platformHeldKeyCount",
    "murakumoBypassCount",
    "massSurveillanceCount",
    "adherentDeanonCount",
    "nonKotobaStoreCount",
]


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


def _walk(node):
    """Yield every dict node in a nested JSON structure."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


# ─── 1. silenTadoriReview zero-counters ─────────────────────────────────


class TestSilenReviewZeroCounters:
    def test_nine_zero_counters_const_zero_and_required(self):
        rec = _load(_SILEN)["defs"]["main"]["record"]
        props = rec["properties"]
        req = set(rec["required"])
        for c in _ZERO_COUNTERS:
            assert c in props, f"silenTadoriReview missing counter {c!r}"
            assert props[c].get("type") == "integer"
            assert props[c].get("const") == 0, (
                f"{c} must be const 0 — it is the on-chain proof a §D1 gate holds"
            )
            assert c in req, f"{c} must be required so every review carries the proof"

    def test_exactly_the_nine_counters(self):
        # If a counter is added/removed the test must be updated deliberately —
        # this guards against a silent weakening of the audit surface.
        rec = _load(_SILEN)["defs"]["main"]["record"]
        const_zero = {
            k for k, v in rec["properties"].items()
            if isinstance(v, dict) and v.get("const") == 0
        }
        assert const_zero == set(_ZERO_COUNTERS), (
            f"zero-counter set drifted: {const_zero ^ set(_ZERO_COUNTERS)}"
        )


# ─── 2. caseMandate authorization-anchor invariants ─────────────────────


class TestCaseMandate:
    def test_transparent_force_logged_const_true(self):
        rec = _load(_CASE)["defs"]["main"]["record"]
        tfl = rec["properties"]["transparentForceLogged"]
        assert tfl.get("type") == "boolean"
        assert tfl.get("const") is True, "G5: every case action is on-chain monitorable"

    def test_phase_is_dryrun_live_pair(self):
        rec = _load(_CASE)["defs"]["main"]["record"]
        phase = rec["properties"]["phase"]
        assert phase.get("type") == "integer"
        assert set(phase.get("knownValues", [])) == {0, 1}, (
            "phase is the {0 dry-run, 1 live} pair (G3 default 0)"
        )

    def test_authorization_anchor_required(self):
        rec = _load(_CASE)["defs"]["main"]["record"]
        req = set(rec["required"])
        for f in ("caseId", "authorizationRef", "authorityDid", "authoritySignature"):
            assert f in req, f"G3: {f} must be required (no caseless / unsigned live write)"


# ─── 3. attributionFinding PII-encryption invariants ────────────────────


class TestAttributionFinding:
    def test_encrypted_is_required(self):
        rec = _load(_ATTR)["defs"]["main"]["record"]
        assert "encrypted" in set(rec["required"]), (
            "G6: every attribution finding must declare its encryption posture"
        )

    def test_object_kind_carries_pii_classes(self):
        rec = _load(_ATTR)["defs"]["main"]["record"]
        kinds = set(rec["properties"]["objectKind"].get("knownValues", []))
        for k in ("person", "ip-obs", "device"):
            assert k in kinds, f"objectKind must include PII class {k!r} (forces encrypted=true)"

    def test_confidence_is_integer_permille(self):
        rec = _load(_ATTR)["defs"]["main"]["record"]
        conf = rec["properties"]["confidence"]
        assert conf.get("type") == "integer", "Lexicon v1: confidence is integer per-mille, not float"
        assert conf.get("maximum") == 1000


# ─── 4. no floats anywhere (Lexicon v1) ─────────────────────────────────


class TestNoFloatTypes:
    @pytest.mark.parametrize("path", [_CASE, _ATTR, _TRACE, _SILEN])
    def test_no_number_type(self, path):
        bad = [n for n in _walk(_load(path)) if n.get("type") == "number"]
        assert not bad, f"{path.name}: no `type: number` allowed (ADR-2605190900); found {len(bad)}"


# ─── 5. R0 cell stubs raise at import time ──────────────────────────────


class TestCellsRaiseAtImport:
    @pytest.mark.parametrize("cell", _CELL_NAMES)
    def test_cell_raises_runtime_error(self, cell):
        # py→cljc port: the cell scaffold is now cell.cljc (cell.py retired). Verify it
        # throws the R0-scaffold ex-info — the cljc `solve` raises the same message.
        cell_cljc = _CELLS / cell / "cell.cljc"
        assert cell_cljc.exists(), f"missing cell scaffold {cell}/cell.cljc"
        src = cell_cljc.read_text()
        assert "ex-info" in src and "tadori R0 scaffold" in src, (
            f"{cell}/cell.cljc must throw the tadori R0 scaffold ex-info"
        )

    def test_all_six_cells_present(self):
        present = {p.name for p in _CELLS.glob("tadori_*") if p.is_dir()}
        assert present == set(_CELL_NAMES), f"cell set drifted: {present ^ set(_CELL_NAMES)}"


# ─── 6. manifest gates + manifest↔disk consistency ──────────────────────
# Moved to orgs/etzhayyim/com-etzhayyim-tadori/methods/test_manifest_invariants.cljc (reads
# manifest.edn; the jsonld is retired). The lexicon-id ↔ filename check below
# reads only the lexicon JSONs (no manifest), so it stays here.


class TestLexiconArtifactConsistency:
    def test_each_lexicon_id_matches_its_namespace(self):
        for p in _TADORI_LEX.glob("*.json"):
            lex_id = _load(p)["id"]
            assert lex_id == f"com.etzhayyim.tadori.{p.stem}", (
                f"{p.name}: lexicon id {lex_id!r} must match its filename + namespace"
            )


# ─── 8. lexicon enum coverage (designed value sets) ─────────────────────


class TestLexiconEnumCoverage:
    def test_case_mandate_authorization_basis_enum(self):
        rec = _load(_CASE)["defs"]["main"]["record"]
        basis = set(rec["properties"]["authorizationBasis"].get("knownValues", []))
        assert basis == {
            "fraud-victim-recovery",
            "aml-cti-duty",
            "sanctioned-entity-tracing",
            "council-transparent-force",
        }, "the 4 constitutional bases for an authorized trace must be pinned (G3)"

    def test_trace_report_classification_covers_key_classes(self):
        rec = _load(_TRACE)["defs"]["main"]["record"]
        classes = set(rec["properties"]["classification"].get("knownValues", []))
        # bridge_pool is the class whose v1 false-positive ADR-2605152000 fixed;
        # mixer/sanctioned/whale_eoa are the high-signal AML classes.
        for c in ("bridge_pool", "mixer", "sanctioned", "whale_eoa"):
            assert c in classes, f"traceReport.classification must cover {c!r}"

    def test_attribution_object_kinds_split_pii_and_public(self):
        rec = _load(_ATTR)["defs"]["main"]["record"]
        kinds = set(rec["properties"]["objectKind"].get("knownValues", []))
        # PII classes force encryption; org/email are the broader set.
        assert {"person", "ip-obs", "device"} <= kinds
        assert {"org", "email"} <= kinds
