"""Minimal Kubo HTTP API client (httpx).

Two endpoints, called as multipart POSTs:

- POST /api/v0/add?cid-version=1&pin=true   — returns NDJSON; root CID is the last line's Hash
- POST /api/v0/pin/add?arg=<cid>            — confirms pin

Network contract is identical to the one used by `50-infra/ipfs-pinner/`
(TypeScript). They intentionally do not share a library — they share an
API.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx


class KuboError(RuntimeError):
    pass


def _trim(url: str) -> str:
    return url.rstrip("/")


def _client() -> httpx.Client:
    return httpx.Client(timeout=httpx.Timeout(120.0, connect=10.0), follow_redirects=True)


def _parse_ndjson_last_hash(raw: str) -> str:
    last: str | None = None
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        h = obj.get("Hash")
        if isinstance(h, str):
            last = h
    if not last:
        raise KuboError(f"ipfs /add returned no Hash: {raw!r}")
    return last


def add_file(api_url: str, path: Path) -> str:
    """`ipfs add --cid-version=1 --pin=true <path>` → root CID."""
    url = f"{_trim(api_url)}/api/v0/add?cid-version=1&pin=true&quieter=true"
    with _client() as c:
        with path.open("rb") as fh:
            r = c.post(url, files={"file": (path.name, fh, "application/octet-stream")})
    if r.status_code >= 300:
        raise KuboError(f"{url} returned {r.status_code}: {r.text!r}")
    return _parse_ndjson_last_hash(r.text)


def add_bytes(api_url: str, payload: bytes, filename: str = "blob.json") -> str:
    """Add an in-memory bytes object (used for the map JSON)."""
    url = f"{_trim(api_url)}/api/v0/add?cid-version=1&pin=true&quieter=true"
    with _client() as c:
        r = c.post(url, files={"file": (filename, payload, "application/octet-stream")})
    if r.status_code >= 300:
        raise KuboError(f"{url} returned {r.status_code}: {r.text!r}")
    return _parse_ndjson_last_hash(r.text)


def cat(api_url: str, cid: str) -> bytes:
    """Fetch a CID's bytes via /api/v0/cat (for verify)."""
    url = f"{_trim(api_url)}/api/v0/cat?arg={cid}"
    with _client() as c:
        r = c.post(url)
    if r.status_code >= 300:
        raise KuboError(f"ipfs cat {cid} returned {r.status_code}: {r.text!r}")
    return r.content


def pin_add(api_url: str, cid: str) -> bool:
    """Idempotent recursive pin (used by callers that uploaded via a non-pinning path)."""
    url = f"{_trim(api_url)}/api/v0/pin/add?arg={cid}&recursive=true"
    with _client() as c:
        r = c.post(url)
    if r.status_code >= 300:
        raise KuboError(f"pin/add {cid} returned {r.status_code}: {r.text!r}")
    body = r.json()
    pins = body.get("Pins")
    return isinstance(pins, list) and cid in pins
