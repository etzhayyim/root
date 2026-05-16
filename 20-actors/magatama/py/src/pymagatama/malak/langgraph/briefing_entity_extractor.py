"""briefing_entity_extractor — extract entities/dates/dependencies from briefing text.

Phase 0 PoC = regex + structural patterns only (no LLM call). Phase 1 will
add LLM (qwen3-30b) JSON extraction with the same output shape so consumers
do not need to change.

Returns:

    {
      "entities": [
        {"entity_id": str, "entity_kind": str, "display_name": str,
         "identifier": str, "external_url": str, "confidence": float,
         "extraction_source": "regex"|"llm", "first_seen_in": str (section_no)},
        ...
      ],
      "date_events": [
        {"event_id": str, "event_kind": str, "event_label": str,
         "event_date": str (raw), "iso_date": str, "precision": "day"|"month"|"year"|"quarter",
         "confidence": float},
        ...
      ],
      "dependencies": [
        {"src": "section_no or briefing_id", "dst": "entity_id or briefing_id",
         "dep_kind": str, "required_status": str},
        ...
      ],
      "org_mentions": [
        {"path": str, "role": str, "first_seen_in": str},
        ...
      ],
      "url_citations": [
        {"url": str, "label": str, "cite_kind": str, "first_seen_in": str},
        ...
      ]
    }
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List


# ── Regex patterns ───────────────────────────────────────────────────────

_RE_ADR     = re.compile(r"\bADR[- ](?P<id>\d{4}(?:-\d+)?|\d{10,})\b", re.IGNORECASE)
_RE_PHASE   = re.compile(r"\bPhase\s*(?P<n>\d+)\b", re.IGNORECASE)
_RE_NSID    = re.compile(r"\b(?P<nsid>ai\.gftd\.(?:apps|host|signal|vault|kagami|projector|tool|mcp|kyber|magatama|governance|contract|consent|audit|coverage|dm2|identity|capability|conversation|serve|invoke|policy|risingwave|brief|user|notice|gov|webyubin|spiff|aspect|sub|moneyforward|monyforward|api)\.[a-zA-Z0-9_.]+)")
_RE_VERTEX  = re.compile(r"\b(?P<table>(?:vertex|edge|mv|view|dim)_[a-z][a-zA-Z0-9_]+)")
_RE_URL     = re.compile(r"https?://[^\s\)]+", re.IGNORECASE)
_RE_PATH    = re.compile(r"`(?P<path>(?:[0-9]{2}-)?[a-z0-9_\-./]+(?:\.(?:md|json|jsonc|yaml|yml|ts|tsx|py|toml|csv|sql|bpmn|sh))?)`")
_RE_DATE    = re.compile(
    r"\b(?P<y>20\d{2})[-/年](?P<m>\d{1,2})(?:[-/月](?P<d>\d{1,2})日?)?(?:\s*(?:JST|UTC))?"
)
_RE_QUARTER = re.compile(r"\b(?P<y>20\d{2})-?(?P<q>Q[1-4])\b")
_RE_PERSON  = re.compile(
    r"(?:Kunal\s+Bakshi|Jun\s+Kawasaki|河崎\s*[一-龥]{1,4}|"
    r"バクシ\s*クナル|板倉陽一郎|amanomibashira\s*代表|nakamura|sales-mgr)"
)
_RE_LAW     = re.compile(
    r"(?:個人情報保護法|警察法|警察庁通達\s*R\s*\d+|電気通信事業法\s*§?\s*\d+|刑事訴訟法\s*§?\s*\d+|"
    r"特定電子メール法\s*§?\s*\d*|公務員倫理規程|個情委ガイドライン|GDPR|EU\s*AI\s*Act|FATF)"
)
_RE_DEPENDS = re.compile(
    r"(?P<head>[a-zA-Z0-9\.\-_]{3,40})\s*(?:を|は|が)?\s*(?:依存|要|必要|requires|depends\s+on|blocked\s+by)\s*[: ]?\s*(?P<tail>[a-zA-Z0-9\.\-_]{3,60})"
)


def _id(prefix: str, *seeds: str) -> str:
    h = hashlib.sha256(":".join(seeds).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{h}"


def _norm_iso_date(raw: str, y: str, m: str, d: str | None) -> tuple[str, str]:
    yy = int(y)
    mm = int(m)
    if d:
        dd = int(d)
        iso = f"{yy:04d}-{mm:02d}-{dd:02d}"
        return iso, "day"
    iso = f"{yy:04d}-{mm:02d}-01"
    return iso, "month"


def _norm_quarter(y: str, q: str) -> tuple[str, str]:
    yy = int(y)
    qn = int(q[1])
    start_month = (qn - 1) * 3 + 1
    iso = f"{yy:04d}-{start_month:02d}-01"
    return iso, "quarter"


def extract(text: str, section_no: str = "") -> Dict[str, Any]:
    entities: List[Dict[str, Any]] = []
    date_events: List[Dict[str, Any]] = []
    dependencies: List[Dict[str, Any]] = []
    url_citations: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    def _push_entity(kind: str, name: str, **extra: Any) -> None:
        eid = _id(f"brfent-{kind[:3]}", kind, name)
        if eid in seen_ids:
            return
        seen_ids.add(eid)
        entities.append({
            "entity_id":   eid,
            "entity_kind": kind,
            "display_name": name,
            "identifier":  extra.get("identifier", ""),
            "external_url": extra.get("external_url", ""),
            "confidence":  extra.get("confidence", 0.9),
            "extraction_source": "regex",
            "first_seen_in": section_no,
        })

    # ADRs
    for m in _RE_ADR.finditer(text):
        adr_id = m.group("id")
        _push_entity("adr", f"ADR-{adr_id}", identifier=f"ADR-{adr_id}", confidence=0.95)

    # Phases (Phase 0 / Phase 1 / ...) — concept entities for graph traversal
    for m in _RE_PHASE.finditer(text):
        n = m.group("n")
        _push_entity("concept", f"Phase {n}", identifier=f"phase-{n}", confidence=0.85)

    # NSIDs (treat as project/lexicon entities)
    for m in _RE_NSID.finditer(text):
        nsid = m.group("nsid")
        _push_entity("project", nsid, identifier=nsid, confidence=0.98)

    # RW table references
    for m in _RE_VERTEX.finditer(text):
        tbl = m.group("table")
        _push_entity("concept", tbl, identifier=tbl, confidence=0.9)

    # Laws / frameworks
    for m in _RE_LAW.finditer(text):
        name = m.group(0).strip()
        _push_entity("law", name, identifier=name, confidence=0.92)

    # Persons
    for m in _RE_PERSON.finditer(text):
        name = m.group(0).strip()
        _push_entity("person", name, identifier=name, confidence=0.8)

    # File paths
    for m in _RE_PATH.finditer(text):
        path = m.group("path")
        if "/" not in path and "." not in path:
            continue
        _push_entity("project", path, identifier=path, confidence=0.85)

    # URLs
    for m in _RE_URL.finditer(text):
        url = m.group(0).rstrip(".,);:")
        eid = _id("brfent-url", "url", url)
        if eid not in seen_ids:
            seen_ids.add(eid)
            entities.append({
                "entity_id":   eid,
                "entity_kind": "url",
                "display_name": url,
                "identifier":  "",
                "external_url": url,
                "confidence":  1.0,
                "extraction_source": "regex",
                "first_seen_in": section_no,
            })
        url_citations.append({
            "url": url,
            "label": "",
            "cite_kind": "external",
            "first_seen_in": section_no,
        })

    # Dates
    for m in _RE_DATE.finditer(text):
        raw = m.group(0)
        iso, prec = _norm_iso_date(raw, m.group("y"), m.group("m"), m.group("d"))
        date_events.append({
            "event_id":  _id("brfdt", iso, raw),
            "event_kind": "milestone",
            "event_label": raw,
            "event_date": raw,
            "iso_date":  iso,
            "precision": prec,
            "confidence": 0.85,
        })
    for m in _RE_QUARTER.finditer(text):
        iso, prec = _norm_quarter(m.group("y"), m.group("q"))
        date_events.append({
            "event_id":  _id("brfdt", iso, m.group(0)),
            "event_kind": "milestone",
            "event_label": m.group(0),
            "event_date": m.group(0),
            "iso_date":  iso,
            "precision": prec,
            "confidence": 0.75,
        })

    # Dependencies (heuristic, low confidence)
    for m in _RE_DEPENDS.finditer(text):
        dependencies.append({
            "src": section_no or "self",
            "dst": m.group("tail"),
            "dep_kind": "requires",
            "required_status": "",
            "confidence": 0.5,
        })

    return {
        "entities": entities,
        "date_events": date_events,
        "dependencies": dependencies,
        "url_citations": url_citations,
        "org_mentions": [],  # filled by separate pass in briefing.py based on facts
    }
