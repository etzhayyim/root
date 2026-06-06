#!/usr/bin/env python3
"""Tests for 助 (tasuke) plain-language intake — 誰でも使える, invariants baked in."""
from __future__ import annotations

import intake
import packet


# ── loss parser handles human input ──────────────────────────────────────────
def test_parse_yen_forms():
    assert intake.parse_yen("480000") == 480000
    assert intake.parse_yen("48万") == 480000
    assert intake.parse_yen("48万円") == 480000
    assert intake.parse_yen("480,000円") == 480000
    assert intake.parse_yen("1万5000") == 15000
    assert intake.parse_yen("なし") == 0
    assert intake.parse_yen("") == 0


def test_parse_yesno():
    assert intake.parse_yesno("はい") is True
    assert intake.parse_yesno("yes") is True
    assert intake.parse_yesno("いいえ") is False
    assert intake.parse_yesno("") is False


# ── build_case bakes in G1/G7 ────────────────────────────────────────────────
def _answers(**over):
    base = {"consent": "はい", "narrative": "口座から不正送金された", "occurred": "2026-06-03",
            "loss": "48万", "service": "○○銀行", "account_id": "普通1234567"}
    base.update(over)
    return base


def test_build_case_sets_invariants():
    c = intake.build_case_from_answers(_answers())
    assert c[":case/consent"] is True
    assert c[":case/support-cost-jpy"] == 0
    assert c[":case/server-held-key"] is False
    assert c[":case/loss-jpy"] == 480000
    assert c[":case/loss-breakdown"][0][":jpy"] == 480000


def test_build_case_refuses_without_consent():
    for bad in ("いいえ", "", "no"):
        try:
            intake.build_case_from_answers(_answers(consent=bad))
            assert False, f"consent={bad!r} must raise (G7)"
        except ValueError as e:
            assert "G7" in str(e)


def test_case_id_is_deterministic():
    a, b = _answers(), _answers()
    assert intake.build_case_from_answers(a)[":case/id"] == intake.build_case_from_answers(b)[":case/id"]


# ── end-to-end: answers → packet, free, member-authored ──────────────────────
def test_answers_to_packet_is_free_and_complete():
    case = intake.build_case_from_answers(_answers())
    p = packet.build_packet(case)
    assert p["cost"] == 0
    kinds = [d[":doc/kind"].lstrip(":") for d in p["documents"]]
    assert "damage-report" in kinds and "bank-freeze-request" in kinds  # money moved
    for d in p["documents"]:
        assert d[":doc/authored-by"] == ":member" and d[":doc/published"] is False


# ── interactive shell honors the injected asker + consent abort ──────────────
def test_interactive_collects_with_injected_asker():
    answers = iter(["はい", "乗っ取り被害", "2026-06-02", "なし", "LINE", "@me"])
    case = intake.interactive(ask=lambda _prompt: next(answers))
    assert case[":case/consent"] is True and case[":case/loss-jpy"] == 0


def test_interactive_aborts_on_no_consent():
    try:
        intake.interactive(ask=lambda _prompt: "いいえ")
        assert False, "must abort when consent is refused"
    except SystemExit:
        pass


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test_intake.py")
    sys.exit(1 if failed else 0)
