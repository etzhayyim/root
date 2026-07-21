#!/usr/bin/env python3
"""
Live houbun/contracts ingest helper.

This is an operator script for bootstrapping the law corpus directly into
RisingWave through the PG wire. It mirrors the ADR-0052 houbun table contract
and handles the current e-Gov API v2 tag/children JSON shape.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2  # kotoba-datomic-projection: ADR-2605231500 live-ingest read model
from psycopg2.extras import execute_values


REPO = Path(__file__).resolve().parents[2]
DB_URL = "REDACTED_USE_DATABASE_URL_ENV"
EGOV_BASE = "https://laws.e-gov.go.jp/api/2"
ACTOR_DID = "did:web:houbun.etzhayyim.com"
JPN_PATH_DID = f"{ACTOR_DID}:jpn:e-gov"
CONTRACTS_DID = "did:web:contracts.etzhayyim.com"

WS = re.compile(r"\s+")
NON_ALNUM = re.compile(r"[\W_]+", re.UNICODE)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "etzhayyim-houbun-live-ingest/0.1 (+https://houbun.etzhayyim.com)",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "etzhayyim-houbun-live-ingest/0.1 (+https://houbun.etzhayyim.com)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def flatten(node: Any) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return WS.sub(" ", node).strip()
    if isinstance(node, (int, float)):
        return str(node)
    if isinstance(node, list):
        return " ".join(x for x in (flatten(v) for v in node) if x).strip()
    if isinstance(node, dict):
        if "children" in node:
            return flatten(node.get("children"))
        parts: list[str] = []
        for k, v in node.items():
            if k in ("attr", "tag") or k.startswith("@") or k.startswith("_"):
                continue
            t = flatten(v)
            if t:
                parts.append(t)
        return " ".join(parts).strip()
    return ""


def children_with_tag(node: dict[str, Any], tag: str) -> list[dict[str, Any]]:
    return [c for c in node.get("children", []) if isinstance(c, dict) and c.get("tag") == tag]


def first_child(node: dict[str, Any], tag: str) -> dict[str, Any] | None:
    rows = children_with_tag(node, tag)
    return rows[0] if rows else None


def iter_articles(root: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    section_tags = {
        "Part": "PartTitle",
        "Chapter": "ChapterTitle",
        "Section": "SectionTitle",
        "Subsection": "SubsectionTitle",
        "Division": "DivisionTitle",
    }

    def visit(node: Any, section: str | None) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item, section)
            return
        if not isinstance(node, dict):
            return

        tag = node.get("tag")
        local_section = section
        title_tag = section_tags.get(str(tag))
        if title_tag:
            title_node = first_child(node, title_tag)
            title_text = flatten(title_node)
            if title_text:
                local_section = title_text

        if tag == "Article":
            title = flatten(first_child(node, "ArticleTitle"))
            caption = flatten(first_child(node, "ArticleCaption"))
            body_parts = []
            for child in node.get("children", []):
                if isinstance(child, dict) and child.get("tag") in ("ArticleTitle", "ArticleCaption"):
                    continue
                text = flatten(child)
                if text:
                    body_parts.append(text)
            body = WS.sub(" ", " ".join(body_parts)).strip()
            attr = node.get("attr") if isinstance(node.get("attr"), dict) else {}
            article_no = title or (f"第{attr.get('Num')}条" if attr.get("Num") else f"art-{len(out) + 1}")
            if article_no or body:
                out.append(
                    {
                        "article_no": article_no,
                        "title": caption or None,
                        "section": local_section,
                        "text": body,
                    }
                )
            return

        for child in node.get("children", []):
            visit(child, local_section)

    visit(root, None)
    return out


def article_hash(jurisdiction: str, statute_id: str, article_no: str, amended_at: str) -> str:
    payload = "|".join((jurisdiction or "", statute_id or "", article_no or "", amended_at or ""))
    return hashlib.blake2b(payload.encode("utf-8"), digest_size=6).hexdigest()


def statute_row(law: dict[str, Any], articles: list[dict[str, Any]]) -> tuple[Any, ...]:
    law_info = law.get("law_info") or {}
    rev = law.get("revision_info") or {}
    law_id = law_info.get("law_id") or rev.get("law_id")
    title = rev.get("law_title") or law_id
    current = now_iso()
    vertex_id = f"at://{JPN_PATH_DID}/com.etzhayyim.apps.houbun.statute/{law_id}"
    return (
        vertex_id,
        current[:10],
        JPN_PATH_DID,
        law_id,
        "jpn",
        law_id,
        title,
        title,
        law_info.get("law_type") or rev.get("law_type") or "law",
        law_info.get("promulgation_date"),
        rev.get("amendment_enforcement_date"),
        rev.get("repeal_date"),
        "e-gov",
        f"https://laws.e-gov.go.jp/law/{law_id}",
        "CC-BY-4.0",
        "ja",
        len(articles),
        current,
        current,
        "sys.houbun",
    )


def article_rows(law: dict[str, Any], statute_ref: str, articles: list[dict[str, Any]]) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    law_info = law.get("law_info") or {}
    rev = law.get("revision_info") or {}
    law_id = law_info.get("law_id")
    amended_at = rev.get("amendment_enforcement_date") or ""
    source_url = f"https://laws.e-gov.go.jp/law/{law_id}"
    current = now_iso()
    rows: list[tuple[Any, ...]] = []
    edges: list[tuple[Any, ...]] = []
    for idx, article in enumerate(articles):
        h = article_hash("jpn", str(law_id), str(article["article_no"]), str(amended_at))
        article_did = f"{ACTOR_DID}:article:{h}"
        vertex_id = f"at://{article_did}/com.etzhayyim.apps.houbun.article/{h}"
        rows.append(
            (
                vertex_id,
                current[:10],
                article_did,
                h,
                statute_ref,
                article["article_no"],
                article.get("section"),
                article.get("title"),
                article.get("text"),
                "ja",
                article_did,
                h,
                amended_at,
                source_url,
                current,
                "sys.houbun",
            )
        )
        edges.append(
            (
                f"{statute_ref}::{vertex_id}",
                statute_ref,
                vertex_id,
                current[:10],
                article_did,
                article["article_no"],
                idx,
                current,
                "sys.houbun",
            )
        )
    return rows, edges


def generic_article_rows(
    *,
    jurisdiction: str,
    statute_id: str,
    statute_ref: str,
    articles: list[dict[str, Any]],
    language: str,
    source_url: str,
    amended_at: str | None,
) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    current = now_iso()
    rows: list[tuple[Any, ...]] = []
    edges: list[tuple[Any, ...]] = []
    for idx, article in enumerate(articles):
        h = article_hash(jurisdiction, statute_id, str(article["article_no"]), str(amended_at or ""))
        article_did = f"{ACTOR_DID}:article:{h}"
        vertex_id = f"at://{article_did}/com.etzhayyim.apps.houbun.article/{h}"
        rows.append(
            (
                vertex_id,
                current[:10],
                article_did,
                h,
                statute_ref,
                article["article_no"],
                article.get("section"),
                article.get("title"),
                article.get("text"),
                language,
                article_did,
                h,
                amended_at,
                source_url,
                current,
                "sys.houbun",
            )
        )
        edges.append(
            (
                f"{statute_ref}::{vertex_id}",
                statute_ref,
                vertex_id,
                current[:10],
                article_did,
                article["article_no"],
                idx,
                current,
                "sys.houbun",
            )
        )
    return rows, edges


def insert_statutes(conn: Any, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    rows = [r for r in rows if r[0] not in existing_ids(conn, "vertex_houbun_statute", [x[0] for x in rows])]
    if not rows:
        return
    execute_values(
        conn.cursor(),
        """
        INSERT INTO vertex_houbun_statute (
          vertex_id, created_date, owner_did, rkey, jurisdiction, statute_id,
          title, title_native, statute_type, enacted_date, effective_date,
          repealed_date, source, source_url, license, language, article_count,
          last_verified, created_at, actor_id
        ) VALUES %s
        """,
        rows,
        page_size=100,
    )


def insert_articles(conn: Any, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    rows = [r for r in rows if r[0] not in existing_ids(conn, "vertex_houbun_article", [x[0] for x in rows])]
    if not rows:
        return
    execute_values(
        conn.cursor(),
        """
        INSERT INTO vertex_houbun_article (
          vertex_id, created_date, owner_did, rkey, statute_ref, article_no,
          section, title, text, language, article_did, blake3_hash, amended_at,
          source_url, created_at, actor_id
        ) VALUES %s
        """,
        rows,
        page_size=50,
    )


def insert_edges(conn: Any, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    rows = [r for r in rows if r[0] not in existing_ids(conn, "edge_houbun_statute_article", [x[0] for x in rows], "edge_id")]
    if not rows:
        return
    execute_values(
        conn.cursor(),
        """
        INSERT INTO edge_houbun_statute_article (
          edge_id, src_vid, dst_vid, created_date, owner_did, article_no,
          order_key, created_at, actor_id
        ) VALUES %s
        """,
        rows,
        page_size=100,
    )


def social_rkey(source: str, source_record_id: str) -> str:
    raw = f"{source}-{source_record_id}".lower()
    return NON_ALNUM.sub("-", raw).strip("-")[:64] or "unknown"


def existing_ids(conn: Any, table: str, ids: list[str], column: str = "vertex_id") -> set[str]:
    if not ids:
        return set()
    placeholders = ",".join(["%s"] * len(ids))
    cur = conn.cursor()
    cur.execute(f"SELECT {column} FROM {table} WHERE {column} IN ({placeholders})", ids)
    return {str(row[0]) for row in cur.fetchall()}


def insert_social_contracts(conn: Any) -> int:
    base = REPO / "orgs/etzhayyim/com-etzhayyim-app-contracts/data/social-contracts"
    rows: list[tuple[Any, ...]] = []
    current = now_iso()
    for path in sorted(base.glob("*.jsonld")):
        doc = json.loads(path.read_text())
        source = str(doc.get("source") or urllib.parse.urlparse(str(doc.get("url") or "")).netloc or "local")
        source_record_id = Path(str(doc.get("@id") or path.stem)).name
        rkey = social_rkey(source, source_record_id)
        rows.append(
            (
                f"at://{CONTRACTS_DID}/com.etzhayyim.apps.contracts.socialContract/{rkey}",
                current[:10],
                CONTRACTS_DID,
                rkey,
                doc.get("name"),
                doc.get("constitutionalType"),
                doc.get("jurisdiction"),
                doc.get("adoptedDate"),
                doc.get("effectiveDate"),
                doc.get("scope"),
                doc.get("documentUrl") or doc.get("url"),
                None,
                source,
                source_record_id,
                float(doc.get("confidence") or 1.0),
                doc.get("lastVerified") or current,
                current,
                "sys.contracts",
            )
        )
    existing = existing_ids(conn, "vertex_contracts_social_contract", [r[0] for r in rows])
    rows = [r for r in rows if r[0] not in existing]
    if not rows:
        return 0
    execute_values(
        conn.cursor(),
        """
        INSERT INTO vertex_contracts_social_contract (
          vertex_id, created_date, owner_did, rkey, name, constitutional_type,
          jurisdiction, adopted_date, effective_date, scope, url, un_reg_no,
          source, source_record_id, confidence, last_verified, created_at, actor_id
        ) VALUES %s
        """,
        rows,
        page_size=100,
    )
    return len(rows)


def year_date(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if re.fullmatch(r"\d{4}", s):
        return f"{s}-01-01"
    return s


def insert_constitute_metadata(conn: Any, *, limit: int, include_historic: bool) -> dict[str, int]:
    historic = "true" if include_historic else "false"
    rows_raw = get_json(
        "https://www.constituteproject.org/service/constitutions",
        {"lang": "en", "historic": historic},
    )
    if not isinstance(rows_raw, list):
        raise RuntimeError("Constitute response was not a JSON array")

    current = now_iso()
    rows: list[tuple[Any, ...]] = []
    fetched = 0
    skipped = 0
    for doc in rows_raw:
        if not isinstance(doc, dict):
            continue
        fetched += 1
        if doc.get("country_id") == "Japan":
            skipped += 1
            continue
        if not doc.get("public"):
            skipped += 1
            continue
        if not include_historic and not doc.get("in_force"):
            skipped += 1
            continue
        source_record_id = str(doc.get("id") or "").strip()
        if not source_record_id:
            skipped += 1
            continue
        rkey = social_rkey("constitute", source_record_id)
        title = doc.get("title_long") or doc.get("title") or source_record_id
        adopted = year_date(doc.get("year_enacted"))
        effective = year_date(doc.get("year_reinstated") or doc.get("year_enacted"))
        rows.append(
            (
                f"at://{CONTRACTS_DID}/com.etzhayyim.apps.contracts.socialContract/{rkey}",
                current[:10],
                CONTRACTS_DID,
                rkey,
                title,
                "constitution",
                doc.get("country_id"),
                adopted,
                effective,
                f"national constitution; region={doc.get('region') or ''}; in_force={bool(doc.get('in_force'))}",
                f"https://www.constituteproject.org/service/html?cons_id={urllib.parse.quote(source_record_id)}&lang=en",
                None,
                "constitute-project",
                source_record_id,
                0.9,
                current,
                current,
                "sys.contracts",
            )
        )
        if limit > 0 and len(rows) >= limit:
            break

    existing = existing_ids(conn, "vertex_contracts_social_contract", [r[0] for r in rows])
    rows = [r for r in rows if r[0] not in existing]
    inserted = 0
    if rows:
        execute_values(
            conn.cursor(),
            """
            INSERT INTO vertex_contracts_social_contract (
              vertex_id, created_date, owner_did, rkey, name, constitutional_type,
              jurisdiction, adopted_date, effective_date, scope, url, un_reg_no,
              source, source_record_id, confidence, last_verified, created_at, actor_id
            ) VALUES %s
            """,
            rows,
            page_size=100,
        )
        inserted = len(rows)
    return {"fetched": fetched, "inserted": inserted, "skipped": skipped + len(existing)}


def wikidata_sparql(query: str) -> dict[str, Any]:
    return get_json(
        "https://query.wikidata.org/sparql",
        {"format": "json", "query": query},
    )


def insert_wikidata_untc_treaties(conn: Any, *, limit: int, offset: int) -> dict[str, int]:
    query = f"""
    SELECT ?item ?itemLabel ?untc WHERE {{
      ?item wdt:P9966 ?untc.
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    ORDER BY ?item
    LIMIT {max(1, min(limit, 1000))}
    OFFSET {max(0, offset)}
    """
    payload = wikidata_sparql(query)
    bindings = payload.get("results", {}).get("bindings", [])
    if not isinstance(bindings, list):
        raise RuntimeError("Wikidata SPARQL response missing bindings")

    current = now_iso()
    treaty_rows: list[tuple[Any, ...]] = []
    social_rows: list[tuple[Any, ...]] = []
    for b in bindings:
        if not isinstance(b, dict):
            continue
        objid = str(b.get("untc", {}).get("value") or "").strip()
        item_uri = str(b.get("item", {}).get("value") or "").strip()
        qid = item_uri.rsplit("/", 1)[-1] if item_uri else ""
        title = str(b.get("itemLabel", {}).get("value") or qid or objid).strip()
        if not objid or not title:
            continue
        rkey = NON_ALNUM.sub("-", objid.lower()).strip("-")[:64] or "unknown"
        source_url = f"https://treaties.un.org/Pages/showDetails.aspx?objid={urllib.parse.quote(objid)}"
        treaty_rows.append(
            (
                f"at://{ACTOR_DID}:int:un-treaty/com.etzhayyim.apps.houbun.treaty/{rkey}",
                current[:10],
                f"{ACTOR_DID}:int:un-treaty",
                rkey,
                title,
                title,
                None,
                None,
                None,
                None,
                None,
                "wikidata-p9966-untc",
                objid,
                source_url,
                "en",
                current,
                "sys.houbun",
            )
        )
        srkey = social_rkey("wikidata-p9966-untc", objid)
        social_rows.append(
            (
                f"at://{CONTRACTS_DID}/com.etzhayyim.apps.contracts.socialContract/{srkey}",
                current[:10],
                CONTRACTS_DID,
                srkey,
                title,
                "treaty",
                "international",
                None,
                None,
                f"international treaty; wikidata={qid}",
                source_url,
                None,
                "wikidata-p9966-untc",
                objid,
                0.8,
                current,
                current,
                "sys.contracts",
            )
        )

    existing_treaties = existing_ids(conn, "vertex_houbun_treaty", [r[0] for r in treaty_rows])
    treaty_rows = [r for r in treaty_rows if r[0] not in existing_treaties]
    if treaty_rows:
        execute_values(
            conn.cursor(),
            """
            INSERT INTO vertex_houbun_treaty (
              vertex_id, created_date, owner_did, rkey, title, title_native,
              parties_json, signed_date, entered_into_force_date, un_reg_no,
              depositary, source, source_record_id, source_url, language,
              created_at, actor_id
            ) VALUES %s
            """,
            treaty_rows,
            page_size=100,
        )

    existing_social = existing_ids(conn, "vertex_contracts_social_contract", [r[0] for r in social_rows])
    social_rows = [r for r in social_rows if r[0] not in existing_social]
    if social_rows:
        execute_values(
            conn.cursor(),
            """
            INSERT INTO vertex_contracts_social_contract (
              vertex_id, created_date, owner_did, rkey, name, constitutional_type,
              jurisdiction, adopted_date, effective_date, scope, url, un_reg_no,
              source, source_record_id, confidence, last_verified, created_at, actor_id
            ) VALUES %s
            """,
            social_rows,
            page_size=100,
        )

    return {
        "fetched": len(bindings),
        "houbunTreatiesInserted": len(treaty_rows),
        "socialContractsInserted": len(social_rows),
        "skipped": len(existing_treaties) + len(existing_social),
    }


def et_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return WS.sub(" ", " ".join(t.strip() for t in node.itertext() if t and t.strip())).strip()


def cfr_sections(xml_bytes: bytes) -> tuple[str, str, list[dict[str, Any]]]:
    root = ET.fromstring(xml_bytes)
    title_num = et_text(root.find(".//TITLEPG/TITLENUM"))
    subject = et_text(root.find(".//TITLEPG/SUBJECT"))
    sections: list[dict[str, Any]] = []
    for sec in root.findall(".//SECTION"):
        sect_no = et_text(sec.find("SECTNO"))
        subj = et_text(sec.find("SUBJECT"))
        parts: list[str] = []
        for child in list(sec):
            if child.tag in ("SECTNO", "SUBJECT"):
                continue
            text = et_text(child)
            if text:
                parts.append(text)
        body = WS.sub(" ", " ".join(parts)).strip()
        if sect_no and body:
            sections.append({"article_no": sect_no, "title": subj or None, "section": title_num, "text": body})
    return title_num, subject, sections


def insert_cfr_title(conn: Any, *, year: int, title: int, max_sections: int) -> dict[str, int]:
    listing = get_json(f"https://www.govinfo.gov/bulkdata/json/CFR/{year}/title-{title}")
    files = listing.get("files") or []
    xml_links = [
        f.get("link")
        for f in files
        if isinstance(f, dict) and f.get("fileExtension") == "xml" and isinstance(f.get("link"), str)
    ]
    fetched = 0
    statutes = 0
    articles = 0
    errors = 0
    for link in xml_links:
        try:
            xml_bytes = get_bytes(str(link))
            title_num, subject, sections = cfr_sections(xml_bytes)
            if max_sections > 0:
                sections = sections[:max_sections]
            package = Path(urllib.parse.urlparse(str(link)).path).stem
            current = now_iso()
            path_did = f"{ACTOR_DID}:usa:cfr"
            statute_ref = f"at://{path_did}/com.etzhayyim.apps.houbun.statute/{package}"
            srow = (
                statute_ref,
                current[:10],
                path_did,
                package,
                "usa",
                package,
                f"{title_num}: {subject}".strip(": "),
                f"{title_num}: {subject}".strip(": "),
                "regulation",
                None,
                f"{year}-01-01",
                None,
                "govinfo-cfr",
                str(link),
                "public-domain",
                "en",
                len(sections),
                current,
                current,
                "sys.houbun",
            )
            arows, erows = generic_article_rows(
                jurisdiction="usa",
                statute_id=package,
                statute_ref=statute_ref,
                articles=sections,
                language="en",
                source_url=str(link),
                amended_at=f"{year}-01-01",
            )
            insert_statutes(conn, [srow])
            insert_articles(conn, arows)
            insert_edges(conn, erows)
            conn.commit()
            fetched += 1
            statutes += 1
            articles += len(arows)
            print(f"ingested CFR {year} title-{title} {package}: sections={len(arows)}", flush=True)
        except Exception as exc:  # noqa: BLE001
            conn.rollback()
            errors += 1
            print(f"error CFR {year} title-{title} {link}: {exc}", file=sys.stderr, flush=True)
    return {"fetchedFiles": fetched, "statutes": statutes, "articles": articles, "errors": errors}


TAG_RE = re.compile(r"<[^>]+>")
ART_DIV_RE = re.compile(r'<div[^>]+class="[^"]*\beli-subdivision\b[^"]*"[^>]+id="(art_[^"]+)"[^>]*>', re.I)


def html_text(fragment: str) -> str:
    text = TAG_RE.sub(" ", fragment)
    return WS.sub(" ", html.unescape(text)).strip()


def eurlex_articles(page: str) -> list[dict[str, Any]]:
    matches = list(ART_DIV_RE.finditer(page))
    out: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(page)
        block = page[start:end]
        article_no_match = re.search(r'<p[^>]+class="[^"]*\boj-ti-art\b[^"]*"[^>]*>(.*?)</p>', block, re.I | re.S)
        title_match = re.search(r'<p[^>]+class="[^"]*\boj-sti-art\b[^"]*"[^>]*>(.*?)</p>', block, re.I | re.S)
        article_no = html_text(article_no_match.group(1)) if article_no_match else m.group(1).replace("_", " ")
        title = html_text(title_match.group(1)) if title_match else None
        text = html_text(block)
        if title:
            text = text.replace(title, "", 1).strip()
        if article_no:
            text = text.replace(article_no, "", 1).strip()
        if article_no and text:
            out.append({"article_no": article_no, "title": title, "section": None, "text": text})
    return out


def insert_eurlex_celex(conn: Any, *, celex: str, max_articles: int) -> dict[str, int]:
    url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:{urllib.parse.quote(celex)}"
    page = get_bytes(url).decode("utf-8", errors="replace")
    title_match = re.search(r"<title>(.*?)</title>", page, re.I | re.S)
    title = html_text(title_match.group(1)) if title_match else celex
    articles = eurlex_articles(page)
    if max_articles > 0:
        articles = articles[:max_articles]
    current = now_iso()
    path_did = f"{ACTOR_DID}:eu:eur-lex"
    statute_ref = f"at://{path_did}/com.etzhayyim.apps.houbun.statute/{celex}"
    srow = (
        statute_ref,
        current[:10],
        path_did,
        celex,
        "eu",
        celex,
        title,
        title,
        "regulation" if len(celex) >= 6 and celex[5] == "R" else "law",
        None,
        None,
        None,
        "eur-lex",
        url,
        "EUR-Lex reuse notice",
        "en",
        len(articles),
        current,
        current,
        "sys.houbun",
    )
    arows, erows = generic_article_rows(
        jurisdiction="eu",
        statute_id=celex,
        statute_ref=statute_ref,
        articles=articles,
        language="en",
        source_url=url,
        amended_at=None,
    )
    insert_statutes(conn, [srow])
    insert_articles(conn, arows)
    insert_edges(conn, erows)
    conn.commit()
    print(f"ingested EUR-Lex {celex}: articles={len(arows)}", flush=True)
    return {"statutes": 1, "articles": len(arows), "errors": 0}


def law_ids_from_egov(limit: int, offset: int) -> list[str]:
    ids: list[str] = []
    while len(ids) < limit:
        payload = get_json(f"{EGOV_BASE}/laws", {"limit": min(100, limit - len(ids)), "offset": offset})
        laws = payload.get("laws") or []
        if not laws:
            break
        for item in laws:
            info = item.get("law_info") or {}
            law_id = info.get("law_id")
            if law_id:
                ids.append(str(law_id))
        offset += len(laws)
        if not payload.get("next_offset"):
            break
    return ids


def ingest_egov(conn: Any, law_ids: list[str], sleep_sec: float, max_articles: int) -> dict[str, int]:
    stats = {"fetched": 0, "statutes": 0, "articles": 0, "edges": 0, "skippedLarge": 0, "errors": 0}
    for law_id in law_ids:
        try:
            law = get_json(f"{EGOV_BASE}/law_data/{law_id}")
            law_full = law.get("law_full_text") or {}
            body = first_child(law_full, "LawBody") or law_full
            articles = iter_articles(body)
            if max_articles > 0 and len(articles) > max_articles:
                stats["skippedLarge"] += 1
                print(f"skipped-large {law_id}: articles={len(articles)}", flush=True)
                continue
            srow = statute_row(law, articles)
            statute_ref = srow[0]
            arows, erows = article_rows(law, statute_ref, articles)
            insert_statutes(conn, [srow])
            insert_articles(conn, arows)
            insert_edges(conn, erows)
            conn.commit()
            stats["fetched"] += 1
            stats["statutes"] += 1
            stats["articles"] += len(arows)
            stats["edges"] += len(erows)
            print(f"ingested {law_id}: articles={len(arows)}", flush=True)
            if sleep_sec:
                time.sleep(sleep_sec)
        except Exception as exc:  # noqa: BLE001
            conn.rollback()
            stats["errors"] += 1
            print(f"error {law_id}: {exc}", file=sys.stderr, flush=True)
    return stats


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--database-url", default=DB_URL)
    p.add_argument("--egov-limit", type=int, default=25)
    p.add_argument("--egov-offset", type=int, default=0)
    p.add_argument("--law-id", action="append", default=[])
    p.add_argument("--include-constitution", action="store_true")
    p.add_argument("--sleep", type=float, default=0.15)
    p.add_argument("--max-articles", type=int, default=300)
    p.add_argument("--skip-social", action="store_true")
    p.add_argument("--constitute-limit", type=int, default=0)
    p.add_argument("--constitute-historic", action="store_true")
    p.add_argument("--wikidata-untc-limit", type=int, default=0)
    p.add_argument("--wikidata-untc-offset", type=int, default=0)
    p.add_argument("--cfr-year", type=int, default=0)
    p.add_argument("--cfr-title", type=int, action="append", default=[])
    p.add_argument("--cfr-max-sections", type=int, default=250)
    p.add_argument("--eurlex-celex", action="append", default=[])
    p.add_argument("--eurlex-max-articles", type=int, default=150)
    args = p.parse_args()

    seed_ids = ["321CONSTITUTION"] if args.include_constitution else []
    law_ids = list(dict.fromkeys([*seed_ids, *args.law_id, *law_ids_from_egov(args.egov_limit, args.egov_offset)]))
    print(json.dumps({"plannedLawIds": len(law_ids), "first": law_ids[:5]}, ensure_ascii=False), flush=True)

    conn = psycopg2.connect(args.database_url)
    try:
        social = 0 if args.skip_social else insert_social_contracts(conn)
        constitute = (
            insert_constitute_metadata(
                conn,
                limit=args.constitute_limit,
                include_historic=args.constitute_historic,
            )
            if args.constitute_limit != 0
            else {"fetched": 0, "inserted": 0, "skipped": 0}
        )
        wikidata_untc = (
            insert_wikidata_untc_treaties(
                conn,
                limit=args.wikidata_untc_limit,
                offset=args.wikidata_untc_offset,
            )
            if args.wikidata_untc_limit > 0
            else {"fetched": 0, "houbunTreatiesInserted": 0, "socialContractsInserted": 0, "skipped": 0}
        )
        conn.commit()
        cfr = {"fetchedFiles": 0, "statutes": 0, "articles": 0, "errors": 0}
        if args.cfr_year and args.cfr_title:
            for t in args.cfr_title:
                part = insert_cfr_title(
                    conn,
                    year=args.cfr_year,
                    title=t,
                    max_sections=args.cfr_max_sections,
                )
                for k, v in part.items():
                    cfr[k] = cfr.get(k, 0) + int(v)
        eurlex = {"statutes": 0, "articles": 0, "errors": 0}
        for celex in args.eurlex_celex:
            try:
                part = insert_eurlex_celex(
                    conn,
                    celex=str(celex),
                    max_articles=args.eurlex_max_articles,
                )
                for k, v in part.items():
                    eurlex[k] = eurlex.get(k, 0) + int(v)
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                eurlex["errors"] += 1
                print(f"error EUR-Lex {celex}: {exc}", file=sys.stderr, flush=True)
        stats = ingest_egov(conn, law_ids, args.sleep, args.max_articles)
    finally:
        conn.close()

    print(json.dumps({"ok": True, "socialContractsSeeded": social, "constitute": constitute, "wikidataUntc": wikidata_untc, "cfr": cfr, "eurlex": eurlex, "egov": stats}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
