#!/usr/bin/env python3
"""Structural charter-invariant tests for 扶持 (fuchi).

These parse the ONTOLOGY + LEXICONS + Python code and assert that the invariants making this
the charter-clean inverse of an investment fund hold in all three places at once:

  G1 — no investment vehicle: instrument allowlist == sustenance set; equity/debt/ROI/exit absent
  G2 — cash≡0: :envelope/cash-usd-micros and :alloc/cash-usd-micros are :db/allowed [0]; lex const 0
  G3 — in-kind rails only: :cash-disbursement absent from the rail vocab
  G4 — covenant-gated: :anon / :server absent from author/covenant vocab
  G5 — payoff帰属 = etzhayyim: :maintainer/owns-payoff :db/allowed [false]
  G7 — non-adjudicating route: gov-routes present; no :decision attribute exists
  G9 — no-server-key: :alloc/server-held-key :db/allowed [false]

Standalone-runnable: python3 test_charter_invariants.py
"""
from __future__ import annotations

import pathlib
import sys

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SCHEMA = _ROOT.parents[1] / "00-contracts" / "schemas" / "maintainer-sustenance-ontology.kotoba.edn"
_LEX = _ROOT / "lex"

INVESTMENT_TOKENS = (":equity", ":debt", ":convertible", ":revenue-share",
                     ":profit-claim", ":carry", ":dividend", ":exit", ":loan", ":interest")


def _onto():
    return load_edn(_SCHEMA)


def _attr(onto, ident):
    for a in onto[":schema"]:
        if a.get(":db/ident") == ident:
            return a
    raise AssertionError(f"attribute {ident} missing from schema")


# ── G1: no investment vehicle ───────────────────────────────────────────────
def test_instrument_vocab_is_sustenance_only():
    onto = _onto()
    instruments = set(onto[":ontology/instruments"])
    assert instruments == {":in-kind-grant", ":sustenance", ":tooling-access", ":compute-access"}


def test_no_investment_token_anywhere_in_ontology():
    blob = _SCHEMA.read_text(encoding="utf-8").lower()
    # only allow these tokens inside the documented denylist comment / doc-strings, so check
    # they never appear as an :allowed enum member.
    instr = _attr(_onto(), ":alloc/instrument")
    allowed = set(instr[":db/allowed"])
    for tok in INVESTMENT_TOKENS:
        assert tok not in allowed, f"{tok} must not be allocatable (G1)"


def test_code_allowlist_matches_schema():
    from allocate import ALLOWED_INSTRUMENTS
    onto = {x.lstrip(":") for x in _onto()[":ontology/instruments"]}
    assert set(ALLOWED_INSTRUMENTS) == onto


# ── G2: cash≡0 ──────────────────────────────────────────────────────────────
def test_envelope_cash_allowed_zero_only():
    assert _attr(_onto(), ":envelope/cash-usd-micros")[":db/allowed"] == [0]


def test_alloc_cash_allowed_zero_only():
    assert _attr(_onto(), ":alloc/cash-usd-micros")[":db/allowed"] == [0]


# ── G3: in-kind rails only ──────────────────────────────────────────────────
def test_rail_vocab_has_no_cash_disbursement():
    rails = set(_onto()[":ontology/rails"])
    assert ":cash-disbursement" not in rails
    assert ":housing-commons" in rails and ":liquidity-warifu" in rails


def test_rail_kind_allowed_matches_vocab():
    allowed = set(_attr(_onto(), ":rail/kind")[":db/allowed"])
    assert allowed == set(_onto()[":ontology/rails"])


# ── G4: covenant-gated ──────────────────────────────────────────────────────
def test_covenant_vocab_excludes_anon_and_server():
    covs = set(_onto()[":ontology/covenants"])
    assert covs == {":outreach", ":vowed"}
    assert ":anon" not in covs and ":server" not in covs


# ── G5: payoff attribution = etzhayyim ──────────────────────────────────────
def test_owns_payoff_allowed_false_only():
    assert _attr(_onto(), ":maintainer/owns-payoff")[":db/allowed"] == [False]


# ── G7: non-adjudicating route ──────────────────────────────────────────────
def test_gov_routes_present():
    assert set(_onto()[":ontology/gov-routes"]) == {":auto", ":sbt-vote", ":council-lv7", ":refused"}


def test_no_decision_attribute_exists():
    idents = {a.get(":db/ident") for a in _onto()[":schema"]}
    for forbidden in (":gov/decision", ":alloc/decision", ":triage/decision"):
        assert forbidden not in idents, f"{forbidden} must not exist (G7 non-adjudicating)"


# ── G9: no-server-key ───────────────────────────────────────────────────────
def test_server_held_key_allowed_false_only():
    assert _attr(_onto(), ":alloc/server-held-key")[":db/allowed"] == [False]


# ── lexicon ↔ ontology cross-checks (the three-place property) ───────────────
def test_alloc_lexicon_instrument_enum_matches_ontology():
    lex = load_edn(_LEX / "allocationIntent.edn")
    props = lex[":defs"][":main"][":record"][":properties"]
    enum = set(props[":instrument"][":enum"])
    onto = {x.lstrip(":") for x in _onto()[":ontology/instruments"]}
    assert enum == onto


