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
    """G10: an uncovered jurisdiction (:cl — fixture lineage :br → :mx → :ar →
    :cl as coverage grows) gets NO deadlines/options — tate never guesses foreign law."""
    ps, _ = _by_id()
    p = ps["ntc:cl-unknown"]
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


def test_arbitration_inversion_us_vs_ca_vs_in():
    """Maturity: the SAME clause text ('binding arbitration') maps to THREE distinct
    disclosed positions — :us FAA enforceable · :ca ON CPA void · :in consumer-fora
    jurisdiction not ousted — proving G10 carries jurisdiction-specific MEANING."""
    sys.path.insert(0, str(ACTOR_DIR / "methods"))
    from terms_scan import scan_doc, load_patterns  # noqa: E402
    patterns = load_patterns()
    base = {":doc/context": ":consumer", ":doc/sourcing": ":synthetic",
            ":doc/text": "Any dispute shall be resolved by binding arbitration."}
    us = scan_doc({**base, ":doc/id": "d:us", ":doc/jurisdiction": ":us"}, patterns)
    ca = scan_doc({**base, ":doc/id": "d:ca", ":doc/jurisdiction": ":ca"}, patterns)
    in_ = scan_doc({**base, ":doc/id": "d:in", ":doc/jurisdiction": ":in"}, patterns)
    assert any("ENFORCEABLE" in f["anchor"] or "原則" in f["anchor"] for f in us)
    assert any("無効" in f["anchor"] for f in ca)
    assert any("排除されない" in f["anchor"] for f in in_)


def test_wave5_tw_sg_in_genuine():
    """Wave 5: TW 支付命令 (異議 20日不変期間, 台湾民訴516條) · SG SCT (本人手続,
    弁護士代理禁止) · IN summons (written statement 30d, CPC O.VIII r.1)."""
    ps, _ = _by_id()
    tw = ps["ntc:tw-payment"]
    assert tw["status"] == ":genuine" and tw["proc"] == "proc:tw-payment-order"
    assert any("516條" in d["anchor"] for d in tw["deadlines"])
    sg = ps["ntc:sg-sct"]
    assert sg["status"] == ":genuine" and sg["proc"] == "proc:sg-sct"
    assert any("弁護士代理は禁止" in d["rule"] for d in sg["deadlines"])
    ind = ps["ntc:in-summons"]
    assert ind["status"] == ":genuine" and ind["proc"] == "proc:in-summons"
    assert any("Order VIII Rule 1" in d["anchor"] for d in ind["deadlines"])


def test_digital_channel_never_genuine():
    """G6 hardening (wave 5): for EVERY procedure in the registry, its own trigger
    vocabulary arriving via SMS or email classifies :suspected-fake — including
    mail-only procedures (行政処分 by SMS was previously a hole). Parametric: new
    procedures are covered automatically."""
    procs = load_procs()
    for p in procs:
        for ch in (":sms", ":email"):
            if ch in p.get(":proc/genuine-channels", []):
                continue  # explicitly declared digital channel would be a deliberate choice
            n = {":notice/id": "ntc:synth", ":notice/jurisdiction": p[":proc/jurisdiction"],
                 ":notice/channel": ch, ":notice/text": p[":proc/trigger-keywords"][0],
                 ":notice/sourcing": ":synthetic"}
            _, status = classify(n, procs)
            assert status == ":suspected-fake", (p[":proc/id"], ch, status)


def test_wave4_es_nl_br_genuine():
    """Wave 4: ES proceso monitorio (LEC 815.1 20 días hábiles) · NL dagvaarding
    (Rv 111 roldatum) · BR citação via correio (CPC 335 contestação 15 dias úteis —
    :mail IS a genuine channel in Brazil, unlike JP/DE)."""
    ps, _ = _by_id()
    es = ps["ntc:es-monitorio"]
    assert es["status"] == ":genuine" and es["proc"] == "proc:es-monitorio"
    assert any("815.1" in d["anchor"] for d in es["deadlines"])
    nl = ps["ntc:nl-dagvaarding"]
    assert nl["status"] == ":genuine" and nl["proc"] == "proc:nl-dagvaarding"
    assert any("Rv art. 111" in d["anchor"] for d in nl["deadlines"])
    br = ps["ntc:br-citacao"]
    assert br["status"] == ":genuine" and br["proc"] == "proc:br-citacao"
    assert br["channel"] == ":mail"  # citação pelo correio is the Brazilian default
    assert any("335" in d["anchor"] for d in br["deadlines"])
    assert any("dias úteis" in d["rule"] for d in br["deadlines"])  # business-day honesty


def test_wave6_cn_genuine_and_script_separation():
    """Wave 6: CN 支付令 (15日 清偿/书面异议, 民事诉讼法 督促程序); simplified-script
    patterns are a separate registry entry from :tw traditional ones (G10)."""
    ps, procs = _by_id()
    cn = ps["ntc:cn-zhifuling"]
    assert cn["status"] == ":genuine" and cn["proc"] == "proc:cn-zhifuling"
    assert any("15日" in d["rule"] for d in cn["deadlines"])
    # 支付令 (:cn) and 支付命令 (:tw) resolve to their own procedures
    tw = ps["ntc:tw-payment"]
    assert tw["proc"] == "proc:tw-payment-order" and cn["proc"] != tw["proc"]


def test_us_state_sub_jurisdiction():
    """Wave 6: a :us notice with a known state gets the DISCLOSED state rule appended
    (CA: CCP §412.20 30d + small-claims ceiling); a stateless :us notice gets the
    honest 州不明 entry — never a guessed state deadline (G10)."""
    ps, _ = _by_id()
    ca = ps["ntc:us-summons-ca"]
    assert ca["status"] == ":genuine"
    state_dls = [d for d in ca["deadlines"] if d["label"].startswith("州規則")]
    assert len(state_dls) == 1 and "California" in state_dls[0]["label"]
    assert "412.20" in state_dls[0]["anchor"] and "$12,500" in state_dls[0]["rule"]
    stateless = ps["ntc:us-summons-real"]
    honest = [d for d in stateless["deadlines"] if d["label"] == "州規則 (州不明)"]
    assert len(honest) == 1 and "提示しない" in honest[0]["rule"]


