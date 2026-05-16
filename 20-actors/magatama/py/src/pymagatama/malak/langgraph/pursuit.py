"""pursuit — LangGraph chain for active actor / infrastructure pursuit.

Each pursuit step is a node that:
  1. Classifies a known identifier (URL / domain / actor-name / LINE id /
     bank-account / wallet)
  2. Generates an OSINT search plan (search queries + WHOIS + cert.sh + DNS)
  3. Pushes the plan to a `pursuit_request` table (RW), so a separate worker
     (or the agent loop) can execute the lookups and feed results back.
  4. Persists new identifiers to the appropriate vertex/edge tables when
     results return.

This module is intentionally I/O-light: the heavy OSINT (HTTP fetch, whois,
search APIs) is performed by the calling agent loop using its tools
(`WebSearch`, `WebFetch`). The chain coordinates *what* to look up and *what
to do* with results.

Use:
    from pymagatama.malak.langgraph.pursuit import build_pursuit_graph, plan_queries

    plan = plan_queries(["leedsec.com", "村上世彰", "https://line.me/ti/p/-JrMTzcGJP"])
    # → returns dict of OSINT queries to dispatch
"""

from __future__ import annotations

import re
from typing import Any, TypedDict
from urllib.parse import urlparse


URL_RE = re.compile(r"https?://[^\s<>\"'】」]+", re.IGNORECASE)
LINE_P2P_RE = re.compile(r"line\.me/ti/p/([A-Za-z0-9_\-]+)")
LINE_OC_RE = re.compile(r"line\.me/ti/g2?/([A-Za-z0-9_\-]+)")
DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9\-\.]+\.[a-z]{2,}$", re.IGNORECASE)
JP_NAME_RE = re.compile(r"^[一-龥ァ-ヶー々]{2,8}(?:\s+[一-龥ァ-ヶー々]{2,8})?$")
BTC_RE = re.compile(r"^(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$")
ETH_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def classify_identifier(s: str) -> str:
    """Return one of: url | domain | line-p2p | line-open-chat | btc | eth | jp-name | unknown."""
    s = s.strip()
    if URL_RE.match(s):
        if LINE_P2P_RE.search(s):
            return "line-p2p"
        if LINE_OC_RE.search(s):
            return "line-open-chat"
        return "url"
    if DOMAIN_RE.match(s):
        return "domain"
    if BTC_RE.match(s):
        return "btc"
    if ETH_RE.match(s):
        return "eth"
    if JP_NAME_RE.match(s):
        return "jp-name"
    return "unknown"


def plan_queries(identifier: str) -> list[dict[str, str]]:
    """Generate OSINT lookups for an identifier.

    Each plan entry is dict with keys: kind, query, why.
    `kind` indicates which agent tool to use:
      - search    → WebSearch
      - fetch     → WebFetch
      - whois     → whois lookup
      - dns       → DNS query
      - crtsh     → crt.sh certificate transparency
    """
    kind = classify_identifier(identifier)
    if kind in ("url", "domain"):
        host = urlparse(identifier).netloc or identifier
        host = host.split(":")[0]
        sld = host
        return [
            {"kind": "fetch",  "query": f"https://{host}",                              "why": "live content snapshot"},
            {"kind": "whois",  "query": host,                                            "why": "registrar / creation date / NS"},
            {"kind": "dns",    "query": host,                                            "why": "A/MX/NS records — current hosting"},
            {"kind": "crtsh",  "query": f"https://crt.sh/?q={host}&output=json",        "why": "TLS cert history / sibling subdomains"},
            {"kind": "search", "query": f'"{host}" 詐欺 OR phishing OR scam',           "why": "public abuse reports"},
            {"kind": "search", "query": f'"{host}" 警察 OR 国民生活センター OR 注意喚起', "why": "JP authority warnings"},
        ]
    if kind == "line-p2p":
        line_id = LINE_P2P_RE.search(identifier).group(1)  # type: ignore[union-attr]
        return [
            {"kind": "search", "query": f'"{line_id}" line OR LINE 詐欺 OR scam', "why": "LINE handle reports"},
            {"kind": "search", "query": f'"line.me/ti/p/{line_id}" 詐欺',         "why": "URL-form abuse reports"},
        ]
    if kind == "line-open-chat":
        token = LINE_OC_RE.search(identifier).group(1)  # type: ignore[union-attr]
        return [
            {"kind": "search", "query": f'"{token}" line open chat 詐欺',          "why": "Open Chat token abuse reports"},
        ]
    if kind in ("btc", "eth"):
        return [
            {"kind": "fetch",  "query": f"https://blockchair.com/search?q={identifier}",         "why": "block explorer summary"},
            {"kind": "search", "query": f'"{identifier}" wallet 詐欺 OR scam OR sanctions',     "why": "wallet abuse + sanctions reports"},
            {"kind": "fetch",  "query": f"https://api.chainabuse.com/v1/reports?address={identifier}", "why": "ChainAbuse reports"},
        ]
    if kind == "jp-name":
        return [
            {"kind": "search", "query": f'"{identifier}" 詐欺 OR 逮捕 OR 警察 OR 被害',         "why": "criminal mention search"},
            {"kind": "search", "query": f'"{identifier}" LINE OR インスタ OR Twitter',           "why": "social presence"},
        ]
    return [
        {"kind": "search", "query": f'"{identifier}" 詐欺 OR fraud', "why": "generic OSINT seed"},
    ]


# ── LangGraph state ───────────────────────────────────────────────────
class PursuitState(TypedDict, total=False):
    identifier: str
    kind: str
    plan: list[dict[str, str]]
    results: list[dict[str, Any]]   # filled by agent loop / external worker
    new_identifiers: list[str]      # discovered via results
    error: str


def classify_node(state: PursuitState) -> dict:
    ident = state.get("identifier", "")
    return {"kind": classify_identifier(ident)}


def plan_node(state: PursuitState) -> dict:
    ident = state.get("identifier", "")
    return {"plan": plan_queries(ident)}


def harvest_new_identifiers_node(state: PursuitState) -> dict:
    """Scan `results` for new identifiers (URLs, names, accounts).

    Caller is expected to attach raw text from WebSearch/WebFetch into
    `results[i].text`. We harvest patterns and emit `new_identifiers` so the
    agent can recurse.
    """
    results = state.get("results", []) or []
    text = "\n".join(str(r.get("text", "")) for r in results)
    new = set()
    for m in URL_RE.findall(text):
        new.add(m.rstrip(".,;)"))
    for line in text.splitlines():
        line = line.strip()
        if 2 <= len(line) <= 30 and JP_NAME_RE.match(line):
            new.add(line)
    return {"new_identifiers": sorted(new)[:50]}


def build_pursuit_graph():
    from langgraph.graph import StateGraph, END
    g = StateGraph(PursuitState)
    g.add_node("classify", classify_node)
    g.add_node("plan", plan_node)
    g.add_node("harvest", harvest_new_identifiers_node)
    g.set_entry_point("classify")
    g.add_edge("classify", "plan")
    g.add_edge("plan", "harvest")
    g.add_edge("harvest", END)
    return g.compile()
