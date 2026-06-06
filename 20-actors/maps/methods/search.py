#!/usr/bin/env python3
"""maps — kotoba-native place name search (ADR-2606064500 R2). stdlib only.

The kotoba-native successor to the legacy `cmdSearchPlaces` (`WHERE name LIKE prefix`). kotoba
has no SQL `LIKE`, so name search is a TOKEN INDEX — the same shape kotoba's own web search
uses (BM25 / CJK-bigram, root CLAUDE.md). At ingest, a feature's name is tokenized to a set of
search tokens stored as `:feature/name-token` claims; at query, the query is tokenized the same
way and each token is an AVET probe `AVET(:feature/name-token, <token>)`; candidates are ranked
by how many query tokens they match.

Tokenizer (ONE function, used by BOTH write [ingest.py to_kg_batch] and read [search_places]):
  - ASCII words → all PREFIXES length 2..12 stored; a query word probes itself (so "tok"
    matches "Tokyo" because "tok" is a stored prefix of "tokyo").
  - CJK runs    → all adjacent BIGRAMS stored (+ the single char for length-1 runs); a query
    CJK run probes its bigrams (substring-ish match).

Fail-soft: any error → empty list. The bulk-dumper write path (_kotoba_feature) does NOT yet
stamp name-tokens (follow-up), so features ingested via dumpers are not name-searchable until
that parity lands — an honest, documented gap (mirrors the h3-cell stamping note).

Usage (library): from search import name_tokens, search_places
"""
from __future__ import annotations
import json, urllib.request

QUERY_NSID = "com.etzhayyim.apps.kotoba.graph.sparql"
_TIMEOUT = 5
_MAX_PREFIX = 12


def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (0x3040 <= o <= 0x30FF      # hiragana + katakana
            or 0x3400 <= o <= 0x9FFF   # CJK unified
            or 0xF900 <= o <= 0xFAFF   # CJK compat
            or 0xFF66 <= o <= 0xFF9D)  # halfwidth katakana


def _runs(name: str):
    """Split a name into (kind, text) runs: ('ascii', word) | ('cjk', run).
    Separators (non-alnum, non-CJK) break runs and are dropped."""
    out, buf, kind = [], [], None
    for ch in (name or "").lower():
        k = "cjk" if _is_cjk(ch) else ("ascii" if ch.isalnum() else None)
        if k != kind:
            if buf:
                out.append((kind, "".join(buf)))
            buf, kind = [], k
        if k is not None:
            buf.append(ch)
    if buf and kind is not None:
        out.append((kind, "".join(buf)))
    return out


def _bigrams(s: str):
    return [s[i:i + 2] for i in range(len(s) - 1)] or [s]


def name_tokens(name: str) -> set[str]:
    """INDEX tokens for a feature name (stored as :feature/name-token at ingest)."""
    toks: set[str] = set()
    for kind, text in _runs(name):
        if kind == "ascii" and len(text) >= 2:
            for n in range(2, min(len(text), _MAX_PREFIX) + 1):
                toks.add(text[:n])
        elif kind == "cjk":
            toks.update(_bigrams(text))
            if len(text) == 1:
                toks.add(text)
    return toks


def query_tokens(q: str) -> set[str]:
    """PROBE tokens for a search query."""
    toks: set[str] = set()
    for kind, text in _runs(q):
        if kind == "ascii" and len(text) >= 2:
            toks.add(text[:_MAX_PREFIX])
        elif kind == "cjk":
            toks.update(_bigrams(text))
            if len(text) == 1:
                toks.add(text)
    return toks


def _avet(endpoint: str, predicate: str, objects, limit: int = 2000) -> list[dict]:
    body = {"index": "avet", "predicate": predicate, "objects": list(objects), "limit": limit}
    req = urllib.request.Request(
        f"{endpoint.rstrip('/')}/xrpc/{QUERY_NSID}",
        data=json.dumps(body).encode(), headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read()).get("entities", [])
    except Exception:
        return []


def search_places(endpoint: str, query: str, labels=None, limit: int = 20) -> list[dict]:
    """Name search ranked by query-token overlap. Optional label filter (kebab keywords).
    Returns [{id, name, label, score}], best first."""
    qt = query_tokens(query)
    if not qt:
        return []
    want = None
    if labels:
        want = {l if str(l).startswith(":") else f":{l}" for l in labels}
    out = []
    for e in _avet(endpoint, "feature/name-token", qt):
        stored, name, label = set(), None, None
        for c in e.get("claims", []):
            p, v = c.get("pred"), c.get("value")
            if p == "feature/name-token":
                stored.add(v)
            elif p == "feature/name":
                name = v
            elif p == "feature/label":
                label = v
        if want is not None and label not in want:
            continue
        score = len(stored & qt)
        if score:
            out.append({"id": e.get("id"), "name": name, "label": label, "score": score})
    out.sort(key=lambda r: (-r["score"], (r["name"] or r["id"] or "")))
    return out[:limit]
