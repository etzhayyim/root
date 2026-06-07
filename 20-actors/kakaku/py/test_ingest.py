#!/usr/bin/env python3
"""kakaku 価格 — offer ingest extraction tests (ingest.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_ingest.py
    python3 test_ingest.py

Verifies the tiered extraction (JSON-LD → selector → meta/regex) and the constitutional
gates: live fetch is operator-gated (G11), source URLs are affiliate-stripped (G3), and
the Murakumo LLM is a fallback only (G5; absent in dev → deterministic tiers still work).
"""
import ingest


_JSONLD_PAGE = '''
<html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Product","name":"Vacuum Bottle 500ml",
 "offers":{"@type":"Offer","price":"3200","priceCurrency":"JPY",
           "availability":"https://schema.org/InStock"}}
</script></head><body>...</body></html>
'''

_META_PAGE = '''
<html><head>
<meta property="og:title" content="Thermo Mug &amp; Lid"/>
</head><body><span class="price">¥1,280</span></body></html>
'''


# ── JSON-LD tier ──────────────────────────────────────────────────────────
def test_jsonld_extracts_price_currency_availability():
    o = ingest.extract_offer(_JSONLD_PAGE)
    assert o["price"] == 320000          # 3200 JPY → minor units ×100
    assert o["currency"] == "JPY"
    assert o["availability"] == "in-stock"
    assert o["name"] == "Vacuum Bottle 500ml"
    assert o["extracted"] is True


def test_availability_normalization():
    assert ingest.normalize_availability("https://schema.org/OutOfStock") == "out-of-stock"
    assert ingest.normalize_availability("PreOrder") == "preorder"
    assert ingest.normalize_availability(None) == "unknown"


# ── meta/regex tier ───────────────────────────────────────────────────────
def test_meta_fallback_title_and_price():
    o = ingest.extract_offer(_META_PAGE)
    assert o["name"] == "Thermo Mug & Lid"   # html-unescaped
    assert o["price"] == 128000              # ¥1,280 → minor
    assert o["currency"] == "JPY"


# ── selector tier ─────────────────────────────────────────────────────────
def test_selector_profile_extraction():
    content = '<div id="p">PRICE: 4980 yen</div><h1 id="t">Steel Kettle</h1>'
    prof = {"price": r"PRICE:\s*([0-9]+)", "name": r'<h1[^>]*>(.*?)</h1>'}
    o = ingest.extract_offer(content, selector_profile=prof)
    assert o["price"] == 498000
    assert o["name"] == "Steel Kettle"


# ── affiliate stripping (G3) ──────────────────────────────────────────────
def test_strip_affiliate_params():
    dirty = "https://shop.example/p/123?tag=aff-22&utm_source=x&color=blue"
    clean = ingest.strip_affiliate(dirty)
    assert "tag=" not in clean and "utm_source" not in clean
    assert "color=blue" in clean


# ── G11 operator-gated fetch ──────────────────────────────────────────────
def test_live_fetch_refused_without_operator_g11():
    out = ingest.ingest_offer_from_url("https://shop.example/p?tag=aff", content=None)
    assert out["state"] == "fetch-gated"
    assert "G11" in out["reason"]
    assert "tag=" not in out["productUrl"]    # affiliate stripped even on the gated path


def test_ingest_with_prefetched_content_extracts():
    out = ingest.ingest_offer_from_url("https://shop.example/p?utm_source=x",
                                       content=_JSONLD_PAGE)
    assert out["state"] == "extracted"
    assert out["price"] == 320000
    assert "utm_source" not in out["productUrl"]


def test_incomplete_content_marked():
    out = ingest.ingest_offer_from_url("https://shop.example/p", content="<html>no price</html>")
    assert out["state"] == "incomplete"
    assert out["extracted"] is False


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"ingest.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if _run() else 1)
