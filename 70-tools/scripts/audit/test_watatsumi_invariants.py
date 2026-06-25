"""Lock-in tests for the watatsumi (綿津見 / civilian submersible) invariants.

watatsumi is the civilian submersible manufacturing actor (ADR-2605252200) with a
hard ≤6500 m civilian depth ceiling (G12). This suite pins its safety ceilings and
— after this commit — its full Lexicon-v1 compliance: pressureTestRecord and
pressureHullAttestation carried `type: number` floats (testPressureBar /
leakRateMlPerMin / roundness.maxOutOfRoundPct / limitPct) and silenSubmersibleReview
used an inline object instead of a $ref, all of which the repo's own
validate-lexicons.py flags (ADR-2605190900 integer-with-implied-units rule). The
floats were rescaled to integer units (deci-bar, µL/min, ppm) and the inline object
extracted to a #councilSignature def. Mirrors the other lock-in suites.

  1. No floats anywhere in the 8 watatsumi lexicons (locks the rescale).
  2. ≤6500 m depth ceiling (G12) pinned on pressureTestRecord.
  3. Rescaled integer units carry their ceilings (deci-bar, µL/min ≤ 1000, ppm = 5000).
  4. silenSubmersibleReview uses a $ref for councilSignatures + minItems 5.
  5. id↔namespace; manifest namespaces match disk; DID.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "watatsumi"
# manifest invariants -> 20-actors/watatsumi/methods/test_manifest_invariants.cljc (jsonld retired)


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


# ─── 1. Lexicon v1: no floats (the violation this commit closed) ────────


class TestNoFloats:
    @pytest.mark.parametrize("path", sorted(_LEX.glob("*.json")))
    def test_no_number_type(self, path):
        bad = [n for n in _walk(_load(path)) if n.get("type") == "number"]
        assert not bad, (
            f"{path.name}: `type: number` is prohibited (Lexicon v1, ADR-2605190900) — "
            f"use integer with implied units; found {len(bad)}"
        )


# ─── 2. ≤6500 m civilian depth ceiling (G12) ────────────────────────────


class TestDepthCeiling:
    def test_design_depth_max_6500(self):
        props = _rec("pressureTestRecord")["properties"]
        assert props["designDepthM"].get("maximum") == 6500, "G12: civilian depth ceiling 6500 m"

    def test_g12_kpi_check_const_6500(self):
        props = _rec("pressureTestRecord")["properties"]
        kpi = props["g12KpiCheck"]["properties"]["maxCivilianDepthM"]
        assert kpi.get("const") == 6500, "G12 KPI cap is structurally 6500 m"


# ─── 3. rescaled integer units carry their ceilings ─────────────────────


class TestRescaledUnits:
    def test_test_pressure_is_integer_dbar(self):
        p = _rec("pressureTestRecord")["properties"]
        assert "testPressureDbar" in p and p["testPressureDbar"]["type"] == "integer"
        assert "testPressureBar" not in p, "old float field must be gone"

    def test_leak_rate_integer_microlitre_ceiling_1000(self):
        p = _rec("pressureTestRecord")["properties"]
        leak = p.get("leakRateMicrolitrePerMin", {})
        assert leak.get("type") == "integer"
        assert leak.get("maximum") == 1000, "1000 µL/min = 1.0 mL/min acceptance ceiling"
        assert "leakRateMlPerMin" not in p

    def test_roundness_limit_ppm_const_5000(self):
        r = _rec("pressureHullAttestation")["properties"]["roundness"]["properties"]
        assert r["maxOutOfRoundPpm"]["type"] == "integer"
        assert r["limitPpm"].get("const") == 5000, "0.5% Ø roundness limit = 5000 ppm"
        assert "maxOutOfRoundPct" not in r and "limitPct" not in r


# ─── 4. silenSubmersibleReview uses a $ref (no inline object) ────────────


class TestSilenReviewRef:
    def test_council_signatures_is_ref(self):
        review = _load(_LEX / "silenSubmersibleReview.json")
        item = review["defs"]["main"]["record"]["properties"]["councilSignatures"]["items"]
        assert item.get("type") == "ref", "inline object must be a $ref to a def (Lexicon v1)"
        assert "councilSignature" in review["defs"], "the referenced def must exist"

    def test_quorum_min_five(self):
        sig = _rec("silenSubmersibleReview")["properties"]["councilSignatures"]
        assert sig.get("minItems") == 5, "Council 5-of-7 Safe quorum"


# ─── 5. id↔namespace + manifest consistency ─────────────────────────────


class TestManifestConsistency:
    def test_each_id_matches_namespace(self):
        for p in _LEX.glob("*.json"):
            assert _load(p)["id"] == f"com.etzhayyim.watatsumi.{p.stem}"

