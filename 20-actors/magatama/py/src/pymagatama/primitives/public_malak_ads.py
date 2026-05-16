"""Public Malak ad-library ingest primitives for BPMN/LangServer.

Zeebe owns cadence and queue processing. This module owns the Python worker
side of public ad-library collection and writes the existing vertex_ads_* graph
tables so the public-malak appview can keep its current read path.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import html
import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor


LOG = logging.getLogger(__name__)
OWNER_DID = "did:web:public-malak.gftd.ai"
ACTOR_ID = "sys.langserver.public-malak.ads"
KNOWN_PLATFORMS = {
    "meta",
    "facebook",
    "instagram",
    "whatsapp",
    "google",
    "linkedin",
    "tiktok",
    "x",
    "line",
    "telegram",
}
PLATFORM_ALIASES = {
    "fb": "facebook",
    "facebook_ads": "facebook",
    "ig": "instagram",
    "instagram_ads": "instagram",
    "whatsup": "whatsapp",
    "wa": "whatsapp",
    "twitter": "x",
    "line_ads": "line",
    "telegram_ads": "telegram",
}
KNOWN_QUERY_KINDS = {"search", "advertiser", "page", "political"}
DEFAULT_SEEDS = [
    {"platform": "google", "queryKind": "search", "queryValue": "cybersecurity", "country": "US"},
    {"platform": "facebook", "queryKind": "search", "queryValue": "shopify", "country": "DE"},
    {"platform": "instagram", "queryKind": "search", "queryValue": "shopify", "country": "DE"},
    {"platform": "linkedin", "queryKind": "search", "queryValue": "cloud security", "country": "US"},
    {"platform": "line", "queryKind": "search", "queryValue": "security", "country": "JP"},
    {"platform": "telegram", "queryKind": "search", "queryValue": "security", "country": "US"},
]
ARTIFACT_BUCKET = os.environ.get("PUBLIC_MALAK_ARTIFACT_BUCKET", "").strip()
ARTIFACT_PREFIX = os.environ.get("PUBLIC_MALAK_ARTIFACT_PREFIX", "artifacts/public-malak").strip().strip("/")
ARTIFACT_S3_ENDPOINT = os.environ.get("PUBLIC_MALAK_ARTIFACT_S3_ENDPOINT", "").strip().rstrip("/")
ARTIFACT_S3_REGION = os.environ.get("PUBLIC_MALAK_ARTIFACT_S3_REGION", "auto").strip() or "auto"
ARTIFACT_S3_ACCESS_KEY_ID = os.environ.get("PUBLIC_MALAK_ARTIFACT_S3_ACCESS_KEY_ID", "").strip()
ARTIFACT_S3_SECRET_ACCESS_KEY = os.environ.get("PUBLIC_MALAK_ARTIFACT_S3_SECRET_ACCESS_KEY", "").strip()


def _utc_now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _today() -> _dt.date:
    return _dt.datetime.now(tz=_dt.UTC).date()


def _sha(prefix: str, *parts: Any) -> str:
    raw = "\x1f".join(str(p or "") for p in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _html_artifact_cid(text: str) -> str | None:
    return _sha("html", text[:4096]) if text else None


def _bytes_artifact_cid(kind: str, data: bytes) -> str | None:
    return f"{kind}-{hashlib.sha256(data).hexdigest()[:24]}" if data else None


def _artifact_key(kind: str, cid: str, ext: str) -> str:
    leaf = f"{cid}{ext}"
    return f"{ARTIFACT_PREFIX}/{kind}/{leaf}" if ARTIFACT_PREFIX else f"{kind}/{leaf}"


def _s3_put_artifact(key: str, data: bytes, content_type: str) -> str | None:
    if not (
        ARTIFACT_BUCKET
        and ARTIFACT_S3_ENDPOINT
        and ARTIFACT_S3_ACCESS_KEY_ID
        and ARTIFACT_S3_SECRET_ACCESS_KEY
    ):
        return None
    url = f"{ARTIFACT_S3_ENDPOINT}/{ARTIFACT_BUCKET}/{key}"
    now = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    date = now[:8]
    host = ARTIFACT_S3_ENDPOINT.replace("https://", "").replace("http://", "")
    payload_hash = hashlib.sha256(data).hexdigest()
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{now}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canonical_req = (
        f"PUT\n/{ARTIFACT_BUCKET}/{key}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )
    scope = f"{date}/{ARTIFACT_S3_REGION}/s3/aws4_request"
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n{now}\n{scope}\n"
        + hashlib.sha256(canonical_req.encode()).hexdigest()
    )

    def _sign(k: bytes, msg: str) -> bytes:
        return hmac.new(k, msg.encode(), hashlib.sha256).digest()

    signing_key = _sign(
        _sign(_sign(_sign(f"AWS4{ARTIFACT_S3_SECRET_ACCESS_KEY}".encode(), date), ARTIFACT_S3_REGION), "s3"),
        "aws4_request",
    )
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
    auth = (
        f"AWS4-HMAC-SHA256 Credential={ARTIFACT_S3_ACCESS_KEY_ID}/{scope},"
        f" SignedHeaders={signed_headers},"
        f" Signature={signature}"
    )
    req = urllib.request.Request(
        url,
        data=data,
        method="PUT",
        headers={
            "Content-Type": content_type,
            "x-amz-date": now,
            "x-amz-content-sha256": payload_hash,
            "Authorization": auth,
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        resp.read()
    return f"s3://{ARTIFACT_BUCKET}/{key}"


def _persist_html_artifact(cid: str | None, text: str) -> str | None:
    if not cid or not text:
        return None
    try:
        return _s3_put_artifact(
            _artifact_key("html", cid, ".html"),
            text.encode("utf-8", errors="replace"),
            "text/html; charset=utf-8",
        )
    except Exception:
        LOG.warning("public malak html artifact persist failed cid=%s", cid, exc_info=True)
        return None


def _persist_json_artifact(kind: str, cid: str | None, doc: dict[str, Any], ext: str) -> str | None:
    if not cid:
        return None
    try:
        data = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return _s3_put_artifact(
            _artifact_key(kind, cid, ext),
            data,
            "application/json; charset=utf-8",
        )
    except Exception:
        LOG.warning("public malak json artifact persist failed kind=%s cid=%s", kind, cid, exc_info=True)
        return None


def _header_pairs(headers: Any, limit: int = 80) -> list[dict[str, str]]:
    items = headers.items() if hasattr(headers, "items") else []
    pairs: list[dict[str, str]] = []
    for name, value in list(items)[:limit]:
        pairs.append({"name": str(name)[:160], "value": str(value)[:1000]})
    return pairs


def _har_lite_doc(
    *,
    source_url: str,
    fetch_result: dict[str, Any],
    html_cid: str | None,
    scraped_at: str,
) -> dict[str, Any]:
    text = str(fetch_result.get("text") or "")
    status = int(fetch_result.get("httpStatus") or 0)
    final_url = str(fetch_result.get("finalUrl") or source_url)
    headers = fetch_result.get("headers") if isinstance(fetch_result.get("headers"), dict) else {}
    content_type = str(headers.get("Content-Type") or headers.get("content-type") or "")
    return {
        "log": {
            "version": "1.2",
            "creator": {"name": "pymagatama-public-malak-ads", "version": "1"},
            "entries": [
                {
                    "startedDateTime": scraped_at,
                    "time": int(fetch_result.get("elapsedMs") or 0),
                    "request": {
                        "method": "GET",
                        "url": source_url,
                        "headers": [
                            {"name": "Accept", "value": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
                            {"name": "User-Agent", "value": "pymagatama-public-malak-ads/1 (+https://public-malak.gftd.ai)"},
                        ],
                    },
                    "response": {
                        "status": status,
                        "statusText": str(fetch_result.get("statusText") or ""),
                        "headers": _header_pairs(headers),
                        "redirectURL": "" if final_url == source_url else final_url,
                        "content": {
                            "size": len(text.encode("utf-8", errors="replace")),
                            "mimeType": content_type or "text/html",
                            "htmlCid": html_cid,
                        },
                    },
                    "error": str(fetch_result.get("error") or ""),
                }
            ],
        }
    }


def _har_artifact_cid(doc: dict[str, Any]) -> str | None:
    data = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _bytes_artifact_cid("har", data)


def _run_vid(run_id: str) -> str:
    return f"at://{OWNER_DID}/ai.gftd.apps.publicMalak.adScraperRun/{run_id}"


def _advertiser_vid(platform: str, advertiser_id: str) -> str:
    return f"at://{OWNER_DID}/ai.gftd.apps.publicMalak.adAdvertiser/{platform}-{advertiser_id}"


def _creative_vid(platform: str, ad_id: str) -> str:
    return f"at://{OWNER_DID}/ai.gftd.apps.publicMalak.adCreative/{platform}-{ad_id}"


def _snapshot_vid(platform: str, ad_id: str, run_id: str) -> str:
    return f"at://{OWNER_DID}/ai.gftd.apps.publicMalak.adSnapshot/{platform}-{ad_id}-{run_id}"


def _analysis_vid(creative_vertex_id: str, analysis_kind: str, model_id: str) -> str:
    return f"at://{OWNER_DID}/ai.gftd.apps.publicMalak.adAnalysis/{_sha('analysis', creative_vertex_id, analysis_kind, model_id)}"


def _campaign_vid(campaign_key: str) -> str:
    return f"at://{OWNER_DID}/ai.gftd.apps.publicMalak.adCampaignCluster/{campaign_key}"


def _campaign_edge_id(creative_vertex_id: str, campaign_vertex_id: str) -> str:
    return _sha("edge", creative_vertex_id, campaign_vertex_id)


def _normalize_platform(platform: str) -> str:
    raw = re.sub(r"[\s-]+", "_", str(platform or "").strip().lower())
    return PLATFORM_ALIASES.get(raw, raw)


def _clean_text(value: str, limit: int = 1000) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _extract_title(raw: str) -> str:
    match = re.search(r"<title[^>]*>([\s\S]*?)</title>", raw, flags=re.I)
    if match:
        return _clean_text(match.group(1), 240)
    h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", raw, flags=re.I)
    if h1:
        return _clean_text(h1.group(1), 240)
    return ""


def _decode_json_string(value: str) -> str:
    try:
        decoded = json.loads(f'"{value}"')
    except Exception:
        decoded = value
    return html.unescape(str(decoded))


def _extract_first_json_string(raw: str, keys: tuple[str, ...], limit: int = 500) -> str:
    for key in keys:
        match = re.search(rf'"{re.escape(key)}"\s*:\s*"((?:\\.|[^"\\])*)"', raw)
        if match:
            value = _clean_text(_decode_json_string(match.group(1)), limit)
            if value:
                return value
    return ""


def _extract_first_json_bool(raw: str, keys: tuple[str, ...]) -> bool | None:
    for key in keys:
        match = re.search(rf'"{re.escape(key)}"\s*:\s*(true|false)', raw, flags=re.I)
        if match:
            return match.group(1).lower() == "true"
    return None


def _extract_first_url(raw: str, keys: tuple[str, ...]) -> str:
    value = _extract_first_json_string(raw, keys, limit=1000)
    if value:
        return value
    match = re.search(r"https?://[^\s\"'<>\\]+", html.unescape(raw))
    return match.group(0).rstrip(".,)") if match else ""


def _extract_meta_property(raw: str, properties: tuple[str, ...], limit: int = 500) -> str:
    for prop in properties:
        patterns = (
            rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+name=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(prop)}["\']',
        )
        for pattern in patterns:
            match = re.search(pattern, raw, flags=re.I)
            if match:
                value = _clean_text(match.group(1), limit)
                if value:
                    return value
    return ""


def _parse_meta_ad_library(
    *,
    platform: str,
    query_value: str,
    country: str,
    source_url: str,
    text: str,
    http_status: int,
) -> dict[str, Any]:
    advertiser_name = _extract_first_json_string(
        text,
        ("pageName", "page_name", "advertiserName", "advertiser_name", "bylineName", "byline_name"),
        limit=240,
    )
    advertiser_id = _extract_first_json_string(
        text,
        ("pageID", "page_id", "pageId", "advertiserID", "advertiser_id", "advertiserId"),
        limit=120,
    )
    ad_id = _extract_first_json_string(
        text,
        ("adArchiveID", "ad_archive_id", "adArchiveId", "archiveID", "archive_id", "adID", "ad_id"),
        limit=120,
    )
    headline = _extract_first_json_string(
        text,
        ("title", "headline", "ad_creative_title", "linkTitle", "link_title"),
        limit=240,
    )
    body = _extract_first_json_string(
        text,
        ("bodyText", "body_text", "ad_creative_body", "body", "message", "text"),
        limit=1000,
    )
    cta = _extract_first_json_string(text, ("ctaText", "cta_text", "callToActionText", "call_to_action_text"), limit=120)
    landing_url = _extract_first_url(text, ("linkUrl", "link_url", "landingUrl", "landing_url", "url"))
    is_active = _extract_first_json_bool(text, ("isActive", "is_active", "active"))
    title = headline or _extract_title(text) or f"{platform} ad library: {query_value}"
    clean_body = body or _clean_text(text, 1000)
    parsed = bool(ad_id or advertiser_id or advertiser_name or body or headline)
    fallback_ad_id = _sha("ad", platform, source_url, title)
    return {
        "advertiserId": advertiser_id or _sha("adv", platform, query_value, country),
        "advertiserName": advertiser_name or query_value or title,
        "adId": ad_id or fallback_ad_id,
        "headline": title,
        "bodyText": clean_body,
        "ctaText": cta or None,
        "landingUrl": landing_url or source_url,
        "displayUrl": urllib.parse.urlparse(landing_url or source_url).netloc,
        "creativeType": "meta-library-ad" if parsed else "library-page",
        "isActive": is_active if is_active is not None else bool(text and http_status and http_status < 500),
        "parseOk": bool(text and http_status and http_status < 500),
        "parseError": None if parsed else "meta structured fields not found",
        "parserVersion": "meta-ad-library-v1" if parsed else "LangServer-fetch-v1",
    }


def _parse_public_ad_page(
    *,
    platform: str,
    query_value: str,
    country: str,
    source_url: str,
    text: str,
    http_status: int,
) -> dict[str, Any]:
    advertiser_name = _extract_first_json_string(
        text,
        ("advertiserName", "advertiser_name", "accountName", "account_name", "companyName", "company_name", "orgName", "org_name"),
        limit=240,
    )
    advertiser_id = _extract_first_json_string(
        text,
        ("advertiserId", "advertiser_id", "accountId", "account_id", "companyId", "company_id", "orgId", "org_id"),
        limit=120,
    )
    ad_id = _extract_first_json_string(
        text,
        ("adId", "ad_id", "creativeId", "creative_id", "campaignId", "campaign_id", "promotedTweetId", "promoted_tweet_id"),
        limit=120,
    )
    headline = (
        _extract_first_json_string(text, ("headline", "title", "name", "creativeTitle", "creative_title"), limit=240)
        or _extract_meta_property(text, ("og:title", "twitter:title"), limit=240)
        or _extract_title(text)
    )
    body = (
        _extract_first_json_string(text, ("bodyText", "body_text", "description", "text", "message", "copy"), limit=1000)
        or _extract_meta_property(text, ("og:description", "twitter:description", "description"), limit=1000)
        or _clean_text(text, 1000)
    )
    cta = _extract_first_json_string(text, ("ctaText", "cta_text", "callToAction", "call_to_action"), limit=120)
    landing_url = _extract_first_url(text, ("landingUrl", "landing_url", "destinationUrl", "destination_url", "url", "websiteUrl", "website_url"))
    is_active = _extract_first_json_bool(text, ("isActive", "is_active", "active", "serving"))
    title = headline or f"{platform} ad library: {query_value}"
    parsed = bool(ad_id or advertiser_id or advertiser_name or headline or landing_url)
    fallback_ad_id = _sha("ad", platform, source_url, title)
    parser_version = f"{platform}-ad-library-v1" if parsed else "LangServer-fetch-v1"
    return {
        "advertiserId": advertiser_id or _sha("adv", platform, query_value, country),
        "advertiserName": advertiser_name or query_value or title,
        "adId": ad_id or fallback_ad_id,
        "headline": title,
        "bodyText": body,
        "ctaText": cta or None,
        "landingUrl": landing_url or source_url,
        "displayUrl": urllib.parse.urlparse(landing_url or source_url).netloc,
        "creativeType": f"{platform}-library-ad" if parsed else "library-page",
        "isActive": is_active if is_active is not None else bool(text and http_status and http_status < 500),
        "parseOk": bool(text and http_status and http_status < 500),
        "parseError": None if parsed else f"{platform} structured fields not found",
        "parserVersion": parser_version,
    }


def _parse_observation_fields(
    *,
    platform: str,
    query_value: str,
    country: str,
    source_url: str,
    text: str,
    http_status: int,
) -> dict[str, Any]:
    if platform in {"meta", "facebook", "instagram", "whatsapp"}:
        return _parse_meta_ad_library(
            platform=platform,
            query_value=query_value,
            country=country,
            source_url=source_url,
            text=text,
            http_status=http_status,
        )
    if platform in {"x", "linkedin", "line", "telegram"}:
        return _parse_public_ad_page(
            platform=platform,
            query_value=query_value,
            country=country,
            source_url=source_url,
            text=text,
            http_status=http_status,
        )
    title = _extract_title(text) or f"{platform} ad library: {query_value}"
    return {
        "advertiserId": _sha("adv", platform, query_value, country),
        "advertiserName": query_value or title,
        "adId": _sha("ad", platform, source_url, title),
        "headline": title,
        "bodyText": _clean_text(text, 1000),
        "ctaText": None,
        "landingUrl": source_url,
        "displayUrl": urllib.parse.urlparse(source_url).netloc,
        "creativeType": "library-page",
        "isActive": bool(text and http_status and http_status < 500),
        "parseOk": bool(text and http_status and http_status < 500),
        "parseError": None if bool(text and http_status and http_status < 500) else "empty response",
        "parserVersion": "LangServer-fetch-v1",
    }


def _ads_library_url(platform: str, query_value: str, country: str) -> str:
    platform = _normalize_platform(platform)
    q = urllib.parse.quote(query_value or "")
    c = (country or "ALL").upper()
    if platform == "meta":
        return (
            "https://www.facebook.com/ads/library/"
            f"?active_status=all&ad_type=all&country={c}&q={q}"
        )
    if platform in {"facebook", "instagram", "whatsapp"}:
        return (
            "https://www.facebook.com/ads/library/"
            f"?active_status=all&ad_type=all&country={c}&q={q}"
            f"&publisher_platforms[0]={platform}"
        )
    if platform == "google":
        return f"https://adstransparency.google.com/?region={c}&q={q}"
    if platform == "linkedin":
        return f"https://www.linkedin.com/ad-library/search?keyword={q}&countries={c}"
    if platform == "tiktok":
        return f"https://library.tiktok.com/ads?region={c}&type=1&adv_name={q}"
    if platform == "x":
        return f"https://ads.x.com/transparency?country={c}&keyword={q}"
    if platform == "line":
        return f"https://www.lycbiz.com/jp/service/line-ads/search/?q={q}"
    if platform == "telegram":
        return f"https://ads.telegram.org/?q={q}"
    return ""


def _fetch(url: str, timeout_sec: float) -> dict[str, Any]:
    started = time.time()
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "pymagatama-public-malak-ads/1 (+https://public-malak.gftd.ai)",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read(1_000_000)
            text = body.decode("utf-8", errors="replace")
            return {
                "httpStatus": int(resp.status),
                "statusText": str(getattr(resp, "reason", "") or ""),
                "headers": dict(resp.headers.items()),
                "finalUrl": str(resp.geturl() or url),
                "elapsedMs": int((time.time() - started) * 1000),
                "text": text,
                "error": "",
            }
    except urllib.error.HTTPError as e:
        body = e.read(200_000)
        return {
            "httpStatus": int(e.code),
            "statusText": str(e.reason or ""),
            "headers": dict(e.headers.items()) if e.headers else {},
            "finalUrl": str(e.geturl() or url),
            "elapsedMs": int((time.time() - started) * 1000),
            "text": body.decode("utf-8", errors="replace"),
            "error": str(e.reason or e),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "httpStatus": 0,
            "statusText": "",
            "headers": {},
            "finalUrl": url,
            "elapsedMs": int((time.time() - started) * 1000),
            "text": "",
            "error": f"transport: {e}",
        }


def _insert_ignore(table: str, row: dict[str, Any]) -> int:
    # Drop None values to avoid psycopg3 type-inference failures on nullable
    # typed columns (BIGINT, DOUBLE PRECISION) when using extended protocol.
    # Omitted columns default to NULL in RisingWave.
    row = {k: v for k, v in row.items() if v is not None}
    cols = list(row.keys())
    placeholders = ", ".join([f"%({c})s" for c in cols])
    col_list = ", ".join(cols)
    sql_text = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    with sync_cursor() as cur:
        cur.execute(f"SELECT 1 FROM {table} WHERE vertex_id = %(vertex_id)s LIMIT 1", {"vertex_id": row["vertex_id"]})
        fetchone = getattr(cur, "fetchone", None)
        existing = fetchone() if callable(fetchone) else (cur.fetchall() or [])
        if existing:
            return 0
        cur.execute(sql_text, row)
        return int(cur.rowcount or 0)


def _insert_or_update_by_vertex(table: str, row: dict[str, Any], update_cols: list[str]) -> int:
    row = {k: v for k, v in row.items() if v is not None}
    cols = list(row.keys())
    placeholders = ", ".join([f"%({c})s" for c in cols])
    col_list = ", ".join(cols)
    sql_text = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    writable_cols = [c for c in update_cols if c in row and c != "vertex_id"]
    update_text = ", ".join([f"{c} = %({c})s" for c in writable_cols])
    with sync_cursor() as cur:
        cur.execute(f"SELECT 1 FROM {table} WHERE vertex_id = %(vertex_id)s LIMIT 1", {"vertex_id": row["vertex_id"]})
        fetchone = getattr(cur, "fetchone", None)
        existing = fetchone() if callable(fetchone) else (cur.fetchall() or [])
        if existing:
            if update_text:
                cur.execute(f"UPDATE {table} SET {update_text} WHERE vertex_id = %(vertex_id)s", row)
            return 0
        cur.execute(sql_text, row)
        return int(cur.rowcount or 0)


def _insert_edge_ignore(table: str, row: dict[str, Any]) -> int:
    row = {k: v for k, v in row.items() if v is not None}
    cols = list(row.keys())
    placeholders = ", ".join([f"%({c})s" for c in cols])
    col_list = ", ".join(cols)
    sql_text = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    with sync_cursor() as cur:
        cur.execute(f"SELECT 1 FROM {table} WHERE edge_id = %(edge_id)s LIMIT 1", {"edge_id": row["edge_id"]})
        fetchone = getattr(cur, "fetchone", None)
        existing = fetchone() if callable(fetchone) else (cur.fetchall() or [])
        if existing:
            return 0
        cur.execute(sql_text, row)
        return int(cur.rowcount or 0)


def _update_run(vertex_id: str, status: str, **fields: Any) -> None:
    assigns = ["status = %(status)s"]
    params = {"vertex_id": vertex_id, "status": status, **fields}
    for key in fields:
        assigns.append(f"{key} = %({key})s")
    with sync_cursor() as cur:
        cur.execute(
            f"UPDATE vertex_ads_scraper_run SET {', '.join(assigns)} WHERE vertex_id = %(vertex_id)s",
            params,
        )


def _claim_runs(max_runs: int, platform: str = "", reclaim_after_sec: int = 1800) -> list[dict[str, Any]]:
    platform = _normalize_platform(platform)
    cutoff = _dt.datetime.now(tz=_dt.UTC) - _dt.timedelta(seconds=max(60, int(reclaim_after_sec or 1800)))
    cutoff_s = cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    params: dict[str, Any] = {"cutoff": cutoff_s}
    filters = ["(status = 'queued' OR (status = 'running' AND started_at < %(cutoff)s))"]
    if platform:
        filters.append("platform = %(platform)s")
        params["platform"] = platform
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT vertex_id, platform, query_kind, query_value, country, started_at
            FROM vertex_ads_scraper_run
            WHERE {' AND '.join(filters)}
            ORDER BY started_at ASC
            LIMIT {int(max_runs)}
            """,
            params,
        )
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(zip(cols, row)) for row in (cur.fetchall() or [])]
    for row in rows:
        _update_run(str(row["vertex_id"]), "running", error_message="phase:claimed")
    return rows


