"""Lock-in tests for the tsukuroi (繕い) constitutional invariants.

Pins the structural properties designed in ADR-2605291500 (tsukuroi —
authorized vulnerability-remediation + patch-proposal actor; akuma's
constructive sibling) so a future refactor cannot silently weaken a
constitutional invariant. None are amendable without Council process; this
suite fails fast if any artifact drifts. Mirrors test_tadori_invariants.py /
test_basic_high_income_invariants.py.

Invariants under test (the PROPOSE-ONLY / NO-PROBING / DEFENSIVE-ONLY /
NO-PLATFORM-HELD-KEY ceiling, ADR-2605291500 §"Capability ceiling"):

  1. remediationMandate.mergeAuthorityHeld const false (G4 propose-only).
  2. patchProposal.defensiveOnly const true (G5) + autonomousMerge const false
     (G4), both required.
  3. patchValidationResult.ranAgainstLiveTarget const false (G9) +
     sandboxNamespace const "tsukuroi-validate".
  4. silenTsukuroiReview pins 4 zero-counters const 0, all required.
  5. closureAttestation requires ownerMerged + akumaReprobePass + remediated
     (G11: no self-attested closure).
  6. No `type: number` (float) anywhere (Lexicon v1, ADR-2605190900).
  7. The 7 R0 cell stubs raise at import time until R1.
  8. The manifest pins 13 gates G1..G13 + 5 lexiconNamespaces matching disk.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "tsukuroi"
_MANDATE = _LEX / "remediationMandate.json"
_PROPOSAL = _LEX / "patchProposal.json"
_VALIDATION = _LEX / "patchValidationResult.json"
_CLOSURE = _LEX / "closureAttestation.json"
_SILEN = _LEX / "silenTsukuroiReview.json"
# manifest invariants -> 20-actors/tsukuroi/methods/test_manifest_invariants.cljc (jsonld retired)
_CELLS = _REPO / "20-actors" / "kotodama" / "cells"

_CELL_NAMES = [
    "tsukuroi_finding_intake",
    "tsukuroi_patch_synthesis",
    "tsukuroi_charter_rider_scan",
    "tsukuroi_patch_validation",
    "tsukuroi_pr_submission",
    "tsukuroi_closure_verification",
    "tsukuroi_silen_tsukuroi_review",
]

_ZERO_COUNTERS = [
    "autonomousMergeCount",
    "exploitArtifactCount",
    "outOfScopeWriteCount",
    "platformHeldKeyCount",
]


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


# ─── 1. remediationMandate — propose-only ───────────────────────────────


class TestRemediationMandate:
    def test_merge_authority_held_const_false(self):
        rec = _load(_MANDATE)["defs"]["main"]["record"]
        mah = rec["properties"]["mergeAuthorityHeld"]
        assert mah.get("type") == "boolean"
        assert mah.get("const") is False, "G4: tsukuroi never holds merge/deploy authority"
        assert "mergeAuthorityHeld" in rec["required"]


# ─── 2. patchProposal — defensive-only, no autonomous merge ─────────────


class TestPatchProposal:
    def test_defensive_only_const_true(self):
        rec = _load(_PROPOSAL)["defs"]["main"]["record"]
        do = rec["properties"]["defensiveOnly"]
        assert do.get("const") is True, "G5: fixes only, never an exploit/PoC"
        assert "defensiveOnly" in rec["required"]

    def test_autonomous_merge_const_false(self):
        rec = _load(_PROPOSAL)["defs"]["main"]["record"]
        am = rec["properties"]["autonomousMerge"]
        assert am.get("const") is False, "G4: a human owner merges"
        assert "autonomousMerge" in rec["required"]

    def test_submission_modes(self):
        rec = _load(_PROPOSAL)["defs"]["main"]["record"]
        modes = set(rec["properties"]["submissionMode"].get("knownValues", []))
        assert modes == {"fork-pr", "patch-file", "config-diff"}


# ─── 3. patchValidationResult — sandbox, never live target ──────────────


class TestPatchValidationResult:
    def test_ran_against_live_target_const_false(self):
        rec = _load(_VALIDATION)["defs"]["main"]["record"]
        r = rec["properties"]["ranAgainstLiveTarget"]
        assert r.get("const") is False, "G9: validation never runs against the live target"
        assert "ranAgainstLiveTarget" in rec["required"]

    def test_sandbox_namespace_pinned(self):
        rec = _load(_VALIDATION)["defs"]["main"]["record"]
        assert rec["properties"]["sandboxNamespace"].get("const") == "tsukuroi-validate"


# ─── 4. silenTsukuroiReview — zero-counters ─────────────────────────────


class TestSilenReviewZeroCounters:
    def test_four_zero_counters_const_zero_and_required(self):
        rec = _load(_SILEN)["defs"]["main"]["record"]
        props, req = rec["properties"], set(rec["required"])
        for c in _ZERO_COUNTERS:
            assert props.get(c, {}).get("type") == "integer", f"missing/typed counter {c}"
            assert props[c].get("const") == 0, f"{c} must be const 0"
            assert c in req, f"{c} must be required"

    def test_exactly_the_four_counters(self):
        rec = _load(_SILEN)["defs"]["main"]["record"]
        const_zero = {
            k for k, v in rec["properties"].items()
            if isinstance(v, dict) and v.get("const") == 0
        }
        assert const_zero == set(_ZERO_COUNTERS), f"counter set drifted: {const_zero ^ set(_ZERO_COUNTERS)}"


# ─── 5. closureAttestation — no self-attested closure ───────────────────


class TestClosureAttestation:
    def test_closure_requires_owner_merge_and_reprobe(self):
        rec = _load(_CLOSURE)["defs"]["main"]["record"]
        req = set(rec["required"])
        for f in ("ownerMerged", "akumaReprobePass", "remediated"):
            assert f in req, f"G11: {f} must be required (closure = owner merge + akuma re-probe)"


# ─── 6. no floats anywhere (Lexicon v1) ─────────────────────────────────


class TestNoFloatTypes:
    @pytest.mark.parametrize("path", [_MANDATE, _PROPOSAL, _VALIDATION, _CLOSURE, _SILEN])
    def test_no_number_type(self, path):
        bad = [n for n in _walk(_load(path)) if n.get("type") == "number"]
        assert not bad, f"{path.name}: no `type: number` (ADR-2605190900); found {len(bad)}"


# ─── 7. R0 cell stubs raise at import ───────────────────────────────────


class TestCellsRaiseAtImport:
    @pytest.mark.parametrize("cell", _CELL_NAMES)
    def test_cell_raises_runtime_error(self, cell):
        cell_py = _CELLS / cell / "cell.py"
        assert cell_py.exists(), f"missing cell scaffold {cell}"
        spec = importlib.util.spec_from_file_location(f"_tsukuroi_{cell}", cell_py)
        mod = importlib.util.module_from_spec(spec)
        with pytest.raises(RuntimeError, match="tsukuroi R0 scaffold"):
            spec.loader.exec_module(mod)

    def test_all_seven_cells_present(self):
        present = {p.name for p in _CELLS.glob("tsukuroi_*") if p.is_dir()}
        assert present == set(_CELL_NAMES), f"cell set drifted: {present ^ set(_CELL_NAMES)}"


# ─── 8. manifest gates + artifact consistency ───────────────────────────


class TestManifestConsistency:
    def test_each_lexicon_id_matches_namespace(self):
        for p in _LEX.glob("*.json"):
            assert _load(p)["id"] == f"com.etzhayyim.tsukuroi.{p.stem}"

