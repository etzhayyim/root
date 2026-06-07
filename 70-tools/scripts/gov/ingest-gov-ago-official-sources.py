#!/usr/bin/env python3
"""Directly archive Angola official government source pages into RW/B2.

This is a fallback for the state Worker retirement gate when site.etzhayyim.com is
temporarily unavailable. It writes the same four graph surfaces the verifier
expects: vertex_page, vertex_wet_chunk, vertex_wat, and vertex_screenshot.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import time
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import boto3
import psycopg2 # kotoba-datomic-projection: historical offline script


OWNER_DID = "did:web:ago-state.etzhayyim.com"
BUCKET = os.environ.get("etzhayyim_B2_BUCKET", "etzhayyim-nats")
ENDPOINT = os.environ.get("etzhayyim_B2_ENDPOINT", "https://s3.us-west-004.backblazeb2.com")
PREFIX = "official-sources/ago/governo"

SOURCES = [
    {
        "rkey": "ago-ministro-8c8c8b4d31-11400000",
        "slug": "ago-ministro",
        "url": "https://governo.gov.ao/ministro",
    },
    {
        "rkey": "ago-governador-e495bf67e7-11400000",
        "slug": "ago-governador",
        "url": "https://governo.gov.ao/governador",
    },
    {
        "rkey": "ago-provincias-36779ddfea-11400000",
        "slug": "ago-provincias",
        "url": "https://governo.gov.ao/angola/provincias",
    },
]


def keychain(service: str, account: str) -> str:
    return subprocess.check_output(
        ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
        text=True,
    ).strip()


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today() -> str:
    return dt.datetime.now(dt.UTC).date().isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_html(url: str, out_path: Path) -> bytes:
    result = subprocess.run(
        [
            "curl",
            "-sSL",
            "--connect-timeout",
            "20",
            "--max-time",
            "180",
            "-A",
            "etzhayyim-gov-ago-official-source-archiver/0.1",
            "-o",
            str(out_path),
            url,
        ],
        capture_output=True,
        text=True,
        timeout=220,
    )
    if result.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"fetch failed for {url}: {result.stderr[:200]}")
    return out_path.read_bytes()


def chrome_bin() -> str:
    for candidate in (
        os.environ.get("CHROME_BIN", ""),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome Dev",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    raise RuntimeError("Chrome/Chromium binary not found; set CHROME_BIN")


def render_screenshot(url: str, out_path: Path) -> tuple[int, int]:
    result = subprocess.run(
        [
            chrome_bin(),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--window-size=1440,3600",
            f"--screenshot={out_path}",
            "--virtual-time-budget=8000",
            url,
        ],
        capture_output=True,
        text=True,
        timeout=100,
    )
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"screenshot failed for {url}: {result.stderr[:200]}")
    return image_size(out_path)


def image_size(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        return 0, 0
    width = 0
    height = 0
    for line in result.stdout.splitlines():
        if "pixelWidth:" in line:
            width = int(line.rsplit(":", 1)[1].strip())
        if "pixelHeight:" in line:
            height = int(line.rsplit(":", 1)[1].strip())
    return width, height


def strip_text(raw_html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\\1>", " ", raw_html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def page_title(raw_html: str) -> str:
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw_html)
    if not match:
        return "Portal Oficial do Governo de Angola"
    return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()[:1024]


def outlinks(raw_html: str) -> list[str]:
    links = []
    for match in re.finditer(r"""(?is)<a\s+[^>]*href=["']([^"']+)["']""", raw_html):
        href = html.unescape(match.group(1)).strip()
        if href.startswith("http"):
            links.append(href)
    deduped = []
    for link in links:
        if link not in deduped:
            deduped.append(link)
    return deduped


def upload(client: Any, key: str, path: Path, content_type: str) -> dict[str, Any]:
    data = path.read_bytes()
    client.put_object(Bucket=BUCKET, Key=key, Body=data, ContentType=content_type)
    return {"key": key, "bytes": len(data), "sha256": sha256_bytes(data)}


def vertex_id(collection: str, rkey: str) -> str:
    return f"at://{OWNER_DID}/{collection}/{rkey}"


def upsert_rows(conn: Any, source: dict[str, str], assets: dict[str, Any]) -> None:
    rkey = source["rkey"]
    url = source["url"]
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    crawled_at = now_iso()
    created_date = today()
    raw_html = assets["html_text"]
    markdown = strip_text(raw_html)
    links = outlinks(raw_html)
    title = page_title(raw_html)
    content_hash = sha256_bytes(assets["html_bytes"])

    page_id = vertex_id("com.etzhayyim.apps.site.page", rkey)
    wet_id = vertex_id("com.etzhayyim.apps.site.wetChunk", rkey)
    wat_id = vertex_id("com.etzhayyim.apps.site.wat", rkey)
    screenshot_id = vertex_id("com.etzhayyim.apps.site.screenshot", rkey)

    props = json.dumps(
        {
            "countryCode": "AGO",
            "officialPublisher": "Angolan Government",
            "evidence": {
                "page": {"rkey": rkey, "vertexId": page_id, "b2Blob": assets["html"]["key"]},
                "wet": {"pageRkey": rkey, "vertexId": wet_id},
                "wat": {"rkey": rkey, "vertexId": wat_id},
                "screenshot": {
                    "rkey": rkey,
                    "vertexId": screenshot_id,
                    "b2Blob": assets["screenshot"]["key"],
                    "format": "png",
                    "fileSize": assets["screenshot"]["bytes"],
                },
            },
        },
        separators=(",", ":"),
        ensure_ascii=False,
    )

    with conn.cursor() as cur:
        cur.execute("DELETE FROM vertex_page WHERE vertex_id = %s", (page_id,))
        cur.execute(
            """
            INSERT INTO vertex_page (
              vertex_id, created_date, sensitivity_ord, owner_did, rkey, url,
              domain, title, description, language, content_type, status_code,
              outlink_count, crawl, content_hash, version, crawled_at
            )
            VALUES (%s,%s,1,%s,%s,%s,%s,%s,%s,'pt','text/html','200',%s,%s,%s,1,%s)
            """,
            (
                page_id,
                created_date,
                OWNER_DID,
                rkey,
                url,
                domain,
                title,
                markdown[:4096],
                len(links),
                "gov-ago-official-source-direct",
                content_hash,
                crawled_at,
            ),
        )

        cur.execute("DELETE FROM vertex_wet_chunk WHERE vertex_id = %s", (wet_id,))
        cur.execute(
            """
            INSERT INTO vertex_wet_chunk (
              vertex_id, created_date, sensitivity_ord, owner_did, page_rkey,
              url, domain, chunk_index, total_chunks, markdown, content_hash,
              language, title, section, token_count, crawled_at
            )
            VALUES (%s,%s,1,%s,%s,%s,%s,0,1,%s,%s,'pt',%s,'official-source',%s,%s)
            """,
            (
                wet_id,
                created_date,
                OWNER_DID,
                rkey,
                url,
                domain,
                markdown[:120000],
                content_hash,
                title,
                len(markdown.split()),
                crawled_at,
            ),
        )

        cur.execute("DELETE FROM vertex_wat WHERE vertex_id = %s", (wat_id,))
        cur.execute(
            """
            INSERT INTO vertex_wat (
              vertex_id, created_date, sensitivity_ord, owner_did, rkey, url,
              domain, headers, outlinks, og_title, og_description, language,
              content_type, status_code
            )
            VALUES (%s,%s,1,%s,%s,%s,%s,%s,%s,%s,%s,'pt','text/html','200')
            """,
            (
                wat_id,
                created_date,
                OWNER_DID,
                rkey,
                url,
                domain,
                json.dumps({"content-type": "text/html"}, separators=(",", ":")),
                json.dumps(links[:500], separators=(",", ":"), ensure_ascii=False),
                title,
                markdown[:4096],
            ),
        )

        cur.execute("DELETE FROM vertex_screenshot WHERE vertex_id = %s", (screenshot_id,))
        cur.execute(
            """
            INSERT INTO vertex_screenshot (
              vertex_id, created_date, sensitivity_ord, owner_did, rkey, url,
              domain, blob_ref, format, width, height, quality, file_size,
              content_hash, captured_at
            )
            VALUES (%s,%s,1,%s,%s,%s,%s,%s,'png',%s,%s,100,%s,%s,%s)
            """,
            (
                screenshot_id,
                created_date,
                OWNER_DID,
                rkey,
                url,
                domain,
                assets["screenshot"]["key"],
                assets["width"],
                assets["height"],
                assets["screenshot"]["bytes"],
                assets["screenshot"]["sha256"],
                crawled_at,
            ),
        )

        cur.execute(
            """
            UPDATE vertex_gov_source
               SET "coverageStage" = 'page-wet-wat-gyotaku-ingested',
                   "lastSeenAt" = %s,
                   props = %s
             WHERE vertex_id = %s
            """,
            (crawled_at, props, vertex_id("com.etzhayyim.gov.source", rkey)),
        )


def upsert_rows_with_retry(conn: Any, source: dict[str, str], assets: dict[str, Any]) -> None:
    last_error: Exception | None = None
    for attempt in range(1, 6):
        try:
            upsert_rows(conn, source, assets)
            return
        except Exception as error:  # noqa: BLE001
            last_error = error
            message = str(error)
            retryable = "SlowDown" in message or "RateLimited" in message or "temporary" in message
            if not retryable or attempt == 5:
                raise
            time.sleep(15 * attempt)
    if last_error:
        raise last_error


def main() -> None:
    rw_url = os.environ.get("KOTOBA_URL") or os.environ.get("DATABASE_URL") or keychain("etzhayyim.rw", "ROOT_URL")
    key_id = os.environ.get("etzhayyim_B2_KEY_ID") or keychain("etzhayyim.b2", "APPLICATION_KEY_ID")
    app_key = os.environ.get("etzhayyim_B2_APP_KEY") or keychain("etzhayyim.b2", "APPLICATION_KEY")
    client = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=key_id,
        aws_secret_access_key=app_key,
        region_name="us-west-004",
    )

    conn = psycopg2.connect(rw_url, connect_timeout=15)
    conn.autocommit = True
    try:
        only_rkey = os.environ.get("GOV_AGO_SOURCE_RKEY", "").strip()
        sources = [source for source in SOURCES if not only_rkey or source["rkey"] == only_rkey]
        if only_rkey and not sources:
            raise RuntimeError(f"unknown GOV_AGO_SOURCE_RKEY: {only_rkey}")
        for source in sources:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp = Path(tmp_dir)
                html_path = tmp / "page.html"
                png_path = tmp / "gyotaku.png"
                html_bytes = fetch_html(source["url"], html_path)
                width, height = render_screenshot(source["url"], png_path)
                base = f"{PREFIX}/{source['slug']}"
                html_meta = upload(client, f"{base}/page.html", html_path, "text/html")
                png_meta = upload(client, f"{base}/gyotaku.png", png_path, "image/png")
                upsert_rows_with_retry(
                    conn,
                    source,
                    {
                        "html": html_meta,
                        "screenshot": png_meta,
                        "html_bytes": html_bytes,
                        "html_text": html_bytes.decode("utf-8", errors="replace"),
                        "width": width,
                        "height": height,
                    },
                )
                print(
                    json.dumps(
                        {
                            "rkey": source["rkey"],
                            "url": source["url"],
                            "htmlBytes": html_meta["bytes"],
                            "screenshotBytes": png_meta["bytes"],
                            "width": width,
                            "height": height,
                        },
                        ensure_ascii=False,
                    )
                )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