def queue_seed_runs(seeds: Any = None, limit: int = 20) -> dict[str, Any]:
    raw_seeds = seeds if isinstance(seeds, list) and seeds else DEFAULT_SEEDS
    queued = 0
    skipped = 0
    rows: list[dict[str, Any]] = []
    now = _utc_now()
    for raw in raw_seeds[: max(1, min(int(limit or 20), 100))]:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        platform = _normalize_platform(str(raw.get("platform") or ""))
        query_kind = str(raw.get("queryKind") or raw.get("query_kind") or "search").lower()
        query_value = str(raw.get("queryValue") or raw.get("query_value") or "").strip()
        country = str(raw.get("country") or "").upper()
        if platform not in KNOWN_PLATFORMS or query_kind not in KNOWN_QUERY_KINDS or not query_value:
            skipped += 1
            continue
        run_id = _sha("run", platform, query_kind, query_value, country, now[:13])
        vertex_id = _run_vid(run_id)
        row = {
            "vertex_id": vertex_id,
            "_seq": int(time.time() * 1000),
            "created_date": _today(),
            "sensitivity_ord": 0,
            "owner_did": OWNER_DID,
            "platform": platform,
            "query_kind": query_kind,
            "query_value": query_value,
            "country": country or None,
            "started_at": now,
            "finished_at": None,
            "status": "queued",
            "ads_seen": 0,
            "ads_new": 0,
            "ads_updated": 0,
            "error_message": None,
            "user_agent": "pymagatama-public-malak-ads/1",
            "proxy_country": None,
            "playwright_trace_cid": None,
            "robots_txt_snapshot_cid": None,
            "rate_limit_sleep_ms": 0,
            "org_id": OWNER_DID,
            "user_id": OWNER_DID,
            "actor_id": ACTOR_ID,
        }
        inserted = _insert_ignore("vertex_ads_scraper_run", row)
        queued += inserted
        rows.append({"vertexId": vertex_id, "platform": platform, "queryValue": query_value, "created": bool(inserted)})
    return {"queued": queued, "skipped": skipped, "runs": rows}