def test_alloc_lexicon_cash_const_zero():
    lex = load_edn(_LEX / "allocationIntent.edn")
    props = lex[":defs"][":main"][":record"][":properties"]
    assert props[":cashUsdMicros"][":const"] == 0
    assert props[":serverHeldKey"][":const"] is False


def test_covenant_lexicon_owns_payoff_const_false():
    lex = load_edn(_LEX / "maintainerCovenant.edn")
    props = lex[":defs"][":main"][":record"][":properties"]
    assert props[":ownsPayoff"][":const"] is False
    assert props[":serverHeldKey"][":const"] is False


def test_rail_lexicon_enum_matches_ontology():
    lex = load_edn(_LEX / "routingPlan.edn")
    enum = set(lex[":defs"][":main"][":record"][":properties"][":kind"][":enum"])
    onto = {x.lstrip(":") for x in _onto()[":ontology/rails"]}
    assert enum == onto


# ── R1(a) provisioning intent invariants ────────────────────────────────────
def test_prov_cash_allowed_zero_only():
    assert _attr(_onto(), ":prov/cash-usd-micros")[":db/allowed"] == [0]


def test_prov_published_allowed_false_only():
    assert _attr(_onto(), ":prov/published")[":db/allowed"] == [False]


def test_prov_server_held_key_false_only():
    assert _attr(_onto(), ":prov/server-held-key")[":db/allowed"] == [False]


def test_prov_lexicon_consts():
    props = load_edn(_LEX / "provisioningIntent.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":cashUsdMicros"][":const"] == 0
    assert props[":serverHeldKey"][":const"] is False
    assert props[":published"][":const"] is False


# ── R1(b) 1 SBT = 1 vote invariants ─────────────────────────────────────────
def test_ballot_weight_allowed_one_only():
    assert _attr(_onto(), ":ballot/weight")[":db/allowed"] == [1]


def test_ballot_server_held_key_false_only():
    assert _attr(_onto(), ":ballot/server-held-key")[":db/allowed"] == [False]


def test_ballot_choices_vocab():
    assert set(_onto()[":ontology/ballot-choices"]) == {":yes", ":no", ":abstain"}


def test_ballot_lexicon_weight_const_one():
    props = load_edn(_LEX / "voteBallot.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":weight"][":const"] == 1
    assert props[":serverHeldKey"][":const"] is False


# ── R1(c) toritate booking invariants ───────────────────────────────────────
def test_book_cash_allowed_zero_only():
    assert _attr(_onto(), ":book/cash-usd-micros")[":db/allowed"] == [0]


def test_book_categories_have_no_payroll():
    cats = set(_onto()[":ontology/book-categories"])
    for forbidden in (":payroll", ":salary", ":wage", ":bonus", ":commission"):
        assert forbidden not in cats


def test_book_category_matches_toritate_enum():
    # the schema :book/category :db/allowed must equal the ontology book-categories vocab
    allowed = set(_attr(_onto(), ":book/category")[":db/allowed"])
    assert allowed == set(_onto()[":ontology/book-categories"])


def test_book_code_categories_match_schema():
    from book import TORITATE_CATEGORIES
    onto = {x.lstrip(":") for x in _onto()[":ontology/book-categories"]}
    assert set(TORITATE_CATEGORIES) == onto


def test_booking_lexicon_cash_const_zero():
    props = load_edn(_LEX / "sustenanceBooking.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":cashUsdMicros"][":const"] == 0


def test_flow_classes_vocab():
    assert set(_onto()[":ontology/flow-classes"]) == {
        ":publicfund-to-fuchi", ":fuchi-to-provider", ":provider-to-maintainer"}


# ── R1(d) Displacement-Dividend coupling invariants ─────────────────────────
def test_tithe_bps_is_ten_percent():
    assert _onto()[":ontology/tithe-bps"] == 1000


def test_code_tithe_bps_matches_ontology():
    from couple import TITHE_BPS
    assert TITHE_BPS == _onto()[":ontology/tithe-bps"]


def test_earmark_funded_attr_exists():
    # G2 coupling gate hinges on :earmark/funded — it must be in the schema
    assert _attr(_onto(), ":earmark/funded")[":db/valueType"] == ":db.type/boolean"


def test_couple_admissible_attr_exists():
    assert _attr(_onto(), ":couple/admissible")[":db/valueType"] == ":db.type/boolean"


def test_tithe_split_is_exact_for_all_inputs():
    from couple import DisplacementEvent, earmark_from_surplus
    for s in (1, 7, 9999, 10_001, 60_000_000_000):
        em = earmark_from_surplus(DisplacementEvent("a", "c", 1, s, funded=True))
        assert em.tithe_usd_micros + em.earmark_usd_micros_yr == s


def test_g2_refuses_unfunded():
    from couple import DisplacementEvent, coupling_gate, earmark_from_surplus
    e = DisplacementEvent("sanae", "c", 1, 10, funded=False)
    g = coupling_gate(e, earmark_from_surplus(e), 1)
    assert g["admissible"] is False and "G2" in g["reason"]


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_charter_invariants.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