def test_wave7_pl_se_genuine():
    """Wave 7: PL nakaz zapłaty (sprzeciw 2週間, KPC 480²/505) · SE
    betalningsföreläggande (Kronofogden — bestrida inom förklaringstiden)."""
    ps, _ = _by_id()
    pl = ps["ntc:pl-nakaz"]
    assert pl["status"] == ":genuine" and pl["proc"] == "proc:pl-nakaz-zaplaty"
    assert any("480²" in d["anchor"] for d in pl["deadlines"])
    se = ps["ntc:se-bf"]
    assert se["status"] == ":genuine" and se["proc"] == "proc:se-betalningsforelaggande"
    assert any("1990:746" in d["anchor"] for d in se["deadlines"])
    assert any(o["id"] == ":bestrida" for o in se["options"])


def test_currency_mismatch_refers_conservatively():
    """Wave 7 maturity: a foreign-currency claim can't be sized against the
    jurisdiction's refer-over line → conservative referral-forward, with the reason
    stated. Same-currency small claims stay un-referred."""
    _, procs = _by_id()
    base = {":notice/id": "ntc:cur", ":notice/jurisdiction": ":us",
            ":notice/channel": ":personal-service",
            ":notice/text": "small claims notice", ":notice/sourcing": ":synthetic"}
    # small USD claim on a US small-claims proc → no jurisdiction directory appended
    same = build_plan({**base, ":notice/claim-amount": 500,
                       ":notice/claim-currency": "USD"}, procs)
    assert not any("state bar" in r for r in same["referrals"])
    # same small amount in EUR → incomparable → conservative referral with reason
    mismatch = build_plan({**base, ":notice/claim-amount": 500,
                           ":notice/claim-currency": "EUR"}, procs)
    assert any("外貨建て" in r for r in mismatch["referrals"])
    assert any("state bar" in r for r in mismatch["referrals"])


def test_wave8_at_pt_genuine():
    """Wave 8: AT Zahlungsbefehl (Einspruch 4週間, ZPO §248) · PT injunção
    (oposição 15日, DL 269/98)."""
    ps, _ = _by_id()
    at = ps["ntc:at-zb"]
    assert at["status"] == ":genuine" and at["proc"] == "proc:at-zahlungsbefehl"
    assert any("§248" in d["anchor"] for d in at["deadlines"])
    pt = ps["ntc:pt-injuncao"]
    assert pt["status"] == ":genuine" and pt["proc"] == "proc:pt-injuncao"
    assert any("269/98" in d["anchor"] for d in pt["deadlines"])


def test_wave8_labor_track():
    """Wave 8: the :labor specialty track. Defensive-of-own-employment responses:
    JP 解雇 (労基法22条 理由証明書 + 115条 賃金時効) · DE Kündigung (KSchG §4
    3-WEEK Kündigungsschutzklage + BGB §623 Schriftform — 電子形式無効) · UK
    dismissal (ACAS EC 必須 + ET 3か月−1日)."""
    ps, procs = _by_id()
    jp = ps["ntc:jp-kaiko"]
    assert jp["status"] == ":genuine" and jp["proc"] == "proc:jp-kaiko"
    assert any("労働基準法22条" in d["anchor"] for d in jp["deadlines"])
    de = ps["ntc:de-kuendigung"]
    assert de["status"] == ":genuine" and de["proc"] == "proc:de-kuendigung"
    assert any("3週間" in d["rule"] and "KSchG" in d["anchor"] for d in de["deadlines"])
    assert any("BGB §623" in d["anchor"] for d in de["deadlines"])
    uk = ps["ntc:uk-dismissal"]
    assert uk["status"] == ":genuine" and uk["proc"] == "proc:uk-dismissal"
    assert any("ACAS" in d["rule"] for d in uk["deadlines"])
    # all three carry :proc/track :labor in the registry
    by_id = {p[":proc/id"]: p for p in procs}
    for pid in ("proc:jp-kaiko", "proc:de-kuendigung", "proc:uk-dismissal"):
        assert by_id[pid][":proc/track"] == ":labor"
    # and an email-only Kündigung is suspected-fake (BGB §623 形式無効と整合)
    n = {":notice/id": "ntc:x", ":notice/jurisdiction": ":de", ":notice/channel": ":email",
         ":notice/text": "Kündigung Ihres Arbeitsverhältnisses", ":notice/sourcing": ":synthetic"}
    _, status = classify(n, procs)
    assert status == ":suspected-fake"


def test_wave9_housing_track():
    """Wave 9: the :housing track (jp/de/uk/us). Universal member-protective
    invariant: EVERY :housing procedure carries the no-self-help option — eviction
    happens only by court order; 鍵交換/追い出しは違法."""
    ps, procs = _by_id()
    jp = ps["ntc:jp-kaiyaku-m"]
    assert jp["status"] == ":genuine" and jp["proc"] == "proc:jp-chintai-kaiyaku"
    assert any("借地借家法27条" in d["anchor"] for d in jp["deadlines"])
    assert any("退去義務は生じない" in d["rule"] for d in jp["deadlines"])
    de = ps["ntc:de-miet"]
    assert de["status"] == ":genuine" and de["proc"] == "proc:de-mietkuendigung"
    assert any("§574" in d["anchor"] for d in de["deadlines"])
    uk = ps["ntc:uk-s21"]
    assert uk["status"] == ":genuine" and uk["proc"] == "proc:uk-s21-s8"
    assert any("Protection from Eviction Act 1977" in d["anchor"] for d in uk["deadlines"])
    us = ps["ntc:us-eviction-ca"]
    assert us["status"] == ":genuine" and us["proc"] == "proc:us-eviction"
    assert any("§1161" in d["anchor"] for d in us["deadlines"])
    assert any(d["label"].startswith("州規則 (California") for d in us["deadlines"])
    # parametric: every :housing proc has the no-self-help protection option
    for p in procs:
        if p.get(":proc/track") == ":housing":
            ids = [o[":opt/id"] for o in p[":proc/options"]]
            assert ":no-self-help-protection" in ids, p[":proc/id"]


def test_de_kuendigung_disambiguation():
    """Wave 9: the :de Kündigung collision is resolved by specific triggers —
    Arbeitsverhältnis → labor proc, Mietverhältnis → housing proc, and a bare
    'Kündigung' with no context degrades honestly to :unknown (never guesses
    which 3-week/2-month regime applies)."""
    _, procs = _by_id()
    base = {":notice/id": "ntc:x", ":notice/jurisdiction": ":de",
            ":notice/channel": ":mail", ":notice/sourcing": ":synthetic"}
    p1, s1 = classify({**base, ":notice/text": "Kündigung Ihres Arbeitsverhältnisses"}, procs)
    assert s1 == ":genuine" and p1[":proc/id"] == "proc:de-kuendigung"
    p2, s2 = classify({**base, ":notice/text": "Kündigung des Mietverhältnisses"}, procs)
    assert s2 == ":genuine" and p2[":proc/id"] == "proc:de-mietkuendigung"
    p3, s3 = classify({**base, ":notice/text": "Kündigung"}, procs)
    assert p3 is None and s3 == ":unknown"


