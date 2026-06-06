"""Bunken bibliographic XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import decimal as _decimal
import json
import re
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any

from pymagatama import llm
from pymagatama.kotoba_datomic import get_kotoba_client
from datetime import datetime, timezone


APP_DID = "did:web:bunken.etzhayyim.com"
CDX_API = "https://index.commoncrawl.org/CC-MAIN-2026-12-index"

BIBLIOGRAPHIC_SOURCES: list[tuple[str, str, str]] = [
    ("ndlsearch.ndl.go.jp/books/*", "ndl:bib", "NDL Search 書誌"),
    ("dl.ndl.go.jp/pid/*", "ndl:pid", "NDL デジタルコレクション"),
    ("id.ndl.go.jp/bib/*", "ndl:bib", "NDL 永続的識別子"),
    ("ci.nii.ac.jp/ncid/*", "ncid", "CiNii NCID"),
    ("cir.nii.ac.jp/crid/*", "ncid", "CiNii Research CRID"),
    ("lccn.loc.gov/*", "lccn", "LOC LCCN"),
    ("www.loc.gov/item/*", "lccn", "LOC Item"),
    ("www.worldcat.org/oclc/*", "oclc", "WorldCat OCLC"),
    ("search.worldcat.org/title/*", "oclc", "WorldCat Title"),
    ("viaf.org/viaf/*", "viaf", "VIAF Authority"),
    ("doi.org/10.*", "doi", "DOI"),
    ("dx.doi.org/10.*", "doi", "DOI legacy"),
    ("n2t.net/ark:/*", "ark", "ARK"),
    ("gallica.bnf.fr/ark:/*", "ark", "Gallica BnF ARK"),
]


def _now() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _num(v: Any, fallback: float = 0.0) -> float:
    try:
        n = float(v)
        return n if n == n and n not in (float("inf"), float("-inf")) else fallback
    except (TypeError, ValueError):
        return fallback


def _str(v: Any) -> str:
    return v if isinstance(v, str) else ""


def _apply_aliases(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    aliases = {
        "vertex_id": "vertexId",
        "source_url": "sourceUrl",
        "source_domain": "sourceDomain",
        "crawl_id": "crawlId",
        "discovered_count": "discoveredCount",
        "registered_count": "registeredCount",
        "started_at": "startedAt",
        "completed_at": "completedAt",
        "external_id": "externalId",
        "material_type": "materialType",
        "digital_url": "digitalUrl",
        "did_registered": "didRegistered",
        "did_registered_at": "didRegisteredAt",
        "content_hash": "contentHash",
        "discovered_at": "discoveredAt",
        "enriched_at": "enrichedAt",
        "src_vid": "srcVid",
        "dst_vid": "dstVid",
        "src_did": "srcDid",
        "dst_did": "dstDid",
        "created_at": "createdAt",
    }
    for row in rows:
        aliased_row = {**row}  # Start with all snake_case keys
        for src, dst in aliases.items():
            if src in aliased_row and dst not in aliased_row:
                aliased_row[dst] = aliased_row[src]
        out.append(aliased_row)
    return out


def _djb2(text: str) -> str:
    h = 5381
    for ch in text:
        h = ((h << 5) + h + ord(ch)) & 0xFFFFFFFF
    return f"{h:08x}"


def _vid(label: str, key: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._:-]", "_", key)[:160] or uuid.uuid4().hex
    return f"at://{APP_DID}/com.etzhayyim.apps.bunken.{label}/{safe}"


def _build_did(scheme: str, external_id: str) -> str:
    if scheme == "doc":
        return f"{APP_DID}:doc:{_djb2(external_id)}"
    sanitized = re.sub(r"[^a-zA-Z0-9:._-]", "", external_id.replace("/", ":"))
    return f"{APP_DID}:{scheme}:{sanitized}"


def _classify_era(year: int | None) -> str:
    if year is None:
        return "unknown"
    if year < -3000:
        return "prehistoric"
    if year < 500:
        return "ancient"
    if year < 1760:
        return "medieval"
    if year < 1970:
        return "industrial"
    return "modern"


def _extract_id(url: str) -> tuple[str, str] | None:
    try:
        u = urllib.parse.urlparse(url)
    except Exception:
        return None
    host = u.hostname or ""
    path = u.path or ""
    if host == "id.ndl.go.jp" and path.startswith("/bib/"):
        return ("ndl:bib", path.replace("/bib/", "", 1))
    if host == "ndlsearch.ndl.go.jp" and path.startswith("/books/"):
        return ("ndl:bib", path.replace("/books/", "", 1).split("/")[0])
    if host == "dl.ndl.go.jp" and path.startswith("/pid/"):
        return ("ndl:pid", path.replace("/pid/", "", 1).split("/")[0])
    if host == "ci.nii.ac.jp" and path.startswith("/ncid/"):
        return ("ncid", path.replace("/ncid/", "", 1).rstrip("/"))
    if host == "cir.nii.ac.jp" and path.startswith("/crid/"):
        return ("ncid", path.replace("/crid/", "", 1).rstrip("/"))
    if host == "lccn.loc.gov":
        value = path.lstrip("/").rstrip("/")
        return ("lccn", value) if value else None
    if host == "www.loc.gov" and path.startswith("/item/"):
        return ("lccn", path.replace("/item/", "", 1).rstrip("/"))
    if host == "www.worldcat.org" and path.startswith("/oclc/"):
        return ("oclc", path.replace("/oclc/", "", 1).rstrip("/"))
    if host == "search.worldcat.org" and path.startswith("/title/"):
        return ("oclc", path.replace("/title/", "", 1).rstrip("/"))
    if host == "viaf.org" and path.startswith("/viaf/"):
        return ("viaf", re.sub(r"[/#].*$", "", path.replace("/viaf/", "", 1)))
    if host in ("doi.org", "dx.doi.org") and path.startswith("/10."):
        return ("doi", path.lstrip("/"))
    m = re.search(r"ark:/(\d+/\S+)", path)
    if m:
        return ("ark", m.group(1).rstrip("/"))
    return None


def _list_vertices(label: str) -> list[dict[str, Any]]:
    table = "vertex_bunken_collection_job" if label == "BunkenCollectionJob" else "vertex_bunken_bibliographic_item"
    order_col = "started_at" if label == "BunkenCollectionJob" else "discovered_at"
    # R0: Order by in-Python because select_where does not support ORDER BY.
    rows = get_kotoba_client().select_where(table, None, None, limit=2000)
    rows.sort(key=lambda x: x.get(order_col) or '', reverse=True)
    return _apply_aliases(rows)


def _list_edges(label: str) -> list[dict[str, Any]]:
    # R0: Order by in-Python because select_where does not support ORDER BY.
    rows = get_kotoba_client().select_where("edge_bunken_same_as", None, None, limit=2000)
    rows.sort(key=lambda x: x.get("created_at") or '', reverse=True)
    return _apply_aliases(rows)


def _find_vertex(label: str, pred: Any) -> dict[str, Any] | None:
    for row in _list_vertices(label):
        if pred(row):
            return row
    return None


def _insert_vertex(label: str, record: dict[str, Any]) -> dict[str, Any]:
    key = _str(record.get("id") or record.get("did") or record.get("externalId") or uuid.uuid4().hex)
    vertex_id = _vid(label, key)
    with sync_cursor() as cur:
        if label == "BunkenCollectionJob":
            job_row = {
                "vertex_id": vertex_id,
                "id": record.get("id"),
                "scheme": record.get("scheme"),
                "source_url": record.get("sourceUrl"),
                "source_domain": record.get("sourceDomain"),
                "crawl_id": record.get("crawlId"),
                "status": record.get("status", "pending"),
                "discovered_count": int(_num(record.get("discoveredCount"))),
                "registered_count": int(_num(record.get("registeredCount"))),
                "started_at": record.get("startedAt") or _now(),
                "completed_at": record.get("completedAt", ""),
                "error": record.get("error", ""),
                "org_id": "anon",
                "user_id": APP_DID,
                "actor_id": "bunken",
                "sensitivity_ord": 2,
                "owner_did": APP_DID,
            }
            get_kotoba_client().insert_row("vertex_bunken_collection_job", job_row)
        else:
            item_row = {
                "vertex_id": vertex_id,
                "scheme": record.get("scheme"),
                "external_id": record.get("externalId"),
                "did": record.get("did"),
                "source_url": record.get("sourceUrl"),
                "title": record.get("title", ""),
                "author": record.get("author", ""),
                "year": int(record["year"]) if record.get("year") is not None else None,
                "language": record.get("language", ""),
                "material_type": record.get("materialType", "unknown"),
                "era": record.get("era", "unknown"),
                "country": record.get("country", ""),
                "digital_url": record.get("digitalUrl"),
                "did_registered": bool(record.get("didRegistered", False)),
                "did_registered_at": record.get("didRegisteredAt", ""),
                "content_hash": record.get("contentHash", ""),
                "discovered_at": record.get("discoveredAt") or _now(),
                "enriched_at": record.get("enrichedAt", ""),
                "org_id": "anon",
                "user_id": APP_DID,
                "actor_id": "bunken",
                "sensitivity_ord": 2,
                "owner_did": APP_DID,
            }
            get_kotoba_client().insert_row("vertex_bunken_bibliographic_item", item_row)
    return {**record, "vertexId": vertex_id}


def _patch_vertex(row: dict[str, Any], patch: dict[str, Any]) -> None:
    vertex_id = _str(row.get("vertexId") or row.get("vertex_id"))
    if not vertex_id:
        return
    merged = {**row, **patch}
    _insert_vertex("BunkenCollectionJob" if "crawlId" in merged else "Bunken", merged)


def _insert_edge(src: dict[str, Any], dst: dict[str, Any], label: str, relation: str) -> None:
    src_vid = _str(src.get("vertexId"))
    dst_vid = _str(dst.get("vertexId"))
    if not src_vid or not dst_vid:
        return
    edge_id = f"{src_vid}:{relation}:{dst_vid}"
    edge_row = {
        "edge_id": edge_id,
        "src_vid": src_vid,
        "dst_vid": dst_vid,
        "src_did": src.get("did", ""),
        "dst_did": dst.get("did", ""),
        "relation": relation,
        "created_at": _now(),
        "owner_did": APP_DID,
        "sensitivity_ord": 2,
    }
    get_kotoba_client().insert_row("edge_bunken_same_as", edge_row)


def _fetch_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"user-agent": "bunken.etzhayyim.com/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def task_bunken_collect_from_cdx(crawlId: str = "CC-MAIN-2026-12", schemes: list | None = None, limit: Any = 1000, **_: Any) -> dict[str, Any]:
    wanted = set(schemes or ["ndl:bib", "ndl:pid", "ncid", "lccn", "oclc", "viaf"])
    lim = int(max(1, min(_num(limit, 1000), 10000)))
    jobs = []
    for pattern, scheme, _label in BIBLIOGRAPHIC_SOURCES:
        if scheme not in wanted:
            continue
        job_id = f"cj-{scheme.replace(':', '-')}-{int(time.time() * 1000)}"
        job = {
            "id": job_id,
            "scheme": scheme,
            "sourceUrl": f"{CDX_API}?url={urllib.parse.quote(pattern)}&output=json&limit={lim}",
            "sourceDomain": pattern.split("/")[0],
            "crawlId": crawlId,
            "status": "pending",
            "discoveredCount": 0,
            "registeredCount": 0,
            "startedAt": _now(),
        }
        _insert_vertex("BunkenCollectionJob", job)
        jobs.append(job)
    return {"jobs": len(jobs), "schemes": sorted(wanted), "crawlId": crawlId}


def task_bunken_fetch_cdx_batch(batchSize: Any = 200, **_: Any) -> dict[str, Any]:
    batch = int(max(1, min(_num(batchSize, 200), 1000)))
    jobs = [j for j in _list_vertices("BunkenCollectionJob") if j.get("status") == "pending"]
    jobs.sort(key=lambda r: _str(r.get("startedAt")))
    if not jobs:
        return {"status": "idle", "message": "No pending collection jobs"}
    job = jobs[0]
    try:
        _patch_vertex(job, {"status": "fetching"})
        cdx_url = f"{CDX_API}?url={urllib.parse.quote(_str(job.get('sourceDomain')) + '/*')}&output=json&limit={batch}&filter=statuscode:200"
        text = _fetch_text(cdx_url)
        discovered = registered = 0
        for line in [x for x in text.splitlines() if x.strip()]:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = _str(rec.get("url"))
            extracted = _extract_id(url)
            if not extracted:
                continue
            scheme, external_id = extracted
            did = _build_did(scheme, external_id)
            discovered += 1
            existing = _find_vertex("Bunken", lambda r, s=scheme, e=external_id: r.get("scheme") == s and r.get("externalId") == e)
            if existing:
                _patch_vertex(existing, {"sourceUrl": url})
            else:
                _insert_vertex("Bunken", {
                    "scheme": scheme, "externalId": external_id, "did": did, "sourceUrl": url,
                    "title": "", "author": "", "year": None, "language": "", "materialType": "unknown",
                    "era": "unknown", "country": "", "digitalUrl": None, "didRegistered": False,
                    "discoveredAt": _now(),
                })
            registered += 1
        _patch_vertex(job, {"status": "completed", "discoveredCount": discovered, "registeredCount": registered, "completedAt": _now()})
        return {"status": "completed", "scheme": job.get("scheme"), "discovered": discovered, "registered": registered}
    except Exception as e:  # noqa: BLE001
        _patch_vertex(job, {"status": "failed", "error": str(e)})
        return {"status": "failed", "scheme": job.get("scheme"), "error": str(e)}


def task_bunken_enrich_batch(batchSize: Any = 10, scheme: str = "", **_: Any) -> dict[str, Any]:
    batch = int(max(1, min(_num(batchSize, 10), 30)))
    records = [r for r in _list_vertices("Bunken") if not _str(r.get("title")) and _str(r.get("sourceUrl")) and (not scheme or r.get("scheme") == scheme)]
    records.sort(key=lambda r: _str(r.get("discoveredAt")))
    records = records[:batch]
    if not records:
        return {"status": "idle", "message": "No records to enrich"}
    enriched = 0
    for rec in records:
        try:
            text = _fetch_text(_str(rec.get("sourceUrl")))[:4000]
            content_hash = _djb2(text)
            if _str(rec.get("contentHash")) == content_hash:
                continue
            result = llm.call_tier_json(
                "fast",
                "Extract bibliographic metadata. Return JSON with title, author, year, language, materialType, country.",
                text,
                max_tokens=256,
                timeout_sec=30.0,
            )
            meta = result.get("data") if isinstance(result, dict) and isinstance(result.get("data"), dict) else {}
            year = int(meta["year"]) if str(meta.get("year") or "").lstrip("-").isdigit() else None
            _patch_vertex(rec, {
                "title": _str(meta.get("title")),
                "author": _str(meta.get("author")),
                "year": year,
                "language": _str(meta.get("language")),
                "materialType": _str(meta.get("materialType")) or "unknown",
                "country": _str(meta.get("country")),
                "era": _classify_era(year),
                "contentHash": content_hash,
                "enrichedAt": _now(),
            })
            enriched += 1
        except Exception:
            continue
    return {"status": "completed", "enriched": enriched, "total": len(records)}


def task_bunken_collect_from_ndl_api(keyword: str = "", era: str = "", batchSize: Any = 20, startRecord: Any = 1, **_: Any) -> dict[str, Any]:
    if not keyword:
        return {"error": "keyword required"}
    batch = int(max(1, min(_num(batchSize, 20), 100)))
    start = int(max(1, _num(startRecord, 1)))
    url = f"https://ndlsearch.ndl.go.jp/api/opensearch?cnt={batch}&idx={start}&title={urllib.parse.quote(keyword)}"
    try:
        xml = _fetch_text(url)
    except Exception as e:  # noqa: BLE001
        return {"error": f"NDL API fetch failed: {e}"}
    items = re.findall(r"<item>[\s\S]*?</item>", xml)
    discovered = 0
    for item in items:
        title = (re.search(r"<title>([^<]*)</title>", item) or [None, ""])[1].strip()
        link = (re.search(r"<link>([^<]*)</link>", item) or [None, ""])[1].strip()
        author_m = re.search(r"<author>([^<]*)</author>", item) or re.search(r"<dc:creator>([^<]*)</dc:creator>", item)
        date_m = re.search(r"<dc:date>([^<]*)</dc:date>", item) or re.search(r"<pubDate>([^<]*)</pubDate>", item)
        if not title or not link:
            continue
        extracted = _extract_id(link)
        if not extracted:
            continue
        scheme, external_id = extracted
        did = _build_did(scheme, external_id)
        author = author_m.group(1).strip() if author_m else ""
        year_s = date_m.group(1).strip() if date_m else ""
        year = int(year_s.split("-")[0]) if year_s.split("-")[0].isdigit() else None
        existing = _find_vertex("Bunken", lambda r, s=scheme, e=external_id: r.get("scheme") == s and r.get("externalId") == e)
        patch = {"title": title, "author": author, "year": year, "language": "jpn", "materialType": "printed", "era": era or _classify_era(year), "country": "jpn", "enrichedAt": _now()}
        if existing:
            _patch_vertex(existing, patch)
        else:
            _insert_vertex("Bunken", {"scheme": scheme, "externalId": external_id, "did": did, "sourceUrl": link, "digitalUrl": None, "didRegistered": False, "discoveredAt": _now(), **patch})
        discovered += 1
    return {"status": "completed", "keyword": keyword, "discovered": discovered, "totalItems": len(items), "nextStartRecord": start + batch}


def task_bunken_register_dids(batchSize: Any = 10, scheme: str = "", **_: Any) -> dict[str, Any]:
    batch = int(max(1, min(_num(batchSize, 10), 30)))
    records = [r for r in _list_vertices("Bunken") if not r.get("didRegistered") and _str(r.get("title")) and (not scheme or r.get("scheme") == scheme)]
    records.sort(key=lambda r: _str(r.get("enrichedAt")))
    registered = 0
    for rec in records[:batch]:
        _patch_vertex(rec, {"didRegistered": True, "didRegisteredAt": _now()})
        registered += 1
    return {"status": "completed" if registered else "idle", "registered": registered, "total": min(len(records), batch)}


def task_bunken_link_same_as(batchSize: Any = 20, **_: Any) -> dict[str, Any]:
    batch = int(max(1, min(_num(batchSize, 20), 100)))
    rows = _list_vertices("Bunken")
    edges = _list_edges("SAME_AS")
    linked = 0
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if linked >= batch:
                return {"status": "completed", "linked": linked}
            if not a.get("did") or not b.get("did") or str(a.get("scheme")) == str(b.get("scheme")):
                continue
            if not _str(a.get("title")) or a.get("title") != b.get("title") or _str(a.get("author")) != _str(b.get("author")):
                continue
            av, bv = _str(a.get("vertexId")), _str(b.get("vertexId"))
            if any(({_str(e.get("srcVid")), _str(e.get("dstVid"))} == {av, bv}) for e in edges):
                continue
            _insert_edge(a, b, "SAME_AS", "SAME_AS")
            linked += 1
    return {"status": "completed", "linked": linked}


def task_bunken_stats(**_: Any) -> dict[str, Any]:
    stats: dict[str, dict[str, Any]] = {}
    for row in _list_vertices("Bunken"):
        scheme = _str(row.get("scheme")) or "unknown"
        item = stats.setdefault(scheme, {"scheme": scheme, "total": 0, "registered": 0, "enriched": 0})
        item["total"] += 1
        if row.get("didRegistered"):
            item["registered"] += 1
        if _str(row.get("title")):
            item["enriched"] += 1
    jobs: dict[str, int] = {}
    for job in _list_vertices("BunkenCollectionJob"):
        status = _str(job.get("status")) or "unknown"
        jobs[status] = jobs.get(status, 0) + 1
    return {"schemes": sorted(stats.values(), key=lambda r: -int(r["total"])), "jobs": [{"status": k, "count": v} for k, v in jobs.items()]}


def task_bunken_search(title: str = "", author: str = "", scheme: str = "", era: str = "", country: str = "", limit: Any = 50, **_: Any) -> list[dict[str, Any]]:
    lim = int(max(1, min(_num(limit, 50), 200)))
    rows = [r for r in _list_vertices("Bunken") if _str(r.get("title"))]
    if title:
        rows = [r for r in rows if r.get("title") == title]
    if author:
        rows = [r for r in rows if r.get("author") == author]
    if scheme:
        rows = [r for r in rows if r.get("scheme") == scheme]
    if era:
        rows = [r for r in rows if r.get("era") == era]
    if country:
        rows = [r for r in rows if r.get("country") == country]
    rows.sort(key=lambda r: int(_num(r.get("year"), 0)))
    return [{k: r.get(k) for k in ("did", "scheme", "externalId", "title", "author", "year", "era", "country", "materialType", "didRegistered")} for r in rows[:lim]]


def task_bunken_get_record(did: str = "", scheme: str = "", externalId: str = "", **_: Any) -> dict[str, Any]:
    rows = _list_vertices("Bunken")
    if did:
        rec = next((r for r in rows if r.get("did") == did), None)
    elif scheme and externalId:
        rec = next((r for r in rows if r.get("scheme") == scheme and r.get("externalId") == externalId), None)
    else:
        return {"error": "Provide did or scheme+externalId"}
    if not rec:
        return {"error": "Not found"}
    same_as = [e for e in _list_edges("SAME_AS") if _str(e.get("srcVid")) == _str(rec.get("vertexId")) or _str(e.get("dstVid")) == _str(rec.get("vertexId"))]
    return {"b": rec, "alternateIds": [{"vertexId": _str(e.get("dstVid")) if _str(e.get("srcVid")) == _str(rec.get("vertexId")) else _str(e.get("srcVid"))} for e in same_as]}


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "xrpc.com.etzhayyim.apps.bunken.collectFromCdx": task_bunken_collect_from_cdx,
        "xrpc.com.etzhayyim.apps.bunken.fetchCdxBatch": task_bunken_fetch_cdx_batch,
        "xrpc.com.etzhayyim.apps.bunken.enrichBatch": task_bunken_enrich_batch,
        "xrpc.com.etzhayyim.apps.bunken.collectFromNdlApi": task_bunken_collect_from_ndl_api,
        "xrpc.com.etzhayyim.apps.bunken.registerDids": task_bunken_register_dids,
        "xrpc.com.etzhayyim.apps.bunken.linkSameAs": task_bunken_link_same_as,
        "xrpc.com.etzhayyim.apps.bunken.stats": task_bunken_stats,
        "xrpc.com.etzhayyim.apps.bunken.search": task_bunken_search,
        "xrpc.com.etzhayyim.apps.bunken.getRecord": task_bunken_get_record,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
