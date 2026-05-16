"""Source-fetch helpers for the manimani parse_input node (Phase 3,
ADR-2605080800).

Phase 1/2 stored ``sourceUri`` verbatim as the parsed text. Phase 3
adds:

  - :func:`fetch_url`            HTTP GET + readable-text extraction
  - :func:`fetch_b2_file_ref`    b2:// SigV4 GET + content-type sniff
  - :func:`extract_readable_text` — trafilatura primary,
                                    BeautifulSoup fallback,
                                    plain-text passthrough

Failure model: every fetcher returns a ``FetchResult`` with an explicit
``error`` field instead of raising. The graph node treats a fetch error
the same way it treats a missing field: it routes the intake into a
``defer_for_user_review`` artifact (raw passthrough of the URI string)
so the row still lands.

Size cap: ``MANIMANI_FETCH_MAX_BYTES`` env (default 4 MiB). Bodies past
the cap are truncated, never raised.

trafilatura is an optional dep. When unavailable, the fallback chain is
``BeautifulSoup`` → naive regex strip. All three produce
"reasonable-enough" text for downstream LLM processing.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import io
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional


# ── shared types ─────────────────────────────────────────────────────


@dataclass
class FetchResult:
    """Outcome of a single source fetch.

    ``parsed_text`` is the human-readable extraction (HTML stripped, JSON
    pretty-printed, plain-text passthrough). ``raw_byte_size`` reflects
    the *fetched* body size, before extraction.
    """

    parsed_text: str
    content_type: Optional[str]
    raw_byte_size: int
    error: Optional[str] = None


def _max_bytes() -> int:
    try:
        return max(1024, int(os.environ.get("MANIMANI_FETCH_MAX_BYTES", str(4 * 1024 * 1024))))
    except ValueError:
        return 4 * 1024 * 1024


def _fetch_timeout_sec() -> float:
    try:
        return max(1.0, float(os.environ.get("MANIMANI_FETCH_TIMEOUT_SEC", "10")))
    except ValueError:
        return 10.0


# ── URL fetch ────────────────────────────────────────────────────────


_DEFAULT_UA = (
    "Mozilla/5.0 (compatible; manimani/1.0; "
    "+https://manimani.gftd.ai)"
)


def fetch_url(url: str) -> FetchResult:
    """HTTP GET + readability extraction.

    Only ``http`` and ``https`` schemes are accepted. Non-text content
    types are summarized to a 1-line metadata blurb (we don't ship raw
    bytes back through the graph state).
    """

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return FetchResult(parsed_text=url, content_type=None, raw_byte_size=0,
                           error=f"unsupported scheme: {parsed.scheme!r}")

    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": _DEFAULT_UA,
            "Accept": "text/html,application/json,text/*;q=0.9,*/*;q=0.5",
            "Accept-Language": "en;q=0.9, ja;q=0.8",
        },
    )
    body: bytes
    content_type: str | None
    try:
        with urllib.request.urlopen(req, timeout=_fetch_timeout_sec()) as resp:
            content_type = (resp.headers.get("content-type") or "").lower() or None
            body = resp.read(_max_bytes() + 1)
    except Exception as exc:
        return FetchResult(parsed_text=url, content_type=None, raw_byte_size=0,
                           error=f"fetch failed: {type(exc).__name__}: {exc}")

    truncated = len(body) > _max_bytes()
    if truncated:
        body = body[: _max_bytes()]

    parsed_text = extract_readable_text(body, content_type=content_type, source_uri=url)
    if truncated:
        parsed_text = parsed_text + "\n\n[truncated by manimani fetch cap]"

    return FetchResult(
        parsed_text=parsed_text,
        content_type=content_type,
        raw_byte_size=len(body),
    )


# ── B2 file_ref fetch (SigV4) ────────────────────────────────────────


_B2_PREFIX = "b2://"


def fetch_b2_file_ref(uri: str) -> FetchResult:
    """``b2://bucket/key`` → SigV4 signed GET against the configured
    Backblaze endpoint. Reuses the ``B2_*`` env block already wired in
    the manimani / voxelforge Helm releases.

    Returns the body decoded as text when the content-type is text-like;
    otherwise emits a one-line metadata blurb (size + content-type +
    sha-256 prefix). The graph never inlines arbitrary binary bytes
    into the LangGraph state.
    """

    if not uri.startswith(_B2_PREFIX):
        return FetchResult(parsed_text=uri, content_type=None, raw_byte_size=0,
                           error="not a b2:// reference")
    rest = uri[len(_B2_PREFIX) :]
    if "/" not in rest:
        return FetchResult(parsed_text=uri, content_type=None, raw_byte_size=0,
                           error="b2 uri must be b2://bucket/key")
    bucket, key = rest.split("/", 1)
    if not bucket or not key:
        return FetchResult(parsed_text=uri, content_type=None, raw_byte_size=0,
                           error="b2 uri must be b2://bucket/key")

    endpoint = os.environ.get("B2_ENDPOINT_URL") or "https://s3.us-west-004.backblazeb2.com"
    region = os.environ.get("B2_REGION") or "us-west-004"
    access_key = os.environ.get("B2_ACCESS_KEY_ID") or ""
    secret_key = os.environ.get("B2_SECRET_ACCESS_KEY") or ""
    if not access_key or not secret_key:
        return FetchResult(parsed_text=uri, content_type=None, raw_byte_size=0,
                           error="B2 credentials not configured (B2_ACCESS_KEY_ID / B2_SECRET_ACCESS_KEY)")

    host = urllib.parse.urlparse(endpoint).netloc
    canonical_uri = "/" + bucket + "/" + urllib.parse.quote(key, safe="/-_.~")

    req_url = f"{endpoint.rstrip('/')}/{bucket}/{urllib.parse.quote(key, safe='/-_.~')}"
    headers = _sigv4_get_headers(
        method="GET",
        canonical_uri=canonical_uri,
        host=host,
        region=region,
        service="s3",
        access_key=access_key,
        secret_key=secret_key,
    )

    req = urllib.request.Request(req_url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_fetch_timeout_sec()) as resp:
            content_type = (resp.headers.get("content-type") or "").lower() or None
            body = resp.read(_max_bytes() + 1)
    except Exception as exc:
        return FetchResult(parsed_text=uri, content_type=None, raw_byte_size=0,
                           error=f"b2 GET failed: {type(exc).__name__}: {exc}")

    truncated = len(body) > _max_bytes()
    if truncated:
        body = body[: _max_bytes()]

    parsed_text = extract_readable_text(body, content_type=content_type, source_uri=uri)
    if truncated:
        parsed_text = parsed_text + "\n\n[truncated by manimani fetch cap]"

    return FetchResult(
        parsed_text=parsed_text,
        content_type=content_type,
        raw_byte_size=len(body),
    )


# ── extraction ───────────────────────────────────────────────────────


_TEXTLIKE_CT = re.compile(r"^(text/|application/(json|xml|x?html|atom\+xml|rss\+xml|ld\+json|yaml|toml))")


def extract_readable_text(
    body: bytes,
    *,
    content_type: str | None,
    source_uri: str | None = None,
) -> str:
    """Pick the best extractor for the content-type. Returns text only.

    Order of preference for HTML:
      1. trafilatura (if installed) — strongest readability output.
      2. BeautifulSoup ``get_text(' ')`` — good fallback, ships with
         ``beautifulsoup4`` (already a dep of multiple primitives).
      3. naive ``<tag>`` strip + entity unescape — last resort.

    For JSON / YAML / TOML / XML the body is decoded as UTF-8 and
    pretty-printed. For binary content-types we emit a one-line metadata
    blurb (size + sha-256 prefix) so the graph still has *something* to
    classify on.
    """

    ct = (content_type or "").split(";")[0].strip().lower()

    if not body:
        return ""

    # Binary / unknown — return a metadata blurb (the graph classifies it as memo/unsorted).
    if ct and not _TEXTLIKE_CT.match(ct):
        return _binary_blurb(body, content_type=ct, source_uri=source_uri)

    text = _decode_best_effort(body)

    if ct.startswith("application/json") or ct.endswith("+json") or ct == "application/ld+json":
        try:
            return json.dumps(json.loads(text), indent=2, ensure_ascii=False)[:32_000]
        except Exception:
            return text[:32_000]

    if ct in ("text/html", "application/xhtml+xml") or "<html" in text[:1024].lower():
        return _html_to_text(text)[:32_000]

    if ct in ("text/xml", "application/xml") or ct.endswith("+xml"):
        # Strip XML tags as a courtesy; we don't try to preserve structure.
        return _strip_tags(text)[:32_000]

    # Everything else: plain text passthrough (capped).
    return text[:32_000]


def _decode_best_effort(body: bytes) -> str:
    for enc in ("utf-8", "utf-16", "shift_jis", "euc-jp", "latin-1"):
        try:
            return body.decode(enc)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def _html_to_text(html: str) -> str:
    # 1. trafilatura
    try:  # pragma: no cover — optional dep
        import trafilatura  # type: ignore

        out = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            favor_recall=True,
        )
        if out and out.strip():
            return out.strip()
    except Exception:
        pass

    # 2. BeautifulSoup
    try:  # pragma: no cover — optional dep but widely installed
        from bs4 import BeautifulSoup  # type: ignore

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(("script", "style", "noscript", "template")):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        if text:
            return _collapse_whitespace(text)
    except Exception:
        pass

    # 3. naive
    return _collapse_whitespace(_strip_tags(html))


def _strip_tags(s: str) -> str:
    s = re.sub(r"<script\b[^>]*>.*?</script>", " ", s, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub(r"<style\b[^>]*>.*?</style>", " ", s, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub(r"<[^>]+>", " ", s)
    s = _unescape_entities(s)
    return _collapse_whitespace(s)


def _unescape_entities(s: str) -> str:
    try:
        import html as _html

        return _html.unescape(s)
    except Exception:
        return s


def _collapse_whitespace(s: str) -> str:
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _binary_blurb(body: bytes, *, content_type: str | None, source_uri: str | None) -> str:
    sha = hashlib.sha256(body).hexdigest()[:16]
    parts = [
        f"binary content_type={content_type or 'unknown'}",
        f"size={len(body)}",
        f"sha256={sha}…",
    ]
    if source_uri:
        parts.append(f"uri={source_uri}")
    return " ".join(parts)


# ── SigV4 (minimal GET) ──────────────────────────────────────────────


def _sigv4_get_headers(
    *,
    method: str,
    canonical_uri: str,
    host: str,
    region: str,
    service: str,
    access_key: str,
    secret_key: str,
) -> dict[str, str]:
    """Sign a single GET request to S3-compatible storage (Backblaze B2).

    Mirrors the SigV4 logic used in ``pymagatama.voxelforge.converters``
    but for GET (no payload). Empty body → SHA-256 = e3b0c44…b855.
    """

    now = _dt.datetime.now(_dt.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    payload_hash = hashlib.sha256(b"").hexdigest()
    canonical_querystring = ""
    canonical_headers = (
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_request = (
        f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
        f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )
    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n{amz_date}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    def _sign(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    k_date = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    auth = (
        f"{algorithm} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    return {
        "Host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
        "Authorization": auth,
    }