def _write_observation(run: dict[str, Any], fetch_result: dict[str, Any]) -> dict[str, Any]:
    platform = _normalize_platform(str(run.get("platform") or ""))
    query_value = str(run.get("query_value") or "")
    country = str(run.get("country") or "")
    run_vertex_id = str(run.get("vertex_id") or "")
    run_id = run_vertex_id.rsplit("/", 1)[-1] or _sha("run", platform, query_value)
    source_url = _ads_library_url(platform, query_value, country)
    text = str(fetch_result.get("text") or "")
    http_status = int(fetch_result.get("httpStatus") or 0)
    parsed = _parse_observation_fields(
        platform=platform,
        query_value=query_value,
        country=country,
        source_url=source_url,
        text=text,
        http_status=http_status,
    )
    title = str(parsed["headline"])
    body = str(parsed["bodyText"])
    advertiser_id = str(parsed["advertiserId"])
    advertiser_name = str(parsed["advertiserName"])
    ad_id = str(parsed["adId"])
    now = _utc_now()
    advertiser_vertex_id = _advertiser_vid(platform, advertiser_id)
    creative_vertex_id = _creative_vid(platform, ad_id)
    html_cid = _html_artifact_cid(text)
    _persist_html_artifact(html_cid, text)
    har_doc = _har_lite_doc(
        source_url=source_url,
        fetch_result=fetch_result,
        html_cid=html_cid,
        scraped_at=now,
    )
    har_cid = _har_artifact_cid(har_doc)
    _persist_json_artifact("har", har_cid, har_doc, ".har")
    parse_ok = bool(parsed["parseOk"])
    advertiser_inserted = _insert_ignore("vertex_ads_advertiser", {
        "vertex_id": advertiser_vertex_id,
        "_seq": int(time.time() * 1000),
        "created_date": _today(),
        "sensitivity_ord": 0,
        "owner_did": OWNER_DID,
        "platform": platform,
        "platform_advertiser_id": advertiser_id,
        "name": advertiser_name,
        "verified_name": None,
        "legal_name": None,
        "page_url": source_url,
        "page_category": "public-ad-library",
        "country": country or None,
        "funding_entity": None,
        "is_political": str(run.get("query_kind") or "") == "political",
        "legal_entity_did": None,
        "first_seen_at": now,
        "last_seen_at": now,
        "org_id": OWNER_DID,
        "user_id": OWNER_DID,
        "actor_id": ACTOR_ID,
    })
    creative_inserted = _insert_ignore("vertex_ads_creative", {
        "vertex_id": creative_vertex_id,
        "_seq": int(time.time() * 1000),
        "created_date": _today(),
        "sensitivity_ord": 0,
        "owner_did": OWNER_DID,
        "platform": platform,
        "platform_ad_id": ad_id,
        "advertiser_vertex_id": advertiser_vertex_id,
        "advertiser_name": advertiser_name,
        "creative_type": parsed["creativeType"],
        "headline": title,
        "body_text": body,
        "cta_text": parsed["ctaText"],
        "landing_url": parsed["landingUrl"],
        "display_url": parsed["displayUrl"],
        "media_url": None,
        "media_cid": None,
        "thumbnail_cid": None,
        "languages": None,
        "currency": None,
        "impressions_min": None,
        "impressions_max": None,
        "spend_min": None,
        "spend_max": None,
        "reach_min": None,
        "reach_max": None,
        "is_political": str(run.get("query_kind") or "") == "political",
        "is_active": bool(parsed["isActive"]),
        "ad_delivery_start_date": None,
        "ad_delivery_stop_date": None,
        "first_seen_at": now,
        "last_seen_at": now,
        "source_url": source_url,
        "org_id": OWNER_DID,
        "user_id": OWNER_DID,
        "actor_id": ACTOR_ID,
    })
    _insert_or_update_by_vertex("vertex_ads_snapshot", {
        "vertex_id": _snapshot_vid(platform, ad_id, run_id),
        "_seq": int(time.time() * 1000),
        "created_date": _today(),
        "sensitivity_ord": 0,
        "owner_did": OWNER_DID,
        "creative_vertex_id": creative_vertex_id,
        "platform": platform,
        "platform_ad_id": ad_id,
        "scraper": "LangServer-fetch-scraper",
        "scraper_run_id": run_vertex_id,
        "scraped_at": now,
        "source_url": source_url,
        "http_status": http_status,
        "html_cid": html_cid,
        "screenshot_cid": None,
        "har_cid": har_cid,
        "observed_is_active": parse_ok,
        "observed_impressions_min": None,
        "observed_impressions_max": None,
        "observed_spend_min": None,
        "observed_spend_max": None,
        "parser_version": parsed["parserVersion"],
        "parse_ok": parse_ok,
        "parse_error": None if parse_ok else str(fetch_result.get("error") or parsed["parseError"] or "parse failed")[:500],
        "org_id": OWNER_DID,
        "user_id": OWNER_DID,
        "actor_id": ACTOR_ID,
    }, [
        "_seq",
        "scraped_at",
        "source_url",
        "http_status",
        "html_cid",
        "screenshot_cid",
        "har_cid",
        "observed_is_active",
        "observed_impressions_min",
        "observed_impressions_max",
        "observed_spend_min",
        "observed_spend_max",
        "parser_version",
        "parse_ok",
        "parse_error",
    ])
    return {
        "adsSeen": 1 if parse_ok else 0,
        "adsNew": int(bool(creative_inserted)),
        "adsUpdated": 0 if creative_inserted else 1,
        "advertisersNew": int(bool(advertiser_inserted)),
        "creativeVertexId": creative_vertex_id,
        "httpStatus": http_status,
        "parseOk": parse_ok,
        "parserVersion": parsed["parserVersion"],
    }