def test_wave10_enforcement_track():
    """Wave 10: the :enforcement track. Universal invariant: EVERY :enforcement
    procedure carries at least one :opt/protective option — 差押えにも法定の保護
    範囲がある (民執152条 3/4 · CCPA §1673 25% · ZPO §850k P-Konto); claiming a
    lawful exemption is a RIGHT, not debt evasion (N3 line preserved)."""
    ps, procs = _by_id()
    jp = ps["ntc:jp-sashiosae"]
    assert jp["status"] == ":genuine" and jp["proc"] == "proc:jp-sashiosae"
    assert any("民事執行法152条" in d["anchor"] for d in jp["deadlines"])
    assert any("法テラス" in r for r in jp["referrals"])  # ¥600,001 > refer-over line
    us = ps["ntc:us-garnish"]
    assert us["status"] == ":genuine" and us["proc"] == "proc:us-garnishment"
    assert any("§1673" in d["anchor"] for d in us["deadlines"])
    de = ps["ntc:de-pfaendung"]
    assert de["status"] == ":genuine" and de["proc"] == "proc:de-kontopfaendung"
    assert any("§850k" in d["anchor"] for d in de["deadlines"])
    # parametric: every :enforcement proc has a protective option
    for p in procs:
        if p.get(":proc/track") == ":enforcement":
            assert any(o.get(":opt/protective") is True for o in p[":proc/options"]), \
                p[":proc/id"]


def test_sashiosae_sms_scam_guard():
    """Wave 10: the classic 『差押え最終通告』 SMS scam — 差押 vocabulary over SMS
    with no procedure match → suspected-fake, do-not-contact-sender."""
    _, procs = _by_id()
    n = {":notice/id": "ntc:x", ":notice/jurisdiction": ":jp", ":notice/channel": ":sms",
         ":notice/text": "【差押え最終通告】本日中にご連絡なき場合、給与の差押えを執行します。",
         ":notice/sourcing": ":synthetic"}
    proc, status = classify(n, procs)
    assert status == ":suspected-fake"


def test_wave11_insolvency_track():
    """Wave 11: the :insolvency track (creditor-side defense — protecting the
    member's OWN prepaid/deposit claims when a counterparty fails). Every
    :insolvency proc carries a :opt/protective claim-filing option."""
    ps, procs = _by_id()
    jp = ps["ntc:jp-hasan"]
    assert jp["status"] == ":genuine" and jp["proc"] == "proc:jp-hasan-tsuchi"
    assert any("破産法31条・111条" in d["anchor"] for d in jp["deadlines"])
    us = ps["ntc:us-bk"]
    assert us["status"] == ":genuine" and us["proc"] == "proc:us-bankruptcy-notice"
    assert any("3002" in d["anchor"] for d in us["deadlines"])
    de = ps["ntc:de-inso"]
    assert de["status"] == ":genuine" and de["proc"] == "proc:de-insolvenz"
    assert any("§174" in d["anchor"] for d in de["deadlines"])
    for p in procs:
        if p.get(":proc/track") == ":insolvency":
            assert any(o.get(":opt/protective") is True for o in p[":proc/options"]), \
                p[":proc/id"]


def test_wave11_ie_ch():
    """Wave 11: IE civil summons (small claims ≤€2,000 Registrar) · CH Zahlungsbefehl
    (Rechtsvorschlag 10日 — SchKG 74; same word as :at Zahlungsbefehl resolves to a
    DIFFERENT procedure per jurisdiction, G10)."""
    ps, _ = _by_id()
    ie = ps["ntc:ie-summons"]
    assert ie["status"] == ":genuine" and ie["proc"] == "proc:ie-civil-summons"
    ch = ps["ntc:ch-zb"]
    assert ch["status"] == ":genuine" and ch["proc"] == "proc:ch-zahlungsbefehl"
    assert any("10日" in d["rule"] and "SchKG" in d["anchor"] for d in ch["deadlines"])
    assert any(o["id"] == ":register-cleanup" for o in ch["options"])  # SchKG 8a 信用保護
    at = ps["ntc:at-zb"]
    assert at["proc"] == "proc:at-zahlungsbefehl" and at["proc"] != ch["proc"]


def test_wave12_family_track():
    """Wave 12: the :family track. Universal invariant: EVERY :family procedure
    routes to kokoro 心 (Wellbecoming support) alongside the legal options — and
    the :de Anwaltszwang honesty (tate can't template what only a lawyer may file)
    is disclosed rather than papered over."""
    ps, procs = _by_id()
    jp = ps["ntc:jp-chotei"]
    assert jp["status"] == ":genuine" and jp["proc"] == "proc:jp-kaji-chotei"
    assert any("家事事件手続法51条" in d["anchor"] for d in jp["deadlines"])
    us = ps["ntc:us-divorce"]
    assert us["status"] == ":genuine" and us["proc"] == "proc:us-divorce-petition"
    assert any("30日" in d["rule"] for d in us["deadlines"])
    de = ps["ntc:de-scheidung"]
    assert de["status"] == ":genuine" and de["proc"] == "proc:de-scheidungsantrag"
    assert any("FamFG §114" in d["anchor"] for d in de["deadlines"])
    assert any(o["id"] == ":vkh" for o in de["options"])  # VKH 申請は本人可 (protective)
    # parametric: every :family proc routes to kokoro 心
    for p in procs:
        if p.get(":proc/track") == ":family":
            assert any("kokoro 心" in r for r in p.get(":proc/refer-when", [])), p[":proc/id"]


def test_wave12_dk_fi():
    """Wave 12: DK betalingspåkrav (indsigelse ~14日, retsplejeloven kap. 44a) ·
    FI haastehakemus (vastaus — 無応答は yksipuolinen tuomio)."""
    ps, _ = _by_id()
    dk = ps["ntc:dk-bp"]
    assert dk["status"] == ":genuine" and dk["proc"] == "proc:dk-betalingspaakrav"
    assert any("44a" in d["anchor"] for d in dk["deadlines"])
    fi = ps["ntc:fi-haaste"]
    assert fi["status"] == ":genuine" and fi["proc"] == "proc:fi-haastehakemus"
    assert any("yksipuolinen tuomio" in d["rule"] for d in fi["deadlines"])


