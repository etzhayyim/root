"""Lock-in tests for the mitooshi (見通し) constitutional invariants.

Pins the structural properties designed in ADR-2606051800 (mitooshi — a
non-adjudicating probabilistic forecasting observatory; the charter-clean inverse
of a trading bot) so a future refactor cannot silently weaken a constitutional
invariant. A naive quant predictor IS profit speculation (Charter §1.3 + yobel
bar), so mitooshi's four invariants are load-bearing and each is declared in
ontology schema + lexicon enum/const + the methods/score.cljc guard. This suite
proves they agree:

  INVARIANT #1 — DISTRIBUTION-ONLY (G1): :forecast/point-asserted :db/allowed
      [false]. A deterministic single-future assertion is unrepresentable (非終末論).
  INVARIANT #2 — NON-SPECULATIVE (G2): :forecast/use excludes trade/speculation/
      wager/position. mitooshi never trades, holds a position, or derives P&L.
  INVARIANT #3 — PRIMARY-PUBLIC-SOURCE-ONLY (G4): :series/source-class excludes
      Bloomberg / CapIQ / Refinitiv / 四季報 and scraped Google-Trends.
  INVARIANT #4 — LEAK-FREE SCORING (G5): a score's observation MUST be strictly
      after the forecast's info-as-of, else it is a look-ahead leak. On an
      append-only Datom log this is structurally impossible; score-pair raises.

Invariants under test:

  1. G1 (ontology) — :forecast/point-asserted :db/allowed is exactly [false].
  2. G1 (lexicon) — forecastDistribution.pointAsserted is const false.
  3. G1 (guard) — score-pair raises on a point-asserted forecast.
  4. G2 (ontology + lexicon) — :forecast/use allowed set is the 5 non-speculative
     uses; trade/speculation/wager/position are absent from both.
  5. G2 (guard) — ALLOWED_USE covers the 5; score-pair raises on use='trade';
     silenMitooshiReview.nonSpeculative is const true.
  6. G4 (ontology + lexicon) — :series/source-class allowed set is the 5 primary-
     public classes; Bloomberg/Refinitiv/CapIQ/FactSet/scraped are absent.
  7. G5 (guard) — score-pair raises when obs.observed_at <= info_as_of and
     succeeds when strictly after.
  8. scoreResidual.derived const true (G5 residual is derived) +
     modelUpdateAttestation no-server-key + baien-edge runtime (G9/Murakumo-only).

NOTE: enforcement point 3 now exercises the cljc port (methods/score.cljc via bb
subprocess) since the Python methods/score.py was migrated to cljc.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_ONTOLOGY = _REPO / "00-contracts" / "schemas" / "forecasting-ontology.kotoba.edn"
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "mitooshi"
_ACTORS = _REPO / "20-actors"

_EXPECTED_USE = {"resilience", "planning", "nowcast", "early-warning", "research"}
_FORBIDDEN_USE = {"trade", "speculation", "wager", "position"}
_EXPECTED_SOURCE = {
    "public-broadcast",
    "primary-disclosure",
    "open-commons",
    "gov-open-data",
    "member-principal",
}
_FORBIDDEN_SOURCE = {"bloomberg", "capiq", "refinitiv", "factset", "scraped"}


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text())


def _record_props(lex: dict) -> dict:
    defs = lex["defs"]["main"]
    return defs.get("record", defs)["properties"]


def _ontology_allowed(attr: str) -> list[str]:
    text = _ONTOLOGY.read_text()
    m = re.search(re.escape(attr) + r"\s*\{.*?:db/allowed\s*\[(.*?)\]", text, re.S)
    assert m, f"could not locate {attr} :db/allowed in the ontology"
    return m.group(1).split()


def _bb(expr: str) -> subprocess.CompletedProcess:
    """Run a Clojure expression via bb with the actors classpath."""
    return subprocess.run(
        ["bb", "--classpath", str(_ACTORS), "-e", expr],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_REPO),
    )


# ─────────────────────────────────────────────────────────────────────────
# 1 + 2 + 3. G1 — distribution-only / no point assertion
# ─────────────────────────────────────────────────────────────────────────


def test_g1_ontology_point_asserted_allows_only_false():
    assert _ONTOLOGY.exists(), f"missing ontology: {_ONTOLOGY}"
    toks = _ontology_allowed(":forecast/point-asserted")
    assert toks == ["false"], (
        f"G1: :forecast/point-asserted :db/allowed MUST be [false] (非終末論); got {toks}"
    )


def test_g1_lexicon_point_asserted_const_false():
    props = _record_props(_load_json(_LEX / "forecastDistribution.json"))
    assert props["pointAsserted"].get("const") is False, (
        "G1: forecastDistribution.pointAsserted MUST be const false"
    )


def test_g1_guard_rejects_point_asserted_forecast():
    """G1: score-pair MUST raise on a point-asserted=true forecast (exercised via bb)."""
    result = _bb(
        "(require '[mitooshi.methods.score :as s])"
        "(def fc (s/->forecast \"f1\" \"gaussian\" :info-as-of 100 :point-asserted true))"
        "(def r (try (s/score-pair fc (s/->observation \"o1\" :observed-at 200 :value 0.5))"
        "            :no-throw (catch Exception e :threw)))"
        "(pr r)"
    )
    assert result.returncode == 0, f"bb failed: {result.stderr}"
    assert ":threw" in result.stdout, (
        "G1: score-pair MUST throw on point-asserted=true (非終末論 — deterministic "
        f"assertion unrepresentable); stdout={result.stdout!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 4 + 5. G2 — non-speculative use
# ─────────────────────────────────────────────────────────────────────────


def test_g2_use_set_is_non_speculative_ontology_and_lexicon():
    onto = {t.lstrip(":") for t in _ontology_allowed(":forecast/use")}
    assert onto == _EXPECTED_USE, f"G2: ontology :forecast/use drifted; got {sorted(onto)}"
    lex = set(_record_props(_load_json(_LEX / "forecastDistribution.json"))["use"]["enum"])
    assert lex == _EXPECTED_USE, f"G2: lexicon use enum drifted; got {sorted(lex)}"
    for bad in _FORBIDDEN_USE:
        assert bad not in onto and bad not in lex, (
            f"G2 VIOLATION: speculative use {bad!r} became representable"
        )


def test_g2_guard_rejects_speculative_use_and_review_const():
    """G2: ALLOWED_USE covers the 5 non-speculative uses; score-pair raises on use='trade'."""
    # Check that allowed-use in cljc covers the expected non-speculative set
    result_uses = _bb(
        "(require '[mitooshi.methods.score :as s])"
        "(pr (into #{} (map #(clojure.string/replace % #\"^:\" \"\") s/allowed-use)))"
    )
    assert result_uses.returncode == 0, f"bb failed: {result_uses.stderr}"
    # Parse the printed set from stdout (it will look like #{...})
    uses_str = result_uses.stdout.strip()
    for expected in _EXPECTED_USE:
        assert expected in uses_str, (
            f"G2: allowed-use missing expected member {expected!r}; got {uses_str!r}"
        )
    for bad in _FORBIDDEN_USE:
        assert bad not in uses_str, (
            f"G2 VIOLATION: speculative use {bad!r} found in cljc allowed-use; got {uses_str!r}"
        )

    # Check score-pair raises on use='trade'
    result_trade = _bb(
        "(require '[mitooshi.methods.score :as s])"
        "(def fc (s/->forecast \"f1\" \"gaussian\" :info-as-of 100 :use \"trade\"))"
        "(def r (try (s/score-pair fc (s/->observation \"o1\" :observed-at 200 :value 0.5))"
        "            :no-throw (catch Exception e :threw)))"
        "(pr r)"
    )
    assert result_trade.returncode == 0, f"bb failed: {result_trade.stderr}"
    assert ":threw" in result_trade.stdout, (
        "G2: score-pair MUST throw on use='trade' (speculation is structurally "
        f"unrepresentable); stdout={result_trade.stdout!r}"
    )

    # Lexicon check (unchanged from original)
    review = _record_props(_load_json(_LEX / "silenMitooshiReview.json"))
    assert review["nonSpeculative"].get("const") is True, (
        "G2: silenMitooshiReview.nonSpeculative MUST be const true"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. G4 — primary-public-source-only
# ─────────────────────────────────────────────────────────────────────────


def test_g4_source_class_is_primary_public_only():
    onto = {t.lstrip(":") for t in _ontology_allowed(":series/source-class")}
    assert onto == _EXPECTED_SOURCE, f"G4: ontology source-class drifted; got {sorted(onto)}"
    lex = set(_record_props(_load_json(_LEX / "seriesObservation.json"))["sourceClass"]["enum"])
    assert lex == _EXPECTED_SOURCE, f"G4: lexicon sourceClass enum drifted; got {sorted(lex)}"
    blob = " ".join(onto | lex)
    for bad in _FORBIDDEN_SOURCE:
        assert bad not in blob, (
            f"G4 VIOLATION: proprietary/scraped source {bad!r} became representable "
            f"(read the filing, never the terminal — kanjo §2(c)/(e))"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. G5 — leak-free scoring (look-ahead structurally refused)
# ─────────────────────────────────────────────────────────────────────────


def test_g5_guard_refuses_look_ahead_leak():
    """G5: score-pair MUST raise on observed_at <= info_as_of (look-ahead leak)."""
    result = _bb(
        "(require '[mitooshi.methods.score :as s])"
        "(def fc (s/->forecast \"f1\" \"gaussian\" :info-as-of 100 :mean 0.0 :sd 1.0))"
        # obs at info-as-of (== 100) — look-ahead leak
        "(def r1 (try (s/score-pair fc (s/->observation \"o-leak\" :observed-at 100 :value 0.5))"
        "             :no-throw (catch Exception e :threw)))"
        # obs before info-as-of (== 50) — look-ahead leak
        "(def r2 (try (s/score-pair fc (s/->observation \"o-leak2\" :observed-at 50 :value 0.5))"
        "             :no-throw (catch Exception e :threw)))"
        # obs strictly after (== 200) — should score cleanly
        "(def r3 (s/score-pair fc (s/->observation \"o-ok\" :observed-at 200 :value 0.5)))"
        "(pr {:r1 r1 :r2 r2 :r3-is-map (map? r3) :r3-has-crps (contains? r3 \"crps\")})"
    )
    assert result.returncode == 0, f"bb failed: {result.stderr}"
    assert ":r1 :threw" in result.stdout, (
        f"G5: score-pair MUST throw on observed_at==info_as_of (look-ahead); stdout={result.stdout!r}"
    )
    assert ":r2 :threw" in result.stdout, (
        f"G5: score-pair MUST throw on observed_at<info_as_of (look-ahead); stdout={result.stdout!r}"
    )
    assert ":r3-is-map true" in result.stdout, (
        f"G5: score-pair MUST succeed when observed_at>info_as_of; stdout={result.stdout!r}"
    )
    assert ":r3-has-crps true" in result.stdout, (
        f"G5: result map must contain 'crps' key; stdout={result.stdout!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 8. residual is derived + model-update is no-server-key / baien-edge
# ─────────────────────────────────────────────────────────────────────────


def test_residual_derived_and_model_update_no_server_key():
    assert _record_props(_load_json(_LEX / "scoreResidual.json"))["derived"].get("const") is True, (
        "G5: scoreResidual.derived MUST be const true (a residual is a derived join, "
        "never re-ingested as authoritative)"
    )
    mu = _record_props(_load_json(_LEX / "modelUpdateAttestation.json"))
    assert mu["serverHeldKey"].get("const") is False, (
        "modelUpdateAttestation.serverHeldKey MUST be const false (no-server-key; "
        "promotion is member-signed)"
    )
    assert mu["runtime"].get("const") == "baien-edge", (
        "N6/G9: modelUpdateAttestation.runtime MUST be const 'baien-edge' "
        "(federated edge; no commercial-GPU training)"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