def process_queue(
    max_runs: int = 3,
    timeout_sec: float = 20.0,
    platform: str = "",
    reclaim_after_sec: int = 1800,
) -> dict[str, Any]:
    runs = _claim_runs(
        max(1, min(int(max_runs or 3), 10)),
        platform=platform,
        reclaim_after_sec=reclaim_after_sec,
    )
    results: list[dict[str, Any]] = []
    for run in runs:
        source_url = _ads_library_url(
            str(run.get("platform") or ""),
            str(run.get("query_value") or ""),
            str(run.get("country") or ""),
        )
        if not source_url:
            _update_run(str(run["vertex_id"]), "failed", finished_at=_utc_now(), error_message="unknown platform")
            results.append({"vertexId": run["vertex_id"], "status": "failed", "errorMessage": "unknown platform"})
            continue
        fetched = _fetch(source_url, timeout_sec)
        obs = _write_observation(run, fetched)
        ok = bool(obs["parseOk"])
        status = "completed" if ok else "failed"
        _update_run(
            str(run["vertex_id"]),
            status,
            finished_at=_utc_now(),
            ads_seen=int(obs["adsSeen"]),
            ads_new=int(obs["adsNew"]),
            ads_updated=int(obs["adsUpdated"]),
            error_message=None if ok else str(fetched.get("error") or "parse failed")[:500],
        )
        results.append({"vertexId": run["vertex_id"], "status": status, **obs})
    return {
        "processed": len(results),
        "completed": sum(1 for r in results if r.get("status") == "completed"),
        "failed": sum(1 for r in results if r.get("status") == "failed"),
        "platform": _normalize_platform(platform) or None,
        "runs": results,
    }