def test_wave13_track_expansion_kr_fr():
    """Wave 13: :labor and :housing expand beyond jp/us/de/uk — KR 부당해고 구제신청
    3개월 (근로기준법28조) + 서면통지 27조 (DE §623 と同型) · KR 갱신요구권
    (주택임대차보호법 6조의3) · FR prud'hommes 12 mois (L.1471-1) + précision 15日 ·
    FR congé du bailleur 6か月+形式 (loi 89-462 art.15) + trêve hivernale."""
    ps, procs = _by_id()
    kr_l = ps["ntc:kr-haego"]
    assert kr_l["status"] == ":genuine" and kr_l["proc"] == "proc:kr-budang-haego"
    assert any("근로기준법 28조" in d["anchor"] for d in kr_l["deadlines"])
    assert any("근로기준법 27조" in d["anchor"] for d in kr_l["deadlines"])
    kr_h = ps["ntc:kr-gaengsin"]
    assert kr_h["status"] == ":genuine" and kr_h["proc"] == "proc:kr-gaengsin-geojeol"
    assert any("6조의3" in d["anchor"] for d in kr_h["deadlines"])
    fr_l = ps["ntc:fr-licenciement"]
    assert fr_l["status"] == ":genuine" and fr_l["proc"] == "proc:fr-licenciement"
    assert any("L.1471-1" in d["anchor"] for d in fr_l["deadlines"])
    fr_h = ps["ntc:fr-conge"]
    assert fr_h["status"] == ":genuine" and fr_h["proc"] == "proc:fr-conge-bailleur"
    assert any("trêve hivernale" in d["rule"] for d in fr_h["deadlines"])
    # the housing no-self-help invariant holds automatically for the new procs
    # (test_wave9_housing_track is parametric) — here we just confirm track tags
    by_id = {p[":proc/id"]: p for p in procs}
    assert by_id["proc:kr-budang-haego"][":proc/track"] == ":labor"
    assert by_id["proc:kr-gaengsin-geojeol"][":proc/track"] == ":housing"
    assert by_id["proc:fr-licenciement"][":proc/track"] == ":labor"
    assert by_id["proc:fr-conge-bailleur"][":proc/track"] == ":housing"


def test_wave13_no_forliksraadet():
    """Wave 13: :no — Norway's mandatory conciliation council (forliksrådet,
    本人手続前提) with fraværsdom risk on silence (tvisteloven §6-3/6-6)."""
    ps, _ = _by_id()
    no = ps["ntc:no-forlik"]
    assert no["status"] == ":genuine" and no["proc"] == "proc:no-forliksklage"
    assert any("tvisteloven" in d["anchor"] for d in no["deadlines"])
    assert any("fraværsdom" in d["rule"] for d in no["deadlines"])


def test_wave14_matrix_fill_and_mx():
    """Wave 14: matrix empty-cell fills — :us labor (at-will honesty + EEOC 180/300d
    private-suit precondition) · :uk enforcement (7 clear days + exempt goods) ·
    :fr enforcement (saisie contestation 1 mois + SBI auto-protection, the French
    P-Konto) — and :mx covered (fixture moved to :ar)."""
    ps, _ = _by_id()
    us = ps["ntc:us-term"]
    assert us["status"] == ":genuine" and us["proc"] == "proc:us-termination"
    assert any("at-will" in d["rule"] and "§2000e-5" in d["anchor"] for d in us["deadlines"])
    uk = ps["ntc:uk-noe"]
    assert uk["status"] == ":genuine" and uk["proc"] == "proc:uk-notice-of-enforcement"
    assert any("7 clear days" in d["rule"] for d in uk["deadlines"])
    assert any(o["id"] == ":exempt-goods" for o in uk["options"])
    fr = ps["ntc:fr-saisie"]
    assert fr["status"] == ":genuine" and fr["proc"] == "proc:fr-saisie-attribution"
    assert any("R.162-2" in d["anchor"] for d in fr["deadlines"])  # SBI 自動保護
    mx = ps["ntc:mx-empl"]
    assert mx["status"] == ":genuine" and mx["proc"] == "proc:mx-emplazamiento"
    assert any("entidad federativa" in d["rule"] for d in mx["deadlines"])  # 州差の開示


def test_wave15_insolvency_family_expansion_and_be():
    """Wave 15: :insolvency expands to :fr (déclaration de créance — BODACC 公告
    2か月, forclusion 失権 L.622-24) and :uk (proof of debt, IR 2016 Pt 14);
    :family expands to :uk (no-fault AoS 14日, DDSA 2020 — kokoro invariant
    auto-extends); :be covered (citation, juge de paix ≤€5,000 本人可)."""
    ps, _ = _by_id()
    fr = ps["ntc:fr-creance"]
    assert fr["status"] == ":genuine" and fr["proc"] == "proc:fr-declaration-creance"
    assert any("L.622-24" in d["anchor"] and "forclusion" in d["rule"] for d in fr["deadlines"])
    uk_i = ps["ntc:uk-pod"]
    assert uk_i["status"] == ":genuine" and uk_i["proc"] == "proc:uk-proof-of-debt"
    assert any("Rules 2016" in d["anchor"] for d in uk_i["deadlines"])
    uk_f = ps["ntc:uk-divorce"]
    assert uk_f["status"] == ":genuine" and uk_f["proc"] == "proc:uk-divorce-response"
    assert any("14日" in d["rule"] and "2020" in d["anchor"] for d in uk_f["deadlines"])
    be = ps["ntc:be-citation"]
    assert be["status"] == ":genuine" and be["proc"] == "proc:be-citation"
    assert any("最低8日" in d["rule"] for d in be["deadlines"])


def test_wave16_ar_and_kr_family():
    """Wave 16: :ar covered (traslado contestación 15 días hábiles CPCCN 338/356;
    botón de baja Res.424/2020 → kaiyaku); :family expands to :kr (조정전치주의
    가사소송법 50조 — kokoro invariant auto-extends)."""
    ps, _ = _by_id()
    ar = ps["ntc:ar-traslado"]
    assert ar["status"] == ":genuine" and ar["proc"] == "proc:ar-traslado"
    assert any("CPCCN" in d["anchor"] and "días hábiles" in d["rule"] for d in ar["deadlines"])
    kr = ps["ntc:kr-ihon"]
    assert kr["status"] == ":genuine" and kr["proc"] == "proc:kr-ihon-jojeong"
    assert any("조정전치" in d["rule"] or "조정전치" in d["anchor"] for d in kr["deadlines"])


