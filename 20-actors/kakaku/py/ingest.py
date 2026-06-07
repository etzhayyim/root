#!/usr/bin/env python3
"""kakaku 価格 — offer ingest from page content (extraction pipeline).

ADR-2605091200 + CLAUDE.md Update Flow step 2. Turns an already-fetched page payload into a
canonical offer record, using a tiered extraction strategy and only falling back to the
Murakumo LLM for fields the deterministic extractors miss:

  1. JSON-LD   schema.org Product/Offer (<script type="application/ld+json">)
  2. selector  merchant-specific regex profile (per-merchant override)
  3. meta/regex og:title + currency-symbol price patterns
  4. Murakumo  LLM host-binding fill for STILL-missing name/price/currency/availability (G5)

The network FETCH itself is the only operator-gated step (G11, no-server-key): `ingest_offer_
from_url` refuses to fetch live without an operator ref — extraction runs on already-fetched
or test content. No affiliate params are ever kept (G3): the source URL is normalized.

stdlib only (re/json/html). Murakumo via the kotoba `llm` host binding (no external LLM).
"""
from __future__ import annotations

import html
import json
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

try:
    from kotoba import llm  # type: ignore
except ImportError:  # local dev / offline
    llm = None  # type: ignore

# schema.org availability → kakaku enum
_AVAIL = {
    "instock": "in-stock", "in_stock": "in-stock", "available": "in-stock",
    "outofstock": "out-of-stock", "soldout": "out-of-stock",
    "preorder": "preorder", "presale": "preorder",
    "backorder": "backorder", "limitedavailability": "in-stock",
}
# affiliate / tracking params stripped from any source URL (mirrors okaimono G3 denylist).
_AFFILIATE_PARAMS = frozenset({
    "tag", "aff", "affid", "aff_id", "affiliate", "affiliate_id", "partner", "pid",
    "click_id", "clickid", "ascsubtag", "linkcode", "linkid", "scid", "ref", "ref_",
    "gclid", "fbclid", "msclkid", "yclid", "dclid",
})
_AFFILIATE_PREFIXES = ("utm_", "aff_", "pk_")


def normalize_availability(raw) -> str:
    if not raw:
        return "unknown"
    s = re.sub(r"https?://schema\.org/", "", str(raw)).strip().lower().replace("-", "").replace(" ", "")
    return _AVAIL.get(s, "unknown")


def strip_affiliate(url: str) -> str:
    """Remove affiliate/tracking params from a source URL (G3); functional params kept."""
    if not url:
        return ""
    parts = urlsplit(url)
    kept = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() not in _AFFILIATE_PARAMS
            and not any(k.lower().startswith(p) for p in _AFFILIATE_PREFIXES)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(kept), ""))


# --------------------------------------------------------------------------- #
# 1. JSON-LD schema.org Product/Offer
# --------------------------------------------------------------------------- #
_LD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                    re.DOTALL | re.IGNORECASE)


def _walk_for_offer(node) -> dict:
    """Find the first object carrying an offer (price) anywhere in a JSON-LD tree."""
    found: dict = {}
    if isinstance(node, dict):
        t = str(node.get("@type", "")).lower()
        if "name" in node and not found.get("name"):
            found["name"] = node["name"]
        offers = node.get("offers")
        cand = offers if isinstance(offers, dict) else (offers[0] if isinstance(offers, list) and offers else None)
        src = cand if isinstance(cand, dict) else (node if ("price" in node or t == "offer") else None)
        if isinstance(src, dict) and src.get("price") is not None:
            return {"name": found.get("name") or node.get("name"),
                    "price": src.get("price"), "currency": src.get("priceCurrency"),
                    "availability": src.get("availability")}
        for v in node.values():
            sub = _walk_for_offer(v)
            if sub.get("price") is not None:
                sub.setdefault("name", found.get("name"))
                return sub
    elif isinstance(node, list):
        for v in node:
            sub = _walk_for_offer(v)
            if sub.get("price") is not None:
                return sub
    return found