def queue_status(platform: str = "") -> dict[str, Any]:
    platform = _normalize_platform(platform)
    params: dict[str, Any] = {}
    where = ""
    if platform:
        where = "WHERE platform = %(platform)s"
        params["platform"] = platform
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT status, count(*)
            FROM vertex_ads_scraper_run
            {where}
            GROUP BY status
            """,
            params,
        )
        status_rows = cur.fetchall() or []
        cur.execute(
            f"""
            SELECT platform, count(*)
            FROM vertex_ads_scraper_run
            {where}
            GROUP BY platform
            ORDER BY count(*) DESC
            LIMIT 20
            """,
            params,
        )
        platform_rows = cur.fetchall() or []
    return {
        "platform": platform or None,
        "byStatus": {str(status or "unknown"): int(count or 0) for status, count in status_rows},
        "byPlatform": {str(row_platform or "unknown"): int(count or 0) for row_platform, count in platform_rows},
    }


def _fetch_creative(creative_vertex_id: str) -> dict[str, Any] | None:
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT vertex_id, platform, platform_ad_id, advertiser_vertex_id,
                   advertiser_name, creative_type, headline, body_text,
                   landing_url, display_url, impressions_min, impressions_max,
                   spend_min, spend_max, reach_min, reach_max, is_political,
                   is_active, source_url, last_seen_at
            FROM vertex_ads_creative
            WHERE vertex_id = %(creative_vertex_id)s
            LIMIT 1
            """,
            {"creative_vertex_id": creative_vertex_id},
        )
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall() or []
    if not rows:
        return None
    return dict(zip(cols, rows[0]))


