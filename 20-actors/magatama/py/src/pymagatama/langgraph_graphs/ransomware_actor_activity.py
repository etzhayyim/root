"""ransomware_actor_activity — Malak LangGraph for recent ransomware activity.

Graph:
  START -> collect_sources -> normalize_events -> pregel_score -> publish_yabai -> persist_tick -> END

The graph is intentionally passive OSINT only. It classifies public feed items
and .onion crawl metadata already held by the platform; it does not probe,
exploit, negotiate, or contact ransomware infrastructure.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, TypedDict


MALAK_DID = "did:web:malak.gftd.ai"
YABAI_DID = "did:web:yabai.gftd.ai"
ACTOR_ID = "ransomware-actor-activity"


class RansomwareActorActivityState(TypedDict, total=False):
    lookback_hours: int
    max_items: int
    sources: list[dict[str, Any]]
    raw_items: list[dict[str, Any]]
    events: list[dict[str, Any]]
    pregel_summary: dict[str, Any]
    yabai_publish: dict[str, Any]
    tick_vertex_id: str
    ok: bool
    error: str | None


@dataclass(frozen=True)
class FeedSource:
    source_id: str
    url: str
    source_kind: str
    authority: float


DEFAULT_SOURCES: tuple[FeedSource, ...] = (
    FeedSource(
        "cisa-known-exploited-vulnerabilities",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        "kev-json",
        0.95,
    ),
    FeedSource(
        "cisa-alerts",
        "https://www.cisa.gov/news-events/cybersecurity-advisories/all.xml",
        "rss",
        0.90,
    ),
    FeedSource(
        "the-dfir-report",
        "https://thedfirreport.com/feed/",
        "rss",
        0.78,
    ),
    FeedSource(
        "bleepingcomputer-security",
        "https://www.bleepingcomputer.com/feed/",
        "rss",
        0.65,
    ),
)


RANSOMWARE_TERMS = (
    "ransomware",
    "ransom",
    "extortion",
    "double extortion",
    "data leak",
    "leak site",
    "decryptor",
    "lockbit",
    "blackcat",
    "alphv",
    "clop",
    "akira",
    "black basta",
    "play ransomware",
    "royal ransomware",
    "hunters international",
    "qilin",
)

ONION_SOURCE_ID = "onion-crawl-metadata"
ONION_ENTITY_PREFIX = "onion-site"


def _cap(value: Any, default: int, low: int, high: int) -> int:
    try:
        return max(low, min(int(value), high))
    except Exception:
        return default


def _sha(*parts: Any) -> str:
    raw = "\x1f".join(str(p or "") for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _fetch_text(url: str, *, timeout: float = 12.0) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/rss+xml, application/json, text/xml, */*",
            "User-Agent": "malak-ransomware-activity/1.0 (+https://malak.gftd.ai)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.getcode()), resp.read(1_500_000).decode("utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return -1, f"fetch_error: {e}"


def _fetch_onion_metadata(*, limit: int) -> list[dict[str, Any]]:
    """Read already-crawled onion metadata from RisingWave.

    This is intentionally passive. The active crawl is owned by
    onion_crawl_seeds; this actor only consumes rows already in vertex_onion_*.
    """
    try:
        from pymagatama.db_sync import sync_cursor
    except Exception:
        return []

    sql = """
        WITH page_rollup AS (
          SELECT
            onion_host,
            MAX(crawled_at) AS last_crawled_at,
            COUNT(*) AS ransomware_page_count,
            MAX(title) AS sample_title,
            MAX(text_snippet) AS sample_snippet,
            MAX(threat_indicators) AS sample_threat_indicators,
            MAX(risk_score) AS max_page_risk
          FROM vertex_onion_page
          WHERE onion_host IS NOT NULL
            AND (
              LOWER(COALESCE(category, '')) LIKE '%ransomware%'
              OR LOWER(COALESCE(threat_indicators, '')) LIKE '%ransomware%'
              OR LOWER(COALESCE(threat_indicators, '')) LIKE '%leak site%'
              OR LOWER(COALESCE(text_snippet, '')) LIKE '%ransomware%'
              OR LOWER(COALESCE(text_snippet, '')) LIKE '%decryptor%'
            )
          GROUP BY onion_host
        )
        SELECT
          COALESCE(s.onion_host, p.onion_host) AS onion_host,
          s.site_did,
          COALESCE(s.category, 'ransomware') AS site_category,
          COALESCE(s.risk_score, p.max_page_risk, 0) AS risk_score,
          COALESCE(s.page_count, 0) AS page_count,
          s.reachable,
          s.first_seen,
          COALESCE(s.last_seen, p.last_crawled_at) AS last_seen,
          p.ransomware_page_count,
          p.sample_title,
          p.sample_snippet,
          p.sample_threat_indicators
        FROM page_rollup p
        LEFT JOIN vertex_onion_site s ON s.onion_host = p.onion_host
        WHERE COALESCE(s.onion_host, p.onion_host) IS NOT NULL
        UNION ALL
        SELECT
          s.onion_host,
          s.site_did,
          COALESCE(s.category, 'ransomware') AS site_category,
          COALESCE(s.risk_score, 0) AS risk_score,
          COALESCE(s.page_count, 0) AS page_count,
          s.reachable,
          s.first_seen,
          s.last_seen,
          0 AS ransomware_page_count,
          s.title AS sample_title,
          NULL AS sample_snippet,
          NULL AS sample_threat_indicators
        FROM vertex_onion_site s
        WHERE s.onion_host IS NOT NULL
          AND LOWER(COALESCE(s.category, '')) LIKE '%ransomware%'
          AND NOT EXISTS (SELECT 1 FROM page_rollup p WHERE p.onion_host = s.onion_host)
        LIMIT %s
    """
    try:
        with sync_cursor() as cur:
            cur.execute(sql, (max(1, min(int(limit), 100)),))
            cols = [d[0] for d in cur.description] if cur.description else []
            return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]
    except Exception:
        return []


def _strip_tags(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _rss_items(xml: str, *, limit: int) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    chunks = re.findall(r"<item[\s\S]*?</item>|<entry[\s\S]*?</entry>", xml, flags=re.I)
    for chunk in chunks[:limit]:
        title = _first_tag(chunk, "title")
        link = _first_tag(chunk, "link")
        if not link:
            href = re.search(r"<link[^>]+href=[\"']([^\"']+)[\"']", chunk, flags=re.I)
            link = href.group(1) if href else ""
        summary = _first_tag(chunk, "description") or _first_tag(chunk, "summary")
        published = _first_tag(chunk, "pubDate") or _first_tag(chunk, "published") or _first_tag(chunk, "updated")
        out.append({
            "title": _strip_tags(title)[:300],
            "url": _strip_tags(link)[:500],
            "summary": _strip_tags(summary)[:1000],
            "published": _strip_tags(published)[:120],
        })
    return out


def _first_tag(xml: str, tag: str) -> str:
    m = re.search(rf"<{tag}[^>]*>([\s\S]*?)</{tag}>", xml, flags=re.I)
    return m.group(1).strip() if m else ""


def _kev_items(body: str, *, limit: int) -> list[dict[str, str]]:
    try:
        payload = json.loads(body)
    except Exception:
        return []
    rows = payload.get("vulnerabilities") if isinstance(payload, dict) else []
    out: list[dict[str, str]] = []
    if not isinstance(rows, list):
        return out
    for row in rows[: limit * 4]:
        if not isinstance(row, dict):
            continue
        name = str(row.get("vulnerabilityName") or "")
        notes = " ".join(str(row.get(k) or "") for k in ("shortDescription", "notes", "knownRansomwareCampaignUse"))
        if not _is_ransomware_relevant(f"{name} {notes}"):
            continue
        cve = str(row.get("cveID") or "")
        out.append({
            "title": f"{cve} {name}".strip()[:300],
            "url": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            "summary": notes[:1000],
            "published": str(row.get("dateAdded") or ""),
        })
        if len(out) >= limit:
            break
    return out


def _onion_item(row: dict[str, Any]) -> dict[str, Any]:
    host = str(row.get("onion_host") or "").strip().lower()
    title = str(row.get("sample_title") or f"Ransomware onion site observed: {host}")[:300]
    indicators = str(row.get("sample_threat_indicators") or "")
    snippet = str(row.get("sample_snippet") or "")
    ransomware_pages = int(row.get("ransomware_page_count") or 0)
    page_count = int(row.get("page_count") or 0)
    risk_score = int(row.get("risk_score") or 0)
    summary = (
        f"Existing onion crawl metadata classified {host} as ransomware/leak-site infrastructure. "
        f"ransomware_pages={ransomware_pages}; page_count={page_count}; "
        f"reachable={row.get('reachable')}; risk_score={risk_score}; indicators={indicators[:200]}; "
        f"snippet={snippet[:320]}"
    )
    return {
        "title": title,
        "url": f"http://{host}/",
        "summary": summary[:1000],
        "published": str(row.get("last_seen") or row.get("first_seen") or ""),
        "sourceId": ONION_SOURCE_ID,
        "sourceAuthority": 0.72,
        "sourceKind": "onion-metadata",
        "onionHost": host,
        "siteDid": str(row.get("site_did") or ""),
        "ransomwarePageCount": ransomware_pages,
        "pageCount": page_count,
        "onionRiskScore": risk_score,
    }


def _is_ransomware_relevant(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in RANSOMWARE_TERMS)


def _extract_actor(text: str) -> str:
    lower = text.lower()
    candidates = {
        "lockbit": "LockBit",
        "blackcat": "ALPHV/BlackCat",
        "alphv": "ALPHV/BlackCat",
        "clop": "Cl0p",
        "akira": "Akira",
        "black basta": "Black Basta",
        "play ransomware": "Play",
        "hunters international": "Hunters International",
        "qilin": "Qilin",
    }
    for needle, label in candidates.items():
        if needle in lower:
            return label
    return "unknown-ransomware-actor"


def _extract_indicators(text: str) -> dict[str, list[str]]:
    domains = sorted(set(re.findall(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b", text)))[:20]
    cves = sorted(set(re.findall(r"\bCVE-\d{4}-\d{4,7}\b", text, flags=re.I)))[:20]
    wallets = sorted(set(re.findall(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b", text)))[:10]
    return {"domains": domains, "cves": [c.upper() for c in cves], "wallets": wallets}


def _onion_slug(host: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")[:96] or _sha(host)


def _event_entity_id(event: dict[str, Any]) -> str:
    host = str(event.get("onionHost") or "")
    if host.endswith(".onion"):
        return f"{ONION_ENTITY_PREFIX}-{_onion_slug(host)}"
    actor = str(event.get("actor") or "unknown-ransomware-actor").lower()
    return f"ransomware-actor-{_onion_slug(actor)}"


def _risk_level(score_0_1: float) -> str:
    score = score_0_1 * 100.0
    if score >= 95:
        return "deny"
    if score >= 85:
        return "challenge"
    if score >= 70:
        return "monitor"
    return "clean"


def collect_sources(state: RansomwareActorActivityState) -> dict:
    max_items = _cap(state.get("max_items"), 25, 1, 100)
    raw_items: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []

    for src in DEFAULT_SOURCES:
        status, body = _fetch_text(src.url)
        sources.append({
            "sourceId": src.source_id,
            "url": src.url,
            "kind": src.source_kind,
            "authority": src.authority,
            "status": status,
        })
        if status not in (200, 201):
            continue
        if src.source_kind == "kev-json":
            items = _kev_items(body, limit=max_items)
        else:
            items = _rss_items(body, limit=max_items)
        for item in items:
            item["sourceId"] = src.source_id
            item["sourceAuthority"] = src.authority
            raw_items.append(item)
            if len(raw_items) >= max_items:
                break
        if len(raw_items) >= max_items:
            break

    sources.append({
        "sourceId": ONION_SOURCE_ID,
        "url": "risingwave://vertex_onion_site+vertex_onion_page",
        "kind": "onion-metadata",
        "authority": 0.72,
        "status": "local",
    })
    onion_limit = max_items
    onion_rows = _fetch_onion_metadata(limit=onion_limit)
    for row in onion_rows:
        item = _onion_item(row)
        if item.get("onionHost"):
            raw_items.append(item)
            if sum(1 for x in raw_items if x.get("sourceId") == ONION_SOURCE_ID) >= onion_limit:
                break

    return {"sources": sources, "raw_items": raw_items, "ok": True}


def normalize_events(state: RansomwareActorActivityState) -> dict:
    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in state.get("raw_items") or []:
        title = str(item.get("title") or "")
        summary = str(item.get("summary") or "")
        url = str(item.get("url") or "")
        text = f"{title}\n{summary}\n{url}"
        if not _is_ransomware_relevant(text):
            continue
        event_id = _sha(item.get("sourceId"), title, url)
        if event_id in seen:
            continue
        seen.add(event_id)
        parsed_url = urllib.parse.urlparse(url if "://" in url else "")
        indicators = _extract_indicators(text)
        events.append({
            "eventId": event_id,
            "actor": _extract_actor(text),
            "title": title[:300],
            "summary": summary[:1000],
            "sourceId": item.get("sourceId"),
            "sourceKind": item.get("sourceKind") or "public-feed",
            "sourceAuthority": float(item.get("sourceAuthority") or 0.5),
            "url": url[:500],
            "host": parsed_url.netloc,
            "onionHost": item.get("onionHost") or (parsed_url.netloc if parsed_url.netloc.endswith(".onion") else ""),
            "siteDid": item.get("siteDid") or "",
            "ransomwarePageCount": int(item.get("ransomwarePageCount") or 0),
            "pageCount": int(item.get("pageCount") or 0),
            "published": item.get("published") or "",
            "indicators": indicators,
            "activityKind": "ransomware-activity",
        })
    return {"events": events}


def pregel_score(state: RansomwareActorActivityState) -> dict:
    """PREGEL-style evidence scoring over normalized ransomware claims.

    Score components:
      source authority + explicit ransomware terms + actor attribution +
      technical indicators + recency metadata.
    """
    scored: list[dict[str, Any]] = []
    actor_counts: dict[str, int] = {}
    active = 0
    review = 0
    for event in state.get("events") or []:
        text = f"{event.get('title','')} {event.get('summary','')}".lower()
        evidence = float(event.get("sourceAuthority") or 0.5)
        if _is_ransomware_relevant(text):
            evidence += 0.18
        if event.get("actor") and event.get("actor") != "unknown-ransomware-actor":
            evidence += 0.12
        indicators = event.get("indicators") or {}
        indicator_count = sum(len(indicators.get(k) or []) for k in ("domains", "cves", "wallets"))
        evidence += min(0.15, indicator_count * 0.03)
        if event.get("published"):
            evidence += 0.05
        score = max(0.0, min(1.0, evidence))
        status = "active" if score >= 0.82 else "needs-review" if score >= 0.58 else "weak"
        if status == "active":
            active += 1
        elif status == "needs-review":
            review += 1
        actor = str(event.get("actor") or "unknown-ransomware-actor")
        actor_counts[actor] = actor_counts.get(actor, 0) + 1
        scored.append({**event, "pregelScore": round(score, 3), "pregelStatus": status})

    top_actors = [
        {"actor": actor, "eventCount": count}
        for actor, count in sorted(actor_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    ]
    return {
        "events": scored,
        "pregel_summary": {
            "evaluated": len(scored),
            "active": active,
            "needsReview": review,
            "onionSites": sum(1 for event in scored if str(event.get("onionHost") or "").endswith(".onion")),
            "topActors": top_actors,
            "generatedAt": _now_iso(),
        },
    }


def _publish_yabai_rows(events: list[dict[str, Any]]) -> dict[str, int]:
    try:
        from pymagatama.db_sync import sync_cursor
    except Exception:
        return {"entities": 0, "evidence": 0, "risks": 0, "alerts": 0}

    now = _now_iso()
    today = _today()
    entity_ids: set[str] = set()
    entities = evidence = risks = alerts = 0
    with sync_cursor() as cur:
        for event in events:
            score = float(event.get("pregelScore") or 0.0)
            if score < 0.58:
                continue
            entity_id = _event_entity_id(event)
            entity_ids.add(entity_id)
            onion_host = str(event.get("onionHost") or "")
            entity_type = "onion_site" if onion_host.endswith(".onion") else "threat_actor"
            entity_name = onion_host or str(event.get("actor") or "unknown-ransomware-actor")
            entity_value = onion_host or str(event.get("actor") or "")
            entity_vid = f"at://{YABAI_DID}/ai.gftd.apps.yabai.entity/{entity_id}"
            cur.execute(
                "INSERT INTO vertex_yabai_entity ("
                "vertex_id, _seq, created_date, sensitivity_ord, owner_did, rkey, repo, "
                "entity_id, entity_type, name, value, canonical_name, aliases, source, "
                "created_at, org_id, user_id, actor_id"
                ") VALUES ("
                "%s, %s, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
                ") ON CONFLICT (vertex_id) DO UPDATE SET "
                "name = EXCLUDED.name, value = EXCLUDED.value, canonical_name = EXCLUDED.canonical_name, "
                "source = EXCLUDED.source, created_at = EXCLUDED.created_at",
                (
                    entity_vid, None, today, 300, YABAI_DID,
                    entity_id, YABAI_DID,
                    entity_id, entity_type, entity_name[:512], entity_value[:512],
                    entity_name[:512], "", "ransomware-actor-activity",
                    now, "gftd", "system", ACTOR_ID,
                ),
            )
            entities += 1

            evidence_id = f"ransomware-activity-{event.get('eventId')}"
            evidence_vid = f"at://{YABAI_DID}/ai.gftd.apps.yabai.evidence/{evidence_id}"
            desc = json.dumps(
                {
                    "eventId": event.get("eventId"),
                    "sourceId": event.get("sourceId"),
                    "sourceKind": event.get("sourceKind"),
                    "url": event.get("url"),
                    "host": event.get("host"),
                    "onionHost": onion_host,
                    "siteDid": event.get("siteDid"),
                    "actor": event.get("actor"),
                    "indicators": event.get("indicators"),
                    "pregelScore": score,
                    "pregelStatus": event.get("pregelStatus"),
                    "ransomwarePageCount": event.get("ransomwarePageCount"),
                    "pageCount": event.get("pageCount"),
                },
                ensure_ascii=False,
            )
            cur.execute(
                "INSERT INTO vertex_yabai_evidence ("
                "vertex_id, _seq, created_date, sensitivity_ord, owner_did, rkey, repo, "
                "evidence_id, entity_id, category, confidence, severity, probability, "
                "source, source_reliability, jurisdiction, summary, description, "
                "verification_id, occurred_at, created_at, org_id, user_id, actor_id"
                ") VALUES ("
                "%s, %s, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
                ") ON CONFLICT (vertex_id) DO UPDATE SET "
                "confidence = EXCLUDED.confidence, severity = EXCLUDED.severity, "
                "summary = EXCLUDED.summary, description = EXCLUDED.description, occurred_at = EXCLUDED.occurred_at",
                (
                    evidence_vid, None, today, 300, YABAI_DID,
                    evidence_id, YABAI_DID,
                    evidence_id, entity_id, "CriminalEvidence",
                    score, max(6, min(10, int(round(score * 10)))), score,
                    "ransomware-actor-activity", "medium", "global",
                    str(event.get("title") or "Ransomware actor activity observed")[:512],
                    desc[:4000], "", str(event.get("published") or now)[:64], now,
                    "gftd", "system", ACTOR_ID,
                ),
            )
            evidence += 1

            risk_id = f"risk-{entity_id}"
            risk_vid = f"at://{YABAI_DID}/ai.gftd.apps.yabai.risk/{risk_id}"
            level = _risk_level(score)
            cur.execute(
                "INSERT INTO vertex_yabai_risk ("
                "vertex_id, _seq, created_date, sensitivity_ord, owner_did, rkey, repo, "
                "entity_id, entity_type, entity_name, entity_value, risk_score, "
                "well_becoming_score, penalty, penalty_score, wb_score, info_risk, "
                "level, evidence_count, categories, scored_at, org_id, user_id, actor_id"
                ") VALUES ("
                "%s, %s, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
                ") ON CONFLICT (vertex_id) DO UPDATE SET "
                "risk_score = GREATEST(COALESCE(vertex_yabai_risk.risk_score, 0), EXCLUDED.risk_score), "
                "level = EXCLUDED.level, evidence_count = EXCLUDED.evidence_count, "
                "categories = EXCLUDED.categories, scored_at = EXCLUDED.scored_at",
                (
                    risk_vid, None, today, 300, YABAI_DID,
                    risk_id, YABAI_DID,
                    entity_id, entity_type, entity_name[:512], entity_value[:512], round(score * 100, 2),
                    max(0.0, round(100.0 - score * 100.0, 2)), round(score * 100, 2),
                    round(score * 100, 2), max(0.0, round(100.0 - score * 100.0, 2)), round(score * 100, 2),
                    level, 1, "CriminalEvidence,RansomwareActivity", now,
                    "gftd", "system", ACTOR_ID,
                ),
            )
            risks += 1

            if score >= 0.82:
                alert_id = f"alert-{evidence_id}"
                alert_vid = f"at://{YABAI_DID}/ai.gftd.apps.yabai.alert/{alert_id}"
                cur.execute(
                    "INSERT INTO vertex_yabai_alert ("
                    "vertex_id, _seq, created_date, sensitivity_ord, owner_did, rkey, repo, "
                    "alert_id, entity_id, entity_type, entity_name, risk_score, alert_level, "
                    "status, categories, created_at, org_id, user_id, actor_id"
                    ") VALUES ("
                    "%s, %s, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
                    ") ON CONFLICT (vertex_id) DO UPDATE SET "
                    "risk_score = EXCLUDED.risk_score, alert_level = EXCLUDED.alert_level, "
                    "status = EXCLUDED.status, categories = EXCLUDED.categories",
                    (
                        alert_vid, None, today, 300, YABAI_DID,
                        alert_id, YABAI_DID,
                        alert_id, entity_id, entity_type, entity_name[:512],
                        round(score * 100, 2), level, "open",
                        "CriminalEvidence,RansomwareActivity", now,
                        "gftd", "system", ACTOR_ID,
                    ),
                )
                alerts += 1
    return {"entities": entities, "evidence": evidence, "risks": risks, "alerts": alerts, "uniqueEntities": len(entity_ids)}


def publish_yabai(state: RansomwareActorActivityState) -> dict:
    try:
        result = _publish_yabai_rows(state.get("events") or [])
        return {"yabai_publish": {**result, "ok": True}}
    except Exception as e:  # noqa: BLE001
        return {"yabai_publish": {"ok": False, "error": str(e)}}


def persist_tick(state: RansomwareActorActivityState) -> dict:
    summary = state.get("pregel_summary") or {}
    events = state.get("events") or []
    details = json.dumps({
        "summary": summary,
        "yabaiPublish": state.get("yabai_publish") or {},
        "events": events[:25],
        "sources": state.get("sources") or [],
    }, ensure_ascii=False)
    rationale = (
        f"Passive ransomware actor activity ingest evaluated {summary.get('evaluated', 0)} "
        f"events; active={summary.get('active', 0)} needsReview={summary.get('needsReview', 0)}."
    )
    try:
        from pymagatama.malak.langgraph import db_accessor

        tick = db_accessor.insert_investigation_tick(
            role_id=ACTOR_ID,
            tlp="AMBER",
            action="ransomware_actor_activity_ingest",
            details=details,
            rationale=rationale,
            state_history=[
                "collect_sources",
                "normalize_events",
                "pregel_score",
                "persist_tick",
            ],
        )
        return {"tick_vertex_id": tick, "ok": True, "error": None}
    except Exception as e:  # noqa: BLE001
        return {"tick_vertex_id": "", "ok": False, "error": str(e)}


def build_graph():
    from langgraph.graph import END, StateGraph

    builder = StateGraph(RansomwareActorActivityState)
    builder.add_node("collect_sources", collect_sources)
    builder.add_node("normalize_events", normalize_events)
    builder.add_node("pregel_score", pregel_score)
    builder.add_node("publish_yabai", publish_yabai)
    builder.add_node("persist_tick", persist_tick)
    builder.set_entry_point("collect_sources")
    builder.add_edge("collect_sources", "normalize_events")
    builder.add_edge("normalize_events", "pregel_score")
    builder.add_edge("pregel_score", "publish_yabai")
    builder.add_edge("publish_yabai", "persist_tick")
    builder.add_edge("persist_tick", END)
    return builder.compile()
