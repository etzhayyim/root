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