def _risk_score(creative: dict[str, Any], analysis_kind: str) -> int:
    text = " ".join(str(creative.get(k) or "") for k in ("headline", "body_text", "landing_url")).lower()
    score = 120
    if creative.get("is_political"):
        score += 180
    if analysis_kind in {"adversarial", "targeting"}:
        score += 80
    for token, weight in {
        "urgent": 60,
        "guaranteed": 50,
        "free": 35,
        "limited": 35,
        "crypto": 120,
        "investment": 90,
        "password": 160,
        "verify": 90,
        "login": 80,
        "official": 40,
    }.items():
        if token in text:
            score += weight
    return max(0, min(score, 1000))


def analyze_creative(creative_vertex_id: str, analysis_kind: str = "competitive", model_id: str = "") -> dict[str, Any]:
    kind = analysis_kind if analysis_kind in {"competitive", "adversarial", "claim", "sentiment", "targeting"} else "competitive"
    model = model_id or "heuristic-public-malak-v1"
    creative = None
    for attempt in range(5):
        creative = _fetch_creative(creative_vertex_id)
        if creative or attempt == 4:
            break
        time.sleep(1.0)
    if not creative:
        return {"error": "CreativeNotFound", "creativeVertexId": creative_vertex_id, "analysisKind": kind, "status": "failed"}
    score = _risk_score(creative, kind)
    platform = str(creative.get("platform") or "")
    advertiser = str(creative.get("advertiser_name") or "unknown advertiser")
    headline = _clean_text(str(creative.get("headline") or ""), 180)
    summary = (
        f"{kind} analysis for {platform} creative by {advertiser}: "
        f"{headline or 'no headline'}; risk={score}/1000."
    )
    analysis_vertex_id = _analysis_vid(creative_vertex_id, kind, model)
    inserted = _insert_ignore("vertex_ads_analysis", {
        "vertex_id": analysis_vertex_id,
        "_seq": int(time.time() * 1000),
        "created_date": _today(),
        "sensitivity_ord": 0,
        "owner_did": OWNER_DID,
        "creative_vertex_id": creative_vertex_id,
        "platform": platform,
        "platform_ad_id": creative.get("platform_ad_id"),
        "analysis_kind": kind,
        "model_id": model,
        "status": "completed",
        "summary": summary,
        "risk_score_permille": score,
        "claim_json": None,
        "targeting_json": None,
        "signals_json": (
            "{"
            f"\"isPolitical\":{str(bool(creative.get('is_political'))).lower()},"
            f"\"isActive\":{str(bool(creative.get('is_active'))).lower()}"
            "}"
        ),
        "source_snapshot_id": None,
        "analyzed_at": _utc_now(),
        "org_id": OWNER_DID,
        "user_id": OWNER_DID,
        "actor_id": ACTOR_ID,
    })
    return {
        "analysisVertexId": analysis_vertex_id,
        "creativeVertexId": creative_vertex_id,
        "analysisKind": kind,
        "status": "completed",
        "summary": summary,
        "riskScorePermille": score,
        "created": bool(inserted),
    }


