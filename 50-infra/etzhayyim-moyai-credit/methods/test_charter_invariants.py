"""Tests: the charter invariants, asserted across ledger + fair_share + lexicon together.

These are the load-bearing claims of ADR-2606062100 — that a *reward for inference
participation* can exist without becoming money, a benefit, governance power, or a dent in
Basic High Income. Each is checked structurally, not by inspection.
"""

from __future__ import annotations

import json
import os

from _harness import run_suite
from fair_share import Decision, affects_basic_high_income, evaluate_draw
from ledger import HALF_LIFE_EPOCHS, MoyaiLedger, redeemable_usd_micros

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_LEX = os.path.join(_ROOT, "00-contracts", "lexicons", "com", "etzhayyim", "moyai")


def _lex_props(name):
    with open(os.path.join(_LEX, name), encoding="utf-8") as f:
        doc = json.load(f)
    return doc["defs"]["main"]["record"]["properties"]


def test_cash_zero_no_monetary_path():
    # No function or field in the credit substrate yields a non-zero USD figure.
    assert redeemable_usd_micros() == 0
    assert _lex_props("contributionAttestation.json")["redeemableUsdMicros"]["const"] == 0
    assert _lex_props("drawReceipt.json")["redeemableUsdMicros"]["const"] == 0


def test_non_transferable_structural():
    # The ledger cannot move credit between identities — the verb does not exist.
    L = MoyaiLedger()
    for verb in ("transfer", "gift", "merge", "pool", "assign", "send"):
        assert not hasattr(L, verb)
    assert _lex_props("contributionAttestation.json")["transferable"]["const"] is False


def test_bhi_firewall():
    # The user's explicit constraint, three ways:
    #  (a) the policy constant is False,
    assert affects_basic_high_income() is False
    #  (b) the lexicon locks it const False,
    assert _lex_props("contributionAttestation.json")["affectsBasicHighIncome"]["const"] is False
    #  (c) essential floor is served identically for zero-credit and credit-rich members.
    poor = evaluate_draw(requested_units=50, floor_used_this_period=0, mesh_load=1.0,
                         credit_balance=0.0)
    rich = evaluate_draw(requested_units=50, floor_used_this_period=0, mesh_load=1.0,
                         credit_balance=10_000.0)
    assert poor.decision is rich.decision is Decision.FREE_SUBSISTENCE


def test_no_governance_weight():
    assert _lex_props("contributionAttestation.json")["grantsGovernanceWeight"]["const"] is False


def test_anti_class_no_benefit_and_decays():
    # Not a benefit/stage lever, AND cannot accumulate into a wealth/power store (decay).
    assert _lex_props("contributionAttestation.json")["grantsBenefitOrStage"]["const"] is False
    L = MoyaiLedger()
    L.mint("did:whale", 100_000, 0, "att")
    assert L.balance("did:whale", 20 * HALF_LIFE_EPOCHS) < 1.0  # hoarding decays to dust


def test_reward_actually_exists():
    # The directive was to KEEP a reward. Verify there genuinely IS one: verified work
    # produces a positive, spendable balance that buys real surplus draws under contention.
    L = MoyaiLedger()
    L.mint("did:abel", 200, 0, "att")
    bal = L.balance("did:abel", 0)
    assert bal == 200
    v = evaluate_draw(requested_units=150, floor_used_this_period=0, mesh_load=0.95,
                      credit_balance=bal)
    assert v.decision is Decision.CHARGE_SURPLUS and v.credit_to_burn > 0


def test_conservation_sink_le_source():
    L = MoyaiLedger()
    L.mint("did:a", 100, 0, "att")
    L.burn("did:a", 30, 1, "draw")
    L.assert_conservation()
    assert L.total_burned() <= L.total_minted()


run_suite("test_charter_invariants", [
    ("cash_zero", test_cash_zero_no_monetary_path),
    ("non_transferable", test_non_transferable_structural),
    ("bhi_firewall", test_bhi_firewall),
    ("no_governance_weight", test_no_governance_weight),
    ("anti_class_decays", test_anti_class_no_benefit_and_decays),
    ("reward_exists", test_reward_actually_exists),
    ("conservation", test_conservation_sink_le_source),
])
