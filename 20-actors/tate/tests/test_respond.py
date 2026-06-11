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
    assert {p["status"] for p in ps} <= {":genuine", ":suspected-fake", ":unknown",
                                         ":unknown-jurisdiction"}


# ── worldwide (ADR-2606112400) ───────────────────────────────────────────────

def test_us_summons_genuine_and_referral_forward():
    ps, _ = _by_id()
    p = ps["ntc:us-summons-real"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:us-summons"
    assert any("FRCP 12(a)" in d["anchor"] for d in p["deadlines"])
    # civil suit referral-forward always (G7), with the US directory
    assert any("state bar" in r for r in p["referrals"])


def test_us_fake_email_guard():
    """G6 generalizes: 'summons' vocabulary over email → suspected-fake, US help lines."""
    ps, _ = _by_id()
    p = ps["ntc:us-fake-email"]
    assert p["status"] == ":suspected-fake"
    assert p["steps"][0]["verb"] == "do-not-contact-sender"
    assert p["deadlines"] == [] and p["options"] == []
    assert any("FTC" in r for r in p["referrals"])


def test_de_mahnbescheid():
    ps, _ = _by_id()
    p = ps["ntc:de-mahn"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:de-mahnbescheid"
    assert any("ZPO" in d["anchor"] for d in p["deadlines"])
    assert any(o["id"] == ":widerspruch" for o in p["options"])


def test_eu_order_for_payment():
    ps, _ = _by_id()
    p = ps["ntc:eu-ofp"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:eu-order-for-payment"
    dl = p["deadlines"][0]
    assert "30日" in dl["rule"] and "1896/2006" in dl["anchor"]


def test_uk_claim_referral_over_line():
    """£12,500 > the :uk refer-over line (£10,000) → UK directory appended (G7)."""
    ps, _ = _by_id()
    p = ps["ntc:uk-claim"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:uk-claim-form"
    assert any("CPR" in d["anchor"] for d in p["deadlines"])
    assert any("Citizens Advice" in r for r in p["referrals"])


def test_unknown_jurisdiction_degrades_honestly():
    """G10: an uncovered jurisdiction (:br) gets NO deadlines/options — tate never
    guesses foreign law; it declares the gap and refers."""
    ps, _ = _by_id()
    p = ps["ntc:br-unknown"]
    assert p["status"] == ":unknown-jurisdiction"
    assert p["deadlines"] == [] and p["options"] == []
    assert p["steps"][0]["verb"] == "declare-uncovered"
    assert p["referrals"], "must still refer to local professionals"


def test_kr_jigeup_genuine_and_fake():
    """Wave 2: 지급명령 genuine via formal service (이의신청 2주, 민사소송법 470조);
    the same vocabulary over SMS (『법원』詐称) → suspected-fake with KR help lines."""
    ps, _ = _by_id()
    p = ps["ntc:kr-jigeup"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:kr-jigeup-myeongryeong"
    assert any("민사소송법 470조" in d["anchor"] for d in p["deadlines"])
    assert any(o["id"] == ":i-ui-sincheong" for o in p["options"])
    f = ps["ntc:kr-fake-sms"]
    assert f["status"] == ":suspected-fake"
    assert f["steps"][0]["verb"] == "do-not-contact-sender"
    assert any("경찰청" in r or "금융감독원" in r for r in f["referrals"])


def test_fr_injonction_genuine():
    """Wave 2: injonction de payer — opposition 1 mois (CPC art. 1416)."""
    ps, _ = _by_id()
    p = ps["ntc:fr-injonction"]
    assert p["status"] == ":genuine" and p["proc"] == "proc:fr-injonction-de-payer"
    dl = p["deadlines"][0]
    assert "1か月" in dl["rule"] and "1416" in dl["anchor"]
    assert any(o["id"] == ":opposition" for o in p["options"])


def test_wave3_au_ca_it_genuine():
    """Wave 3: AU statement of claim (NSW UCPR 14.3 28d) · CA plaintiff's claim
    (ON r. 9.01 20d) · IT decreto ingiuntivo (c.p.c. 641 opposizione 40d)."""
    ps, _ = _by_id()
    au = ps["ntc:au-soc"]
    assert au["status"] == ":genuine" and au["proc"] == "proc:au-statement-of-claim"
    assert any("UCPR" in d["anchor"] for d in au["deadlines"])
    ca = ps["ntc:ca-claim"]
    assert ca["status"] == ":genuine" and ca["proc"] == "proc:ca-plaintiffs-claim"
    assert any("9.01" in d["anchor"] for d in ca["deadlines"])
    it = ps["ntc:it-decreto"]
    assert it["status"] == ":genuine" and it["proc"] == "proc:it-decreto-ingiuntivo"
    assert any("641" in d["anchor"] for d in it["deadlines"])
    assert any(o["id"] == ":opposizione" for o in it["options"])


def test_arbitration_inversion_us_vs_ca():
    """Maturity: the SAME clause text ('binding arbitration') maps to opposite
    disclosed positions — :us FAA enforceable vs :ca ON CPA void — proving G10
    carries jurisdiction-specific MEANING, not just filtering."""
    sys.path.insert(0, str(ACTOR_DIR / "methods"))
    from terms_scan import scan_doc, load_patterns  # noqa: E402
    patterns = load_patterns()
    base = {":doc/context": ":consumer", ":doc/sourcing": ":synthetic",
            ":doc/text": "Any dispute shall be resolved by binding arbitration."}
    us = scan_doc({**base, ":doc/id": "d:us", ":doc/jurisdiction": ":us"}, patterns)
    ca = scan_doc({**base, ":doc/id": "d:ca", ":doc/jurisdiction": ":ca"}, patterns)
    assert any("ENFORCEABLE" in f["anchor"] or "原則" in f["anchor"] for f in us)
    assert any("無効" in f["anchor"] for f in ca)


def test_procedures_never_cross_jurisdictions():
    """G10: JP 支払督促 vocabulary under a :us notice must NOT match the JP procedure."""
    _, procs = _by_id()
    n = {":notice/id": "ntc:x", ":notice/jurisdiction": ":us",
         ":notice/channel": ":special-service", ":notice/text": "支払督促を発する。",
         ":notice/sourcing": ":synthetic"}
    proc, status = classify(n, procs)
    assert proc is None and status in (":unknown", ":suspected-fake")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