def _list_creatives_for_analysis(
    *,
    limit: int,
    platform: str = "",
    analysis_kind: str = "competitive",
    model_id: str = "",
) -> list[str]:
    platform = _normalize_platform(platform)
    model = model_id or "heuristic-public-malak-v1"
    params: dict[str, Any] = {"analysis_kind": analysis_kind, "model_id": model}
    filters = []
    if platform:
        filters.append("c.platform = %(platform)s")
        params["platform"] = platform
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT c.vertex_id
            FROM vertex_ads_creative c
            {where}
            AND NOT EXISTS (
              SELECT 1
              FROM vertex_ads_analysis a
              WHERE a.creative_vertex_id = c.vertex_id
                AND a.analysis_kind = %(analysis_kind)s
                AND a.model_id = %(model_id)s
            )
            ORDER BY c.last_seen_at DESC
            LIMIT {int(limit)}
            """ if where else
            f"""
            SELECT c.vertex_id
            FROM vertex_ads_creative c
            WHERE NOT EXISTS (
              SELECT 1
              FROM vertex_ads_analysis a
              WHERE a.creative_vertex_id = c.vertex_id
                AND a.analysis_kind = %(analysis_kind)s
                AND a.model_id = %(model_id)s
            )
            ORDER BY c.last_seen_at DESC
            LIMIT {int(limit)}
            """,
            params,
        )
        rows = cur.fetchall() or []
    return [str(row[0]) for row in rows]


def analyze_recent(
    *,
    limit: int = 10,
    platform: str = "",
    analysis_kind: str = "competitive",
    model_id: str = "",
) -> dict[str, Any]:
    kind = analysis_kind if analysis_kind in {"competitive", "adversarial", "claim", "sentiment", "targeting"} else "competitive"
    max_items = max(1, min(int(limit or 10), 100))
    creative_ids: list[str] = []
    for attempt in range(5):
        creative_ids = _list_creatives_for_analysis(
            limit=max_items,
            platform=platform,
            analysis_kind=kind,
            model_id=model_id,
        )
        if creative_ids or attempt == 4:
            break
        time.sleep(1.0)
    results = [
        analyze_creative(creative_id, analysis_kind=kind, model_id=model_id)
        for creative_id in creative_ids
    ]
    return {
        "analyzed": sum(1 for result in results if result.get("status") == "completed"),
        "failed": sum(1 for result in results if result.get("status") == "failed"),
        "analysisKind": kind,
        "platform": _normalize_platform(platform) or None,
        "results": results,
    }


_CLAIM_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it",
    "of", "on", "or", "our", "the", "this", "to", "with", "you", "your", "now", "new",
    "more", "learn", "shop", "official", "ad", "ads", "campaign",
}


def _landing_domain(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url or "").strip())
    host = parsed.netloc or parsed.path.split("/", 1)[0]
    host = host.lower().split("@")[-1].split(":", 1)[0].strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host[:240]


def _claim_token(headline: str, body_text: str) -> str:
    text = f"{headline or ''} {body_text or ''}".lower()
    tokens = [
        token
        for token in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", text)
        if token not in _CLAIM_STOPWORDS
    ]
    if not tokens:
        return _sha("claim", text)[:32]
    token = "-".join(tokens[:8])
    return token[:96]


def _campaign_key(creative: dict[str, Any], platform_scope: str = "platform") -> str:
    scope = "cross_platform" if platform_scope == "cross_platform" else "platform"
    platform_part = "*" if scope == "cross_platform" else _normalize_platform(str(creative.get("platform") or ""))
    advertiser = str(creative.get("advertiser_vertex_id") or creative.get("advertiser_name") or "").lower()
    domain = _landing_domain(str(creative.get("landing_url") or creative.get("display_url") or ""))
    claim = _claim_token(str(creative.get("headline") or ""), str(creative.get("body_text") or ""))
    return _sha("campaign", scope, platform_part, advertiser, domain, claim)


def _list_creatives_for_clustering(*, limit: int, platform: str = "", platform_scope: str = "platform") -> list[str]:
    platform = _normalize_platform(platform)
    params: dict[str, Any] = {}
    filters = []
    if platform:
        filters.append("c.platform = %(platform)s")
        params["platform"] = platform
    where = ("WHERE " + " AND ".join(filters) + " AND") if filters else "WHERE"
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT c.vertex_id
            FROM vertex_ads_creative c
            {where} NOT EXISTS (
              SELECT 1
              FROM edge_ads_creative_in_campaign e
              WHERE e.src_vid = c.vertex_id
            )
            ORDER BY c.last_seen_at DESC
            LIMIT {int(limit)}
            """,
            params,
        )
        rows = cur.fetchall() or []
    return [str(row[0]) for row in rows]