def extract_jsonld(content: str) -> dict:
    for block in _LD_RE.findall(content or ""):
        try:
            data = json.loads(block.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        got = _walk_for_offer(data)
        if got.get("price") is not None:
            return got
    return {}


# --------------------------------------------------------------------------- #
# 2. merchant-specific selector profile (regex)  +  3. meta/regex fallback
# --------------------------------------------------------------------------- #
def extract_selector(content: str, profile: dict) -> dict:
    out: dict = {}
    for field, pat in (profile or {}).items():
        m = re.search(pat, content or "")
        if m:
            out[field] = m.group(1) if m.groups() else m.group(0)
    return out


_PRICE_RE = re.compile(r"[¥$€£]\s?([0-9][0-9,]*(?:\.[0-9]{1,2})?)")
_OG_TITLE_RE = re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', re.IGNORECASE)
_CURRENCY_SYM = {"¥": "JPY", "$": "USD", "€": "EUR", "£": "GBP"}


def extract_meta(content: str) -> dict:
    out: dict = {}
    mt = _OG_TITLE_RE.search(content or "")
    if mt:
        out["name"] = html.unescape(mt.group(1))
    mp = _PRICE_RE.search(content or "")
    if mp:
        out["price"] = mp.group(1).replace(",", "")
        out["currency"] = _CURRENCY_SYM.get(mp.group(0)[0])
    return out


def _to_minor(price) -> int:
    """Convert a price string/number to integer minor units (×100 for 2-dp currencies)."""
    try:
        return int(round(float(str(price).replace(",", "")) * 100))
    except (TypeError, ValueError):
        return 0


# --------------------------------------------------------------------------- #
# orchestration
# --------------------------------------------------------------------------- #
_REQUIRED = ("name", "price", "currency", "availability")


def extract_offer(content: str, selector_profile: dict | None = None,
                  use_llm: bool = False) -> dict:
    """Run the tiered extraction over already-fetched content. Deterministic tiers first;
    the Murakumo LLM (when available + use_llm) fills ONLY still-missing fields (G5)."""
    merged: dict = {}
    for tier in (extract_jsonld(content),
                 extract_selector(content, selector_profile or {}),
                 extract_meta(content)):
        for k, v in tier.items():
            if v is not None and merged.get(k) in (None, ""):
                merged[k] = v
    if use_llm and llm is not None and any(merged.get(f) in (None, "") for f in _REQUIRED):
        merged = _llm_fill(content, merged)
    price_minor = _to_minor(merged.get("price"))
    return {
        "name": (merged.get("name") or "").strip(),
        "price": price_minor,                       # minor units
        "currency": merged.get("currency") or "unknown",
        "availability": normalize_availability(merged.get("availability")),
        "extracted": price_minor > 0,
        "tiers": [t for t, present in (("jsonld", bool(extract_jsonld(content))),) if present],
    }


def _llm_fill(content: str, partial: dict) -> dict:
    try:
        out = llm.infer(  # type: ignore[union-attr]
            model="gemma3:4b",
            prompt="Extract name, price, currency, availability as JSON from this product "
                   "page text (no commentary): " + (content or "")[:4000])
        data = json.loads(str(out))
        for k in _REQUIRED:
            if partial.get(k) in (None, "") and data.get(k) is not None:
                partial[k] = data[k]
    except Exception:
        pass
    return partial


def ingest_offer_from_url(url: str, content: str | None = None,
                          selector_profile: dict | None = None,
                          operator_ref: str | None = None, use_llm: bool = False) -> dict:
    """Ingest an offer. The network FETCH is operator-gated (G11, no-server-key): when no
    `content` is supplied a live fetch is required, which is REFUSED without an operator ref —
    extraction never silently hits the network. With `content` (pre-fetched or test) it
    extracts deterministically. The source URL is affiliate-stripped (G3)."""
    clean_url = strip_affiliate(url)
    if content is None:
        if not operator_ref:
            return {"state": "fetch-gated", "productUrl": clean_url,
                    "reason": "live fetch requires an operator ref (G11 no-server-key)"}
        return {"state": "fetch-gated", "productUrl": clean_url,
                "reason": "operator present — wire the live fetcher before use (G11)"}
    offer = extract_offer(content, selector_profile, use_llm=use_llm)
    offer["productUrl"] = clean_url
    offer["state"] = "extracted" if offer["extracted"] else "incomplete"
    return offer
