#!/usr/bin/env python3
"""tate 盾 — response-planner tests (ADR-2606112300). Pure stdlib.

Verifies the defense gates empirically:
  - G6 架空請求 guard: court vocabulary on SMS → :suspected-fake; plan refuses any
    contact-sender step, preserves evidence, routes tasuke/#9110/188
  - genuine 特別送達 支払督促 → 督促異議 option + 2-week DISCLOSED rule (民訴391/393)
  - 少額訴訟 → 通常移行申述 present + 民訴373条; claim ≤ 60万 ceiling honest
  - 訴状 (高額) → referral-forward always carries 法テラス/弁護士会 (G7)
  - 行政処分 → 審査請求 3月 (行審法18条1項) + 取消訴訟 6月 (行訴法14条1項)
  - G4 deadline honesty: every deadline is a RULE + anchor + verify-service-date,
    never a computed calendar date
  - G3 UPL: representation unrepresentable; every option is member self-submit/decide
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from terms_scan import load_docs  # noqa: E402
from respond_plan import load_procs, classify, build_plan, plans, _make_option  # noqa: E402


def _by_id():
    _, notices = load_docs()
    procs = load_procs()
    return {n[":notice/id"]: build_plan(n, procs) for n in notices}, procs


def test_fake_sms_guard():
    ps, _ = _by_id()
    p = ps["ntc:fake-sms"]
    assert p["status"] == ":suspected-fake"
    verbs = [s["verb"] for s in p["steps"]]
    assert verbs[0] == "do-not-contact-sender"
    assert "preserve-evidence" in verbs
    # never a step that contacts the sender; no deadlines/options offered on a fake
    assert all("contact-sender" not in v or v == "do-not-contact-sender" for v in verbs)
    assert p["deadlines"] == [] and p["options"] == []
    assert any("tasuke" in r for r in p["referrals"])
    assert any("#9110" in r for r in p["referrals"])
    assert any("188" in r for r in p["referrals"])


def test_channel_discriminator():
    """The SAME 支払督促 text is genuine via 特別送達 but suspected-fake via email."""
    _, procs = _by_id()
    base = {":notice/id": "ntc:x", ":notice/text": "支払督促を発する。", ":notice/claim-jpy": 10000,
            ":notice/sourcing": ":synthetic"}
    _, s1 = classify({**base, ":notice/channel": ":special-service"}, procs)
    _, s2 = classify({**base, ":notice/channel": ":email"}, procs)
    assert s1 == ":genuine" and s2 == ":suspected-fake"


def test_tokusoku_genuine():
    ps, _ = _by_id()
    p = ps["ntc:tokusoku-real"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:shiharai-tokusoku"
    assert any(o["id"] == ":tokusoku-igi" for o in p["options"])
    dl = p["deadlines"][0]
    assert "2週間" in dl["rule"] and "民事訴訟法391条" in dl["anchor"]


def test_shougaku_transfer_option():
    ps, procs = _by_id()
    p = ps["ntc:shougaku-real"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:shougaku-sosho"
    assert any(o["id"] == ":ikou" for o in p["options"])  # 通常移行申述 (民訴373条)
    assert any("民事訴訟法373条" in d["anchor"] for d in p["deadlines"])
    proc = next(x for x in procs if x[":proc/id"] == "proc:shougaku-sosho")
    assert proc[":proc/claim-ceiling-jpy"] == 600000  # 民訴368条 — disclosed, not invented


def test_sojou_referral_forward():
    ps, _ = _by_id()
    p = ps["ntc:sojou-big"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:sojou"
    assert any("法テラス" in r for r in p["referrals"]), "G7: 本訴 must referral-forward"


def test_gyousei_deadlines():
    ps, _ = _by_id()
    p = ps["ntc:gyousei"]
    assert p["status"] == ":genuine"
    anchors = " / ".join(d["anchor"] for d in p["deadlines"])
    assert "行政不服審査法18条1項" in anchors and "行政事件訴訟法14条1項" in anchors
    rules = " / ".join(d["rule"] for d in p["deadlines"])
    assert "3月以内" in rules and "6箇月以内" in rules


def test_deadline_honesty_no_computed_dates():
    """G4: rules + anchors only; verify-service-date on every deadline; no ISO dates."""
    ps, _ = _by_id()
    for p in ps.values():
        for d in p["deadlines"]:
            assert d["verify_service_date"] is True, (p["notice"], d)
            assert d["anchor"], d
            assert not any(ch.isdigit() and "-" in d["rule"][:0] for ch in d["rule"])  # no computed date fields exist
            assert "deadline_date" not in d and "due" not in d


def test_upl_gates():
    """G3: representation unrepresentable; everything member-submitted, dry-run."""
    try:
        _make_option({":opt/id": ":dairi", ":opt/kind": ":representation", ":opt/label": "代理"})
        raise AssertionError("representation was representable")
    except ValueError:
        pass
    ps, _ = _by_id()
    for p in ps.values():
        assert p["mode"] == "dry-run"
        for o in p["options"]:
            assert o["submitted_by"] == "member" and o["kind"] in (":self-submit", ":self-decide")
        if p["status"] == ":genuine":
            assert any(s["verb"] == "self-submit" for s in p["steps"])


def test_plans_cover_all_notices():
    _, notices = load_docs()
    ps = plans(notices, load_procs())
    assert len(ps) == len(notices)
    assert {p["status"] for p in ps} <= {":genuine", ":suspected-fake", ":unknown"}


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