def _campaign_counts(campaign_vertex_id: str) -> tuple[int, int]:
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT count(*), count(DISTINCT platform)
            FROM edge_ads_creative_in_campaign
            WHERE dst_vid = %(campaign_vertex_id)s
            """,
            {"campaign_vertex_id": campaign_vertex_id},
        )
        rows = cur.fetchall() or []
    if not rows:
        return 0, 0
    return int(rows[0][0] or 0), int(rows[0][1] or 0)


def _update_campaign_cluster_stats(campaign_vertex_id: str, last_seen_at: str) -> None:
    creative_count, platform_count = _campaign_counts(campaign_vertex_id)
    with sync_cursor() as cur:
        cur.execute(
            """
            UPDATE vertex_ads_campaign_cluster
            SET creative_count = %(creative_count)s,
                platform_count = %(platform_count)s,
                last_seen_at = %(last_seen_at)s
            WHERE vertex_id = %(campaign_vertex_id)s
            """,
            {
                "campaign_vertex_id": campaign_vertex_id,
                "creative_count": creative_count,
                "platform_count": platform_count,
                "last_seen_at": last_seen_at,
            },
        )


def cluster_recent(*, limit: int = 25, platform: str = "", platform_scope: str = "platform") -> dict[str, Any]:
    scope = "cross_platform" if platform_scope == "cross_platform" else "platform"
    max_items = max(1, min(int(limit or 25), 200))
    creative_ids: list[str] = []
    for attempt in range(5):
        creative_ids = _list_creatives_for_clustering(limit=max_items, platform=platform, platform_scope=scope)
        if creative_ids or attempt == 4:
            break
        time.sleep(1.0)

    results: list[dict[str, Any]] = []
    for creative_id in creative_ids:
        creative = _fetch_creative(creative_id)
        if not creative:
            results.append({"creativeVertexId": creative_id, "status": "failed", "error": "CreativeNotFound"})
            continue
        now = _utc_now()
        key = _campaign_key(creative, scope)
        campaign_vertex_id = _campaign_vid(key)
        domain = _landing_domain(str(creative.get("landing_url") or creative.get("display_url") or ""))
        claim = _claim_token(str(creative.get("headline") or ""), str(creative.get("body_text") or ""))
        risk = _risk_score(creative, "competitive")
        summary = (
            f"{scope} campaign cluster for {creative.get('advertiser_name') or 'unknown advertiser'} "
            f"on {domain or 'unknown domain'}: {str(creative.get('headline') or 'no headline')[:160]}"
        )
        campaign_inserted = _insert_ignore("vertex_ads_campaign_cluster", {
            "vertex_id": campaign_vertex_id,
            "_seq": int(time.time() * 1000),
            "created_date": _today(),
            "sensitivity_ord": 0,
            "owner_did": OWNER_DID,
            "campaign_key": key,
            "platform_scope": scope,
            "advertiser_vertex_id": creative.get("advertiser_vertex_id"),
            "advertiser_name": creative.get("advertiser_name"),
            "landing_domain": domain or None,
            "claim_token": claim,
            "sample_headline": creative.get("headline"),
            "sample_body_text": creative.get("body_text"),
            "creative_count": 0,
            "platform_count": 0,
            "first_seen_at": creative.get("last_seen_at") or now,
            "last_seen_at": creative.get("last_seen_at") or now,
            "risk_score_permille": risk,
            "summary": summary,
            "org_id": OWNER_DID,
            "user_id": OWNER_DID,
            "actor_id": ACTOR_ID,
        })
        edge_inserted = _insert_edge_ignore("edge_ads_creative_in_campaign", {
            "edge_id": _campaign_edge_id(creative_id, campaign_vertex_id),
            "src_vid": creative_id,
            "dst_vid": campaign_vertex_id,
            "_seq": int(time.time() * 1000),
            "created_date": _today(),
            "sensitivity_ord": 0,
            "owner_did": OWNER_DID,
            "platform": creative.get("platform"),
            "platform_ad_id": creative.get("platform_ad_id"),
            "match_basis": "advertiser_domain_claim",
            "created_at": now,
        })
        _update_campaign_cluster_stats(campaign_vertex_id, str(creative.get("last_seen_at") or now))
        results.append({
            "creativeVertexId": creative_id,
            "campaignVertexId": campaign_vertex_id,
            "campaignKey": key,
            "status": "completed",
            "campaignCreated": bool(campaign_inserted),
            "edgeCreated": bool(edge_inserted),
        })
    return {
        "clustered": sum(1 for result in results if result.get("status") == "completed"),
        "failed": sum(1 for result in results if result.get("status") == "failed"),
        "platform": _normalize_platform(platform) or None,
        "platformScope": scope,
        "results": results,
    }


async def task_queue_seed_runs(**kwargs: Any) -> dict[str, Any]:
    return queue_seed_runs(seeds=kwargs.get("seeds"), limit=int(kwargs.get("limit") or 20))


async def task_process_queue(**kwargs: Any) -> dict[str, Any]:
    return process_queue(
        max_runs=int(kwargs.get("maxRuns") or kwargs.get("max") or 3),
        timeout_sec=float(kwargs.get("timeoutSec") or 20.0),
        platform=str(kwargs.get("platform") or ""),
        reclaim_after_sec=int(kwargs.get("reclaimAfterSec") or kwargs.get("reclaim_after_sec") or 1800),
    )


async def task_analyze_creative(**kwargs: Any) -> dict[str, Any]:
    return analyze_creative(
        creative_vertex_id=str(kwargs.get("creativeVertexId") or kwargs.get("creative_vertex_id") or ""),
        analysis_kind=str(kwargs.get("analysisKind") or kwargs.get("analysis_kind") or "competitive"),
        model_id=str(kwargs.get("modelId") or kwargs.get("model_id") or ""),
    )


async def task_analyze_recent(**kwargs: Any) -> dict[str, Any]:
    return analyze_recent(
        limit=int(kwargs.get("limit") or kwargs.get("max") or 10),
        platform=str(kwargs.get("platform") or ""),
        analysis_kind=str(kwargs.get("analysisKind") or kwargs.get("analysis_kind") or "competitive"),
        model_id=str(kwargs.get("modelId") or kwargs.get("model_id") or ""),
    )


async def task_cluster_recent(**kwargs: Any) -> dict[str, Any]:
    return cluster_recent(
        limit=int(kwargs.get("limit") or kwargs.get("max") or 25),
        platform=str(kwargs.get("platform") or ""),
        platform_scope=str(kwargs.get("platformScope") or kwargs.get("platform_scope") or "platform"),
    )


def register(worker: Any, *, timeout_ms: int) -> None:
    worker.task(
        task_type="publicMalak.ads.queueSeedRuns",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_queue_seed_runs)
    worker.task(
        task_type="publicMalak.ads.processQueue",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_process_queue)
    worker.task(
        task_type="publicMalak.ads.analyzeCreative",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_analyze_creative)
    worker.task(
        task_type="publicMalak.ads.analyzeRecent",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_analyze_recent)
    worker.task(
        task_type="publicMalak.ads.clusterRecent",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_cluster_recent)
