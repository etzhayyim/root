#!/usr/bin/env python3
"""tate 盾 — clause-scanner + Datom-emit tests (ADR-2606112300). Pure stdlib.

Verifies the constitutional invariants empirically:
  - registries + member docs load, all member-side data is :synthetic (G1)
  - G2 non-adjudicating: every flag carries a DISCLOSED anchor + verify-current-law;
    no flag carries a verdict field; report language is 可能性/専門家確認
  - G5 context honesty: consumer anchors never fire on :b2b docs (and vice versa)
  - expected shapes hit: 違約金→9条1号, 全部免責→8条, 19.9%→9条2号, リボ自動,
    B2B 無限賠償/競業避止/90日サイト
  - routes are members of the closed route set
  - Datom log: ground + transient strata; determinism
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from terms_scan import load_docs, load_patterns, scan, scan_doc, report  # noqa: E402
import datom_emit  # noqa: E402

ROUTES = {":kurashimori", ":kaiyaku", ":referral", ":info"}


def _res():
    docs, _ = load_docs()
    return docs, scan(docs, load_patterns())


def test_load_nontrivial_and_synthetic():
    docs, notices = load_docs()
    patterns = load_patterns()
    assert len(docs) >= 4 and len(notices) >= 5 and len(patterns) >= 12
    for d in docs:
        assert d.get(":doc/sourcing") == ":synthetic", d[":doc/id"]
    for n in notices:
        assert n.get(":notice/sourcing") == ":synthetic", n[":notice/id"]


def test_non_adjudicating_flags():
    """G2: anchor + verify-current-law on every flag; no verdict key anywhere."""
    _, res = _res()
    assert res["flags"], "scanner found nothing — seed/keywords drifted"
    for f in res["flags"]:
        assert f["anchor"], f
        assert f["disclosed"] is True and f["verify_current_law"] is True
        assert "verdict" not in f and "invalid" not in f, f
        assert f["route"] in ROUTES, f


def test_report_language_honest():
    _, res = _res()
    text = report(res)
    assert "可能性" in text and "専門家確認" in text
    assert "無効です" not in text  # never asserts invalidity (G2)


def test_context_honesty_no_cross_anchors():
    """G5: consumer-law anchors must never fire on :b2b docs, and B2B patterns
    must never fire on consumer docs — even when keywords would match."""
    docs, _ = load_docs()
    patterns = load_patterns()
    for d in docs:
        for f in scan_doc(d, patterns):
            p = next(p for p in patterns if p[":clause/id"] == f["clause"])
            assert p[":clause/context"] == d[":doc/context"], f
    # adversarial: a B2B doc containing a consumer keyword still yields no consumer anchor
    fake_b2b = {":doc/id": "doc:adv", ":doc/context": ":b2b", ":doc/sourcing": ":synthetic",
                ":doc/text": "当社は一切の責任を負いません。違約金として残期間の利用料全額。"}
    for f in scan_doc(fake_b2b, patterns):
        assert "消費者契約法" not in f["anchor"], f


def test_expected_shapes_hit():
    _, res = _res()
    hits = {(f["doc"], f["clause"]) for f in res["flags"]}
    assert ("doc:fitness-tos", "cl:excessive-penalty") in hits
    assert ("doc:fitness-tos", "cl:auto-renewal-trap") in hits
    assert ("doc:video-tos", "cl:full-exemption") in hits
    assert ("doc:video-tos", "cl:excessive-late-interest") in hits
    assert ("doc:video-tos", "cl:exclusive-jurisdiction") in hits
    assert ("doc:card-agreement", "cl:auto-revolving") in hits
    assert ("doc:card-agreement", "cl:defense-cutoff") in hits
    assert ("doc:b2b-services", "cl:b2b-unlimited-liability") in hits
    assert ("doc:b2b-services", "cl:b2b-noncompete") in hits
    assert ("doc:b2b-services", "cl:b2b-long-payment") in hits
    assert ("doc:b2b-services", "cl:b2b-ip-assignment") in hits


def test_risk_ordering():
    _, res = _res()
    order = {":high": 0, ":mid": 1, ":info": 2}
    per_doc = {}
    for f in res["flags"]:
        per_doc.setdefault(f["doc"], []).append(order[f["risk"]])
    # within scan_doc, high sorts first
    docs, _ = load_docs()
    for d in docs:
        ranks = [order[f["risk"]] for f in scan_doc(d, load_patterns())]
        assert ranks == sorted(ranks), d[":doc/id"]


def test_intl_expected_shapes_hit():
    """Worldwide (ADR-2606112400): representative intl clause shapes fire."""
    _, res = _res()
    hits = {(f["doc"], f["clause"]) for f in res["flags"]}
    assert ("doc:us-saas-tos", "cl:us-arbitration-class-waiver") in hits
    assert ("doc:us-saas-tos", "cl:us-auto-renewal-negative-option") in hits
    assert ("doc:us-saas-tos", "cl:us-early-termination-fee") in hits
    assert ("doc:eu-sub-tos", "cl:eu-withdrawal-exclusion") in hits
    assert ("doc:eu-sub-tos", "cl:eu-unilateral-change") in hits
    assert ("doc:uk-gym-terms", "cl:uk-liability-exclusion") in hits
    assert ("doc:de-agb", "cl:de-price-increase") in hits
    assert ("doc:de-agb", "cl:de-lump-damages") in hits
    # wave 2 (:kr :fr)
    assert ("doc:kr-tos", "cl:kr-full-exemption") in hits
    assert ("doc:kr-tos", "cl:kr-excessive-penalty") in hits
    assert ("doc:fr-abonnement", "cl:fr-liability-exclusion") in hits
    assert ("doc:fr-abonnement", "cl:fr-tacit-renewal") in hits
    # wave 3 (:au :ca :it)
    assert ("doc:au-tos", "cl:au-unfair-variation") in hits
    assert ("doc:au-tos", "cl:au-guarantee-exclusion") in hits
    assert ("doc:ca-tos", "cl:ca-arbitration-consumer") in hits
    assert ("doc:ca-tos", "cl:ca-all-sales-final") in hits
    assert ("doc:it-tos", "cl:it-clausola-vessatoria") in hits
    assert ("doc:it-tos", "cl:it-tacito-rinnovo") in hits
    # wave 4 (:es :nl :br)
    assert ("doc:es-tos", "cl:es-clausula-abusiva") in hits
    assert ("doc:es-tos", "cl:es-prorroga-automatica") in hits
    assert ("doc:nl-voorwaarden", "cl:nl-exoneratie") in hits
    assert ("doc:nl-voorwaarden", "cl:nl-stilzwijgende-verlenging") in hits
    assert ("doc:br-termos", "cl:br-exoneracao") in hits
    assert ("doc:br-termos", "cl:br-renovacao-automatica") in hits
    # wave 5 (:tw :sg :in)
    assert ("doc:tw-tos", "cl:tw-full-exemption") in hits
    assert ("doc:tw-tos", "cl:tw-auto-renewal") in hits
    assert ("doc:sg-tos", "cl:sg-liability-exclusion") in hits
    assert ("doc:sg-tos", "cl:sg-auto-renewal") in hits
    assert ("doc:in-tos", "cl:in-liability-exclusion") in hits
    assert ("doc:in-tos", "cl:in-arbitration-no-ouster") in hits
    # wave 6 (:cn — 簡体字, :tw 繁体字とは別パターン)
    assert ("doc:cn-tos", "cl:cn-full-exemption") in hits
    assert ("doc:cn-tos", "cl:cn-auto-renewal") in hits
    # wave 7 (:pl :se)
    assert ("doc:pl-regulamin", "cl:pl-niedozwolona") in hits
    assert ("doc:pl-regulamin", "cl:pl-auto-renewal") in hits
    assert ("doc:se-villkor", "cl:se-friskrivning") in hits
    assert ("doc:se-villkor", "cl:se-auto-renewal") in hits
    # wave 8 (:at :pt)
    assert ("doc:at-agb", "cl:at-haftungsausschluss") in hits
    assert ("doc:at-agb", "cl:at-auto-renewal") in hits
    assert ("doc:pt-condicoes", "cl:pt-exclusao") in hits
    assert ("doc:pt-condicoes", "cl:pt-renovacao") in hits
    # wave 11 (:ie :ch)
    assert ("doc:ie-terms", "cl:ie-liability") in hits
    assert ("doc:ie-terms", "cl:ie-auto-renewal") in hits
    assert ("doc:ch-agb", "cl:ch-haftungsausschluss") in hits
    assert ("doc:ch-agb", "cl:ch-auto-renewal") in hits


def test_jurisdiction_isolation():
    """G10: anchors never cross jurisdictions — JP statutes never fire on a US doc,
    even when the keywords are present."""
    docs, _ = load_docs()
    patterns = load_patterns()
    for d in docs:
        for f in scan_doc(d, patterns):
            p = next(p for p in patterns if p[":clause/id"] == f["clause"])
            assert p.get(":clause/jurisdiction", ":jp") == d.get(":doc/jurisdiction", ":jp"), f
    # adversarial: a US consumer doc containing JP keywords yields NO JP anchor
    adv = {":doc/id": "doc:adv-us", ":doc/jurisdiction": ":us", ":doc/context": ":consumer",
           ":doc/sourcing": ":synthetic",
           ":doc/text": "当社は一切の責任を負いません。遅延損害金は年率19.9%。"}
    for f in scan_doc(adv, patterns):
        assert "消費者契約法" not in f["anchor"], f


def test_case_insensitive_matching():
    """Maturity (wave 3): sentence-initial capitals / ALL-CAPS must not hide a clause."""
    patterns = load_patterns()
    doc = {":doc/id": "doc:caps", ":doc/jurisdiction": ":au", ":doc/context": ":consumer",
           ":doc/sourcing": ":synthetic", ":doc/text": "WE EXCLUDE ALL LIABILITY."}
    assert any(f["clause"] == "cl:au-guarantee-exclusion" for f in scan_doc(doc, patterns))


def test_datoms_ground_and_transient():
    text = datom_emit.emit(tx=3)
    assert ":clause/anchor" in text and ":doc/context" in text
    assert ":bond/is-transient true" in text, "derived flags must be transient (G2)"
    assert ":tate/risk" in text and ":tate/status" in text


def test_determinism():
    assert datom_emit.emit(tx=1) == datom_emit.emit(tx=1)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
