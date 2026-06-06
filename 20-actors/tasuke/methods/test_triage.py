#!/usr/bin/env python3
"""Tests for 助 (tasuke) triage — scam-kind classification, severity, free-windows, gates."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from triage import SCAM_KINDS, classify, support_cost_jpy, triage

_SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-cybercrime-cases.kotoba.edn"


def _intake(**over):
    base = {":case/id": "t1", ":case/consent": True, ":case/support-cost-jpy": 0,
            ":case/server-held-key": False, ":case/narrative": ""}
    base.update(over)
    return base


# ── G1 全て無料 ──────────────────────────────────────────────────────────────
def test_support_is_always_free():
    assert support_cost_jpy() == 0
    assert support_cost_jpy({":case/loss-jpy": 999}) == 0


def test_nonzero_cost_intake_refused():
    try:
        triage(_intake(**{":case/support-cost-jpy": 100}))
        assert False, "G1 should refuse a non-zero support cost"
    except ValueError as e:
        assert "G1" in str(e)


def test_every_triage_output_is_free():
    for c in load_edn(_SEED)[":case/batch"]:
        assert triage(c)[":triage/support-cost-jpy"] == 0


# ── G7 consent + no-server-key ───────────────────────────────────────────────
def test_no_consent_refused():
    try:
        triage(_intake(**{":case/consent": False}))
        assert False
    except ValueError as e:
        assert "G7" in str(e)


def test_server_held_key_refused():
    try:
        triage(_intake(**{":case/server-held-key": True}))
        assert False
    except ValueError as e:
        assert "no-server-key" in str(e)


# ── G4 classification is a KIND, in vocab, never a verdict ────────────────────
def test_classify_keywords():
    assert classify(_intake(**{":case/narrative": "口座から不正送金された"})) == "unauthorized-transfer"
    assert classify(_intake(**{":case/narrative": "アカウントが乗っ取りされてログインできない"})) == "account-takeover"
    assert classify(_intake(**{":case/narrative": "偽サイトのフィッシングにあった"})) == "phishing"
    assert classify(_intake(**{":case/narrative": "サポート詐欺の警告画面"})) == "support-scam"


def test_explicit_scam_kind_honored():
    assert classify(_intake(**{":case/scam-kind": ":ransomware"})) == "ransomware"


def test_every_classification_is_in_vocab():
    for c in load_edn(_SEED)[":case/batch"]:
        assert triage(c)[":triage/scam-kind"].lstrip(":") in SCAM_KINDS


def test_no_verdict_field_in_output():
    t = triage(_intake(**{":case/scam-kind": ":investment-scam"}))
    assert not any("verdict" in k or "guilty" in k or "crime" in k for k in t)


# ── severity + actions + windows + G5 (no paid referral) ─────────────────────
def test_unauthorized_transfer_with_loss_is_critical():
    t = triage(_intake(**{":case/scam-kind": ":unauthorized-transfer", ":case/loss-jpy": 5000}))
    assert t[":triage/severity"] == ":critical"


def test_actions_nonempty_and_evidence_first():
    t = triage(_intake(**{":case/scam-kind": ":phishing"}))
    assert t[":triage/actions"] and "証拠" in t[":triage/actions"][0]


def test_windows_present_and_free():
    t = triage(_intake(**{":case/scam-kind": ":unauthorized-transfer"}))
    assert t[":triage/windows"] and t[":triage/paid-referral"] is False


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_triage.py")
    sys.exit(1 if failed else 0)
