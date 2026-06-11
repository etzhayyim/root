"""kakaku 価格 — shared minimal EDN reader + seed classifier (stdlib only).

Ported from the kabuto/watatsuna readers (same subset: vectors [], maps {},
:keyword, "string", number, bool, nil). Keeps kakaku's tooling dependency-free so
it runs on any python3 with no install step. ADR-2605091200.
"""
from __future__ import annotations
import re
import pathlib

# ── minimal EDN reader (subset) ──────────────────────────────────────────────
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')
_END = object()


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':
        return True
    if t == 'false':
        return False
    if t == 'nil':
        return None
    if t.startswith(':'):
        return t  # keep keywords as ":ns/name" strings
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            v = _parse(it)
            out[k] = v
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def load_edn(path: pathlib.Path):
    it = _tokens(pathlib.Path(path).read_text(encoding='utf-8'))
    return _parse(it)


def _kw(v):
    """Strip a leading ':' from an EDN keyword value (':in-stock' → 'in-stock')."""
    return v[1:] if isinstance(v, str) and v.startswith(":") else v


def classify(rows):
    """Split the flat seed vector into (products, merchants, offers, price_history),
    normalizing the agent-facing field names so agent.py can consume them directly.
    Keyword values (availability, region, status) are stripped of their leading ':'."""
    products, merchants, offers, ph = {}, {}, [], []
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ":product/id" in r:
            products[r[":product/id"]] = {
                "productId": r[":product/id"], "name": r.get(":product/name"),
                "brand": r.get(":product/brand"), "jan": r.get(":product/jan"),
                "category": r.get(":product/category")}
        elif ":merchant/id" in r:
            merchants[r[":merchant/id"]] = {
                "merchantId": r[":merchant/id"], "name": r.get(":merchant/name"),
                "region": _kw(r.get(":merchant/region")),
                "reputationScore": r.get(":merchant/reputation-score"),
                "status": _kw(r.get(":merchant/status"))}
        elif ":offer/id" in r:
            mid = r[":offer/id"].split(":", 1)[0]
            offers.append({
                "offerId": r[":offer/id"], "merchantId": mid,
                "price": r.get(":offer/price", 0), "shippingFee": r.get(":offer/shipping-fee", 0),
                "totalPrice": r.get(":offer/total-price", 0),
                "availability": _kw(r.get(":offer/availability", "unknown")),
                "deliveryEtaDays": r.get(":offer/delivery-eta-days", 14),
                "productUrl": r.get(":offer/product-url")})
        elif ":ph/total-price" in r:
            ph.append({"totalPrice": r.get(":ph/total-price"),
                       "availability": _kw(r.get(":ph/availability", "unknown")),
                       "observedAt": r.get(":ph/observed-at")})
    return products, merchants, offers, ph