def test_wave17_au_ca_labor_housing():
    """Wave 17: :au FWC unfair dismissal **21日** (FW Act s.394) · :au NSW
    termination notice (NCAT order までは退去不要) · :ca ON ESA vs common law
    (severance サイン前警告 = protective) · :ca N12 (bad-faith → T5, LTB+Sheriff
    のみが執行可) — labor/housing invariants auto-extend."""
    ps, procs = _by_id()
    au_l = ps["ntc:au-dismissal"]
    assert au_l["status"] == ":genuine" and au_l["proc"] == "proc:au-unfair-dismissal"
    assert any("21日" in d["rule"] and "s.394" in d["anchor"] for d in au_l["deadlines"])
    au_h = ps["ntc:au-termnotice"]
    assert au_h["status"] == ":genuine" and au_h["proc"] == "proc:au-termination-notice"
    assert any("NCAT" in d["rule"] for d in au_h["deadlines"])
    ca_l = ps["ntc:ca-dismissal"]
    assert ca_l["status"] == ":genuine" and ca_l["proc"] == "proc:ca-dismissal"
    assert any("common law" in d["rule"] for d in ca_l["deadlines"])
    ca_h = ps["ntc:ca-n12"]
    assert ca_h["status"] == ":genuine" and ca_h["proc"] == "proc:ca-n12"
    assert any("bad faith" in d["rule"] or "T5" in d["rule"] for d in ca_h["deadlines"])


def test_court_vocabulary_derived():
    """Wave 17 maturity: the fake-guard vocabulary is DERIVED from the registry —
    every procedure trigger keyword is automatically a trip-wire (new procedures are
    scam-guarded the moment they land), plus the curated generics."""
    from respond_plan import court_vocabulary, CURATED_TRIPWIRES
    procs = load_procs()
    vocab = set(court_vocabulary(procs))
    for p in procs:
        for k in p[":proc/trigger-keywords"]:
            assert k in vocab, (p[":proc/id"], k)
    assert set(CURATED_TRIPWIRES) <= vocab
    # and the derived vocabulary actually guards: an :au scam SMS using the FWC
    # trigger words is suspected-fake
    n = {":notice/id": "ntc:x", ":notice/jurisdiction": ":au", ":notice/channel": ":sms",
         ":notice/text": "URGENT: unfair dismissal compensation owed to you, call now",
         ":notice/sourcing": ":synthetic"}
    _, status = classify(n, procs)
    assert status == ":suspected-fake"


def test_wave18_kr_enforcement_fr_family():
    """Wave 18: :kr 압류 (급여 1/2 + 월185만원 압류금지 민사집행법246조 — 5管轄目の
    差押え保護, protective invariant auto) · :fr assignation en divorce (avocat
    obligatoire を正直開示 + AJ 本人申請; kokoro invariant auto)."""
    ps, _ = _by_id()
    kr = ps["ntc:kr-apnyu"]
    assert kr["status"] == ":genuine" and kr["proc"] == "proc:kr-apnyu"
    assert any("246조" in d["anchor"] for d in kr["deadlines"])
    fr = ps["ntc:fr-divorce"]
    assert fr["status"] == ":genuine" and fr["proc"] == "proc:fr-divorce-assignation"
    assert any("avocat" in d["rule"] for d in fr["deadlines"])
    assert any(o["id"] == ":aj" for o in fr["options"])


def test_critical_deadlines_surface_first():
    """Wave 18 maturity: catastrophic-if-missed deadlines (:dl/critical — KSchG
    3週間/解雇有効擬制, CH 10日, AU 21日, FR forclusion, KR 3개월, JP 督促異議)
    ALWAYS sort to the top of the plan so the member cannot miss them."""
    ps, procs = _by_id()
    for nid, proc_id in [("ntc:de-kuendigung", "proc:de-kuendigung"),
                         ("ntc:ch-zb", "proc:ch-zahlungsbefehl"),
                         ("ntc:au-dismissal", "proc:au-unfair-dismissal"),
                         ("ntc:fr-creance", "proc:fr-declaration-creance"),
                         ("ntc:kr-haego", "proc:kr-budang-haego"),
                         ("ntc:tokusoku-real", "proc:shiharai-tokusoku")]:
        p = ps[nid]
        assert p["proc"] == proc_id
        assert p["deadlines"][0]["critical"] is True, nid
    # multi-rule proc: the critical rule beats registry order when it is not first
    # (registry lint: critical is boolean-only)
    for p in procs:
        for dl in p[":proc/deadline-rules"]:
            assert dl.get(":dl/critical") in (None, True), (p[":proc/id"], dl)


def test_wave19_kr_insolvency_au_family():
    """Wave 19: :kr 채권신고 (실권 리스ク, 채무자회생법 — insolvency 6管轄) ·
    :au response to divorce 28日 + property settlement 12か月の別期限警告
    (family 7管轄; kokoro auto)."""
    ps, _ = _by_id()
    kr = ps["ntc:kr-singo"]
    assert kr["status"] == ":genuine" and kr["proc"] == "proc:kr-chaegwon-singo"
    assert any("실권" in d["rule"] for d in kr["deadlines"])
    au = ps["ntc:au-divorce"]
    assert au["status"] == ":genuine" and au["proc"] == "proc:au-divorce-response"
    assert any("28日" in d["rule"] for d in au["deadlines"])
    assert any("12か月" in o["label"] for o in au["options"])  # property の別期限


def test_universal_protective_invariant():
    """Wave 19 maturity: EVERY non-civil procedure carries ≥1 :opt/protective
    option — the per-track invariants (no-self-help / exemption / claim-filing /
    defensive response) unify into one meta-invariant: tate never ships a
    specialty-track procedure without a member-protecting move."""
    _, procs = _by_id()
    for p in procs:
        if p.get(":proc/track", ":civil") == ":civil":
            continue
        assert any(o.get(":opt/protective") is True for o in p[":proc/options"]), \
            p[":proc/id"]


