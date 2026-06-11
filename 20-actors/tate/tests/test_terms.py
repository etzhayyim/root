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
