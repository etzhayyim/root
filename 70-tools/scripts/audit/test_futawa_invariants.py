"""Lock-in tests for the futawa (二輪 / small-displacement motorcycle) invariants.

futawa is the small-displacement motorcycle manufacturing actor (≤250cc / ≤15kW
ceiling). Its attestation lexicons encode structural Charter-compliance gates and
an anti-planned-obsolescence durability target; the displacement/power ceiling is
Council-gated via the silen review scope. This suite pins them so a refactor
cannot silently weaken a charter/safety invariant. Mirrors the other lock-in suites.

  1. Structural compliance gates — every gNCompliant-style attestation flag is
     const true (a record cannot attest non-compliance).
  2. Anti-planned-obsolescence — engineAttestation.g14ServiceLifeYearsTarget
     const 30 (a 30-year repairable service-life target, not a disposable engine).
  3. Ceiling is Council-gated — silenMobilityReview.scope carries the explicit
     wave-2 expansion gates (>250cc, >15kW), proving the ≤250cc/≤15kW ceiling can
     only be raised through a Council review, never silently.
  4. No floats (Lexicon v1); id↔namespace; manifest namespaces match disk.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "futawa"
# manifest invariants -> orgs/etzhayyim/com-etzhayyim-futawa/methods/test_manifest_invariants.cljc (jsonld retired)

# (lexicon stem, field) → expected const true. The structural compliance gates.
_TRUE_GATES = [
    ("electricalAttestation", "g8Compliant"),
    ("electricalAttestation", "g12OpenDiagnostic"),
    ("engineAttestation", "g11Compliant"),
    ("paintAttestation", "g5CharterPass"),
    ("paintAttestation", "g7VocCompliant"),
    ("partsCatalog", "g12ForwardPublishing"),
    ("testRecord", "g6SoundCompliant"),
    ("testRecord", "g7AbsFunctionCompliant"),
    ("vehicleLotAttestation", "g12Compliant"),
    ("vehicleLotAttestation", "g13PreRegisteredWithHodoki"),
    ("vehicleLotAttestation", "g4BilingualMet"),
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


def _rec(stem: str) -> dict:
    return _load(_LEX / f"{stem}.json")["defs"]["main"]["record"]


# ─── 1. structural compliance gates ─────────────────────────────────────


class TestComplianceGates:
    @pytest.mark.parametrize("stem,field", _TRUE_GATES)
    def test_gate_is_const_true(self, stem, field):
        v = _rec(stem)["properties"].get(field, {})
        assert v.get("const") is True, f"{stem}.{field} must be const true (structural compliance)"


# ─── 2. anti-planned-obsolescence durability ────────────────────────────


class TestServiceLife:
    def test_engine_service_life_target_30_years(self):
        v = _rec("engineAttestation")["properties"]["g14ServiceLifeYearsTarget"]
        assert v.get("const") == 30, (
            "g14: 30-year repairable service-life target (anti-planned-obsolescence); "
            "a refactor must not silently lower it"
        )


# ─── 3. ≤250cc / ≤15kW ceiling is Council-gated ─────────────────────────


class TestCeilingIsCouncilGated:
    def test_silen_review_scope_has_displacement_and_power_expansion_gates(self):
        scope = set(_rec("silenMobilityReview")["properties"]["scope"].get("knownValues", []))
        assert "wave-2-displacement-above-250cc" in scope, (
            "raising the 250cc ceiling must be an explicit Council silen-review scope"
        )
        assert "wave-2-electric-above-15kw" in scope, (
            "raising the 15kW ceiling must be an explicit Council silen-review scope"
        )

    def test_silen_review_verdict_enum(self):
        verdict = set(_rec("silenMobilityReview")["properties"]["verdict"].get("knownValues", []))
        assert verdict == {"approve", "approve-with-conditions", "defer", "reject"}


# ─── 4. hygiene + manifest consistency ──────────────────────────────────


class TestHygieneAndManifest:
    @pytest.mark.parametrize("path", sorted(_LEX.glob("*.json")))
    def test_no_number_type(self, path):
        bad = [n for n in _walk(_load(path)) if n.get("type") == "number"]
        assert not bad, f"{path.name}: no `type: number` (ADR-2605190900); found {len(bad)}"

    def test_each_id_matches_namespace(self):
        for p in _LEX.glob("*.json"):
            assert _load(p)["id"] == f"com.etzhayyim.futawa.{p.stem}"