def test_wave20_enforcement_au_ca_and_nz():
    """Wave 20: 賃金差押え保護が7管轄に (:au protected amount NSW CPA ss.119/122 ·
    :ca ON Wages Act s.7 80%差押禁止); :nz Disputes Tribunal — **email が宣言された
    genuine channel である初の管轄** (declared-digital は G6 ガードの例外として
    registry が意図的に選ぶ)."""
    ps, _ = _by_id()
    au = ps["ntc:au-garnishee"]
    assert au["status"] == ":genuine" and au["proc"] == "proc:au-garnishee"
    assert any("ss.119" in d["anchor"] for d in au["deadlines"])
    ca = ps["ntc:ca-garnish"]
    assert ca["status"] == ":genuine" and ca["proc"] == "proc:ca-garnishment"
    assert any("80%" in d["rule"] for d in ca["deadlines"])
    nz = ps["ntc:nz-dt"]
    assert nz["status"] == ":genuine" and nz["proc"] == "proc:nz-disputes-tribunal"
    assert nz["channel"] == ":email"  # declared digital channel — genuine by registry choice
    assert any("弁護士代理は法律で原則排除" in d["rule"] or "s.38" in d["anchor"]
               for d in nz["deadlines"])


def test_wave21_it_es_labor_critical():
    """Wave 21: civil-only 行の解消開始 — :it impugnazione **60 giorni** (L.604/1966
    art.6, その後180日提訴) · :es demanda por despido **20 días hábiles** (ET 59.3 —
    欧州最短級, caducidad); both critical → plan 先頭; finiquito/『no conforme』
    警告 = protective."""
    ps, _ = _by_id()
    it = ps["ntc:it-licenziamento"]
    assert it["status"] == ":genuine" and it["proc"] == "proc:it-licenziamento"
    assert it["deadlines"][0]["critical"] is True
    assert "60日" in it["deadlines"][0]["rule"]
    es = ps["ntc:es-despido"]
    assert es["status"] == ":genuine" and es["proc"] == "proc:es-despido"
    assert es["deadlines"][0]["critical"] is True
    assert "20日" in es["deadlines"][0]["rule"] and "caducidad" in es["deadlines"][0]["rule"]


def test_wave22_br_tw_labor():
    """Wave 22: :br dispensa (verbas rescisórias TRCT サイン前点検 protective +
    時効2年/遡及5年 CF art.7 XXIX + CLT 477 10日支払) · :tw 資遣/解僱 (勞基法11/12條
    法定事由 + 勞資爭議調解 + 非自願離職證明 = 失業給付の鍵)."""
    ps, _ = _by_id()
    br = ps["ntc:br-dispensa"]
    assert br["status"] == ":genuine" and br["proc"] == "proc:br-dispensa"
    assert any("XXIX" in d["anchor"] for d in br["deadlines"])
    tw = ps["ntc:tw-zigian"]
    assert tw["status"] == ":genuine" and tw["proc"] == "proc:tw-jiegu"
    assert any("11條" in d["anchor"] for d in tw["deadlines"])
    assert any(o["id"] == ":feiziyuan" for o in tw["options"])


def test_wave23_cn_nl_labor():
    """Wave 23: :cn 劳动仲裁 1年时效・仲裁前置 + 经济补偿 N/2N (labor 14 juris) ·
    :nl vervaltermijn **2か月** (BW 7:686a — 停止・中断なしの失権期間, critical) +
    vaststellingsovereenkomst 14日撤回権の確認警告."""
    ps, _ = _by_id()
    cn = ps["ntc:cn-jiechu"]
    assert cn["status"] == ":genuine" and cn["proc"] == "proc:cn-jiechu"
    assert any("27条" in d["anchor"] for d in cn["deadlines"])
    assert any("2N" in d["rule"] for d in cn["deadlines"])
    nl = ps["ntc:nl-ontslag"]
    assert nl["status"] == ":genuine" and nl["proc"] == "proc:nl-ontslag"
    assert nl["deadlines"][0]["critical"] is True
    assert "7:686a" in nl["deadlines"][0]["anchor"]


def test_wave24_es_it_housing_ch_labor():
    """Wave 24: 南欧の高速立退き — :es desahucio oposición 10 días hábiles
    (critical) + enervación · :it convalida di sfratto (欠席=確定, critical) +
    termine di grazia 90日 · :ch Einsprache **vor Ende der Kündigungsfrist**
    (OR 336b, critical) — housing no-self-help は parametric で自動適用."""
    ps, _ = _by_id()
    es = ps["ntc:es-desahucio"]
    assert es["status"] == ":genuine" and es["proc"] == "proc:es-desahucio"
    assert es["deadlines"][0]["critical"] is True
    assert any("enervación" in d["rule"] for d in es["deadlines"])
    it = ps["ntc:it-sfratto"]
    assert it["status"] == ":genuine" and it["proc"] == "proc:it-sfratto"
    assert it["deadlines"][0]["critical"] is True
    assert any("termine di grazia" in d["rule"] for d in it["deadlines"])
    ch = ps["ntc:ch-kuendigung"]
    assert ch["status"] == ":genuine" and ch["proc"] == "proc:ch-arbeitskuendigung"
    assert any("336b" in d["anchor"] for d in ch["deadlines"])


def test_critical_banner_in_report():
    """Wave 24 maturity: critical deadlines carry the ⚠ banner in the rendered plan."""
    from respond_plan import report as plan_report
    _, notices = load_docs()
    ps = plans(notices, load_procs())
    text = plan_report(ps)
    assert "⚠ 期限ルール" in text


def test_wave25_sg_pt_labor():
    """Wave 25: :sg TADM 1か月 (mediation 前置 → ECT — 弁護士代理禁止の本人手続,
    critical; work pass 警告) · :pt impugnação 60 dias + suspensão 5 días úteis
    (CT 386/387, critical)."""
    ps, _ = _by_id()
    sg = ps["ntc:sg-dismissal"]
    assert sg["status"] == ":genuine" and sg["proc"] == "proc:sg-dismissal"
    assert sg["deadlines"][0]["critical"] is True
    assert "1か月" in sg["deadlines"][0]["rule"]
    pt = ps["ntc:pt-despedimento"]
    assert pt["status"] == ":genuine" and pt["proc"] == "proc:pt-despedimento"
    assert pt["deadlines"][0]["critical"] is True
    assert "60日" in pt["deadlines"][0]["rule"] and "5日" in pt["deadlines"][0]["rule"]


def test_wave26_se_pl_ie_labor():
    """Wave 26: :se ogiltigförklaring underrättelse **2 veckor** (LAS 40§ —
    世界最短級, critical) · :pl odwołanie **21 dni** (KP 264, critical) ·
    :ie WRC 6か月/最大12か月 (UDA 1977, critical)."""
    ps, _ = _by_id()
    se = ps["ntc:se-uppsagning"]
    assert se["status"] == ":genuine" and se["proc"] == "proc:se-uppsagning"
    assert se["deadlines"][0]["critical"] is True and "LAS" in se["deadlines"][0]["anchor"]
    pl = ps["ntc:pl-wypowiedzenie"]
    assert pl["status"] == ":genuine" and pl["proc"] == "proc:pl-wypowiedzenie"
    assert "21 dni" in pl["deadlines"][0]["rule"]
    ie = ps["ntc:ie-dismissal"]
    assert ie["status"] == ":genuine" and ie["proc"] == "proc:ie-dismissal"
    assert any("s.41" in d["anchor"] for d in ie["deadlines"])


def test_wave27_no_nz_in_labor():
    """Wave 27: :no forhandlinger **2 uker** + søksmål 8 uker/6mnd (aml §17-3/17-4,
    critical; stå i stilling) · :nz **personal grievance 90日** (ERA 2000 s.114,
    critical; email genuine の労働通知) · :in ID Act 25F 手続要件 + gratuity Form I
    30日 (PGA 1972)."""
    ps, _ = _by_id()
    no = ps["ntc:no-oppsigelse"]
    assert no["status"] == ":genuine" and no["proc"] == "proc:no-oppsigelse"
    assert no["deadlines"][0]["critical"] is True and "§17-3" in no["deadlines"][0]["anchor"]
    nz = ps["ntc:nz-dismissal"]
    assert nz["status"] == ":genuine" and nz["proc"] == "proc:nz-dismissal"
    assert nz["channel"] == ":email"  # declared digital — NZ 雇用実務
    assert "90日" in nz["deadlines"][0]["rule"]
    ind = ps["ntc:in-retrench"]
    assert ind["status"] == ":genuine" and ind["proc"] == "proc:in-termination"
    assert any("25F" in d["anchor"] for d in ind["deadlines"])
    assert any("Form I" in o["label"] for o in ind["options"])


def test_wave28_civil_only_eliminated():
    """Wave 28 milestone: the last 5 civil-only rows gain :labor — :dk 協約ルート
    主体の honest 開示 · :fi kanneaika 2v · :be CCT 109 motivation 2 mois (critical) ·
    :mx prescripción **2 meses** (LFT 518 critical; renuncia 署名拒否警告) · :ar
    telegrama laboral (TT 無料) — 解雇通知が全管轄で専門応答を持つ."""
    ps, _ = _by_id()
    for nid, pid in [("ntc:dk-opsigelse", "proc:dk-opsigelse"),
                     ("ntc:fi-irtisanominen", "proc:fi-irtisanominen"),
                     ("ntc:be-licenciement", "proc:be-licenciement"),
                     ("ntc:mx-despido", "proc:mx-despido"),
                     ("ntc:ar-despido", "proc:ar-despido")]:
        p = ps[nid]
        assert p["status"] == ":genuine" and p["proc"] == pid, nid
    assert ps["ntc:mx-despido"]["deadlines"][0]["critical"] is True
    assert ps["ntc:be-licenciement"]["deadlines"][0]["critical"] is True
    assert any("telegrama" in o["label"] for o in ps["ntc:ar-despido"]["options"])
    # :at — computed civil-only gap が手元リストの漏れを検出した管轄 (Anfechtung 2 Wochen)
    at = ps["ntc:at-kuendigung"]
    assert at["status"] == ":genuine" and at["proc"] == "proc:at-kuendigung"
    assert at["deadlines"][0]["critical"] is True and "§105" in at["deadlines"][0]["anchor"]


def test_wave29_nl_br_se_housing():
    """Wave 29: housing 13 juris — :nl BW 7:272 (賃貸人の opzegging では終了しない;
    同意しない自由 = protective) · :br purga da mora 15日 (Lei 8.245/91 critical) ·
    :se besittningsskydd + hyresnämnden (anvisning 必須). Labor/housing の同語衝突
    (uppsägning/opzegging) は雇用特定 trigger へ分離済み."""
    ps, procs = _by_id()
    nl = ps["ntc:nl-huur"]
    assert nl["status"] == ":genuine" and nl["proc"] == "proc:nl-huuropzegging"
    assert any("7:272" in d["anchor"] for d in nl["deadlines"])
    br = ps["ntc:br-despejo"]
    assert br["status"] == ":genuine" and br["proc"] == "proc:br-despejo"
    assert br["deadlines"][0]["critical"] is True and "purga da mora" in br["deadlines"][0]["rule"]
    se = ps["ntc:se-hyres"]
    assert se["status"] == ":genuine" and se["proc"] == "proc:se-hyresuppsagning"
    assert any("hyresnämnden" in d["rule"] for d in se["deadlines"])
    # disambiguation: 雇用通知は labor へ, 賃貸通知は housing へ, 裸の語は :unknown
    base = {":notice/id": "ntc:x", ":notice/channel": ":mail", ":notice/sourcing": ":synthetic"}
    p1, s1 = classify({**base, ":notice/jurisdiction": ":se",
                       ":notice/text": "Uppsägning av din anställning"}, procs)
    assert p1[":proc/id"] == "proc:se-uppsagning"
    p2, s2 = classify({**base, ":notice/jurisdiction": ":se",
                       ":notice/text": "Uppsägning"}, procs)
    assert p2 is None  # bare word → honest degrade


def test_wave30_es_br_it_enforcement():
    """Wave 30: 賃金差押え保護が10法体系に — :es SMI 全額保護+累進 (LEC 607) ·
    :br **原則 impenhorável** (CPC 833 IV — 世界最広) · :it un quinto 1/5 +
    minimo vitale (c.p.c. 545). 全 enforcement proc の protective invariant auto."""
    ps, _ = _by_id()
    es = ps["ntc:es-embargo"]
    assert es["status"] == ":genuine" and es["proc"] == "proc:es-embargo"
    assert any("607" in d["anchor"] for d in es["deadlines"])
    br = ps["ntc:br-penhora"]
    assert br["status"] == ":genuine" and br["proc"] == "proc:br-penhora"
    assert any("833" in d["anchor"] for d in br["deadlines"])
    it = ps["ntc:it-pignoramento"]
    assert it["status"] == ":genuine" and it["proc"] == "proc:it-pignoramento"
    assert any("545" in d["anchor"] and "un quinto" in d["rule"] for d in it["deadlines"])


def test_plans_json_export():
    """Wave 30 maturity: 機械可読プラン (yoro UI 向け) — JSON round-trips with the
    same statuses/procs as the in-memory plans."""
    import json
    _, notices = load_docs()
    ps = plans(notices, load_procs())
    text = json.dumps(ps, ensure_ascii=False, indent=1)
    back = json.loads(text)
    assert len(back) == len(ps)
    assert {p["status"] for p in back} == {p["status"] for p in ps}
    assert all("deadlines" in p and "options" in p for p in back)


def test_wave31_insolvency_es_it_nl():
    """Wave 31: insolvency 9 juris — :es comunicación 1 mes/BOE 起算 (劣後リスク,
    critical) · :it insinuazione 30日前/PEC (tardiva, critical) · :nl ter
    verificatie (insolventieregister 確認)."""
    ps, _ = _by_id()
    es = ps["ntc:es-concurso"]
    assert es["status"] == ":genuine" and es["proc"] == "proc:es-concurso"
    assert es["deadlines"][0]["critical"] is True
    it = ps["ntc:it-insinuazione"]
    assert it["status"] == ":genuine" and it["proc"] == "proc:it-insinuazione"
    assert any("PEC" in d["rule"] for d in it["deadlines"])
    nl = ps["ntc:nl-faillissement"]
    assert nl["status"] == ":genuine" and nl["proc"] == "proc:nl-faillissement"
    assert any("108-110" in d["anchor"] for d in nl["deadlines"])


def test_insolvency_kaiyaku_crosscheck_invariant():
    """Wave 31 maturity: EVERY :insolvency procedure carries the kaiyaku 縁-ledger
    crosscheck in an option label — 前払金/ポイント/gift card が債権であることを
    member が必ず知り, actor 連携が構造保証になる."""
    _, procs = _by_id()
    for p in procs:
        if p.get(":proc/track") == ":insolvency":
            assert any("kaiyaku" in o[":opt/label"] for o in p[":proc/options"]), \
                p[":proc/id"]


def test_wave32_es_it_br_family():
    """Wave 32: family 10 juris — :es contestación 20 días + **abogado/procurador
    必須の正直開示** (justicia gratuita 本人申請 protective) · :it Cartabia 統一手続
    costituzione 30日前 · :br contestação 15 du + **cartório 低負担ルート** の開示;
    kokoro invariant auto-extends."""
    ps, _ = _by_id()
    es = ps["ntc:es-divorcio"]
    assert es["status"] == ":genuine" and es["proc"] == "proc:es-divorcio"
    assert es["deadlines"][0]["critical"] is True
    assert any("justicia gratuita" in o["label"] for o in es["options"])
    it = ps["ntc:it-separazione"]
    assert it["status"] == ":genuine" and it["proc"] == "proc:it-separazione"
    assert any("473-bis" in d["anchor"] for d in it["deadlines"])
    br = ps["ntc:br-divorcio"]
    assert br["status"] == ":genuine" and br["proc"] == "proc:br-divorcio"
    assert any("cartório" in o["label"] for o in br["options"])


def test_wave33_pl_at_ch_housing():
    """Wave 33: housing 16 juris — :pl lokal socjalny + **okres ochronny 冬季執行
    停止** (trêve hivernale の波蘭版) · :at **裁判所経由でしか解約できない** MRG §33
    + Einwendungen 4 Wochen (critical) · :ch Schlichtungsbehörde 30日 無料 +
    **Formular 不備=無効** (OR 266l, critical). Miet/Arbeit の同語は分離済み."""
    ps, procs = _by_id()
    pl = ps["ntc:pl-eksmisja"]
    assert pl["status"] == ":genuine" and pl["proc"] == "proc:pl-eksmisja"
    assert any("okres ochronny" in d["rule"] for d in pl["deadlines"])
    at = ps["ntc:at-aufkuendigung"]
    assert at["status"] == ":genuine" and at["proc"] == "proc:at-mietkuendigung"
    assert at["deadlines"][0]["critical"] is True and "§33" in at["deadlines"][0]["anchor"]
    ch = ps["ntc:ch-mietkuendigung"]
    assert ch["status"] == ":genuine" and ch["proc"] == "proc:ch-mietkuendigung"
    assert any("266l" in d["anchor"] for d in ch["deadlines"])
    # :ch 同語分離: Arbeitsverhältnis → labor / Mietverhältnis → housing
    base = {":notice/id": "ntc:x", ":notice/jurisdiction": ":ch",
            ":notice/channel": ":mail", ":notice/sourcing": ":synthetic"}
    p1, _ = classify({**base, ":notice/text": "Kündigung des Arbeitsverhältnisses"}, procs)
    p2, _ = classify({**base, ":notice/text": "Kündigung des Mietverhältnisses"}, procs)
    assert p1[":proc/id"] == "proc:ch-arbeitskuendigung"
    assert p2[":proc/id"] == "proc:ch-mietkuendigung"


def test_wave34_nl_se_tw_enforcement():
    """Wave 34: 賃金保護13法体系 — :nl beslagvrije voet 自動計算 (是正請求可) ·
    :se förbehållsbelopp 再計算請求 · :tw 1/3 限度 + 最低生活費 (声明異議)."""
    ps, _ = _by_id()
    nl = ps["ntc:nl-beslag"]
    assert nl["status"] == ":genuine" and nl["proc"] == "proc:nl-beslag"
    assert any("beslagvrije voet" in d["rule"] for d in nl["deadlines"])
    se = ps["ntc:se-utmatning"]
    assert se["status"] == ":genuine" and se["proc"] == "proc:se-utmatning"
    assert any("förbehållsbelopp" in d["rule"] for d in se["deadlines"])
    tw = ps["ntc:tw-qiangzhi"]
    assert tw["status"] == ":genuine" and tw["proc"] == "proc:tw-qiangzhi"
    assert any("115-1" in d["anchor"] for d in tw["deadlines"])


def test_wave36_cn_housing():
    """Wave 36: :cn housing — 任意解除の制限 + **买卖不破租赁** (民法典725条);
    断水断电/換鎖の no-self-help."""
    ps, _ = _by_id()
    cn = ps["ntc:cn-tuizu"]
    assert cn["status"] == ":genuine" and cn["proc"] == "proc:cn-tuizu"
    assert any("725" in d["anchor"] for d in cn["deadlines"])


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
