"""Emit ``com.etzhayyim.substrate.datasetPin`` records to PDS.

Mirrors the auth + emit pattern of ``50-infra/ipfs-pinner/src/emit.ts``
(AtpAgent / com.atproto.repo.createRecord), but in Python via httpx —
no atproto SDK dep.

Environment contract:

  ETZ_E7M_PDS_URL        default: https://pds.etzhayyim.com
  ETZ_E7M_PDS_DID        repo DID to write under (e.g. did:web:e7m-dataset.etzhayyim.com)
  ETZ_E7M_PDS_SESSION    JSON {did, handle, accessJwt, refreshJwt}     (preferred)
  ETZ_E7M_PDS_AUTH       JSON {handle, password}                       (fallback)

If neither SESSION nor AUTH is set the emitter refuses to POST. Use
``dry_run=True`` (default for the CLI Phase 1 window) to print the
record body instead.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Optional

import httpx


COLLECTION = "com.etzhayyim.substrate.datasetPin"
DEFAULT_PDS = "https://pds.etzhayyim.com"
DEFAULT_DID = "did:web:dataset-pinner.etzhayyim.com"


class PdsError(RuntimeError):
    pass


def _client(*, headers: dict[str, str] | None = None) -> httpx.Client:
    return httpx.Client(
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
        headers=headers or {},
    )


def _resolve_session(pds_url: str) -> tuple[str, dict[str, Any]]:
    raw_session = os.environ.get("ETZ_E7M_PDS_SESSION")
    if raw_session:
        s = json.loads(raw_session)
        if not all(k in s for k in ("did", "handle", "accessJwt", "refreshJwt")):
            raise PdsError("ETZ_E7M_PDS_SESSION missing required keys")
        return s["did"], s

    raw_auth = os.environ.get("ETZ_E7M_PDS_AUTH")
    if not raw_auth:
        raise PdsError(
            "PDS emit requires ETZ_E7M_PDS_SESSION or ETZ_E7M_PDS_AUTH "
            "(JSON-encoded credentials). See pds.py docstring."
        )
    auth = json.loads(raw_auth)
    if not all(k in auth for k in ("handle", "password")):
        raise PdsError("ETZ_E7M_PDS_AUTH missing 'handle' or 'password'")
    with _client() as c:
        r = c.post(
            f"{pds_url.rstrip('/')}/xrpc/com.atproto.server.createSession",
            json={"identifier": auth["handle"], "password": auth["password"]},
        )
        if r.status_code >= 300:
            raise PdsError(f"createSession failed: {r.status_code} {r.text!r}")
        sess = r.json()
    return sess["did"], sess


def build_record(
    *,
    name: str,
    revision: str,
    kind: str,
    cid: str,
    size_bytes: int,
    sha256: str | None,
    providers: list[str],
    pinned_at: str,
    charter_rider_scan: dict[str, Any],
    assigned_nodes: list[str] | None = None,
    source: dict[str, Any] | None = None,
    license: str | None = None,
    manifest_row_ref: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "$type": COLLECTION,
        "name": name,
        "revision": revision,
        "kind": kind,
        "cid": cid,
        "sizeBytes": size_bytes,
        "providers": providers,
        "pinnedAt": pinned_at,
        "charterRiderScan": charter_rider_scan,
    }
    if sha256:
        body["sha256"] = sha256
    if assigned_nodes:
        body["assignedNodes"] = assigned_nodes
    if source:
        body["source"] = source
    if license:
        body["license"] = license
    if manifest_row_ref:
        body["manifestRowRef"] = manifest_row_ref
    return body


def emit(record: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
    """Create the record on PDS, or print it in dry-run mode.

    Returns ``{dryRun: true}`` in dry-run mode, otherwise the response
    body from ``com.atproto.repo.createRecord`` (which contains ``uri``
    and ``cid``).
    """
    if dry_run:
        print(
            "[e7m-dataset/pds] DRY RUN — would create record:\n"
            + json.dumps(record, indent=2, sort_keys=True),
            file=sys.stderr,
        )
        return {"dryRun": True}

    pds_url = os.environ.get("ETZ_E7M_PDS_URL", DEFAULT_PDS).rstrip("/")
    sess_did, sess = _resolve_session(pds_url)
    repo_did = os.environ.get("ETZ_E7M_PDS_DID", DEFAULT_DID if sess_did != DEFAULT_DID else sess_did)

    with _client(headers={"Authorization": f"Bearer {sess['accessJwt']}"}) as c:
        r = c.post(
            f"{pds_url}/xrpc/com.atproto.repo.createRecord",
            json={
                "repo": repo_did,
                "collection": COLLECTION,
                "record": record,
            },
        )
        if r.status_code >= 300:
            raise PdsError(
                f"createRecord failed: {r.status_code} {r.text!r}"
            )
        return r.json()


_AT_URI_RE = re.compile(
    r"^at://(?P<repo>[^/]+)/(?P<collection>[^/]+)/(?P<rkey>[^/?#]+)$"
)


def parse_at_uri(at_uri: str) -> tuple[str, str, str]:
    """Parse `at://<repo>/<collection>/<rkey>` → (repo, collection, rkey).

    Raises PdsError on bad shape. Used by `resolve_datasetpin` to look
    up the record + by callers wanting structural validation."""
    m = _AT_URI_RE.match(at_uri)
    if m is None:
        raise PdsError(f"bad at-uri shape: {at_uri!r}")
    return m.group("repo"), m.group("collection"), m.group("rkey")


def resolve_datasetpin(
    at_uri: str,
    *,
    pds_url: Optional[str] = None,
    timeout_sec: float = 30.0,
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Resolve an `at://...datasetPin/<rkey>` AT URI → record value.

    Returns the record body containing at minimum ``cid`` (the IPFS
    pin map CID per ADR-2605241500 §D contract). Auth is anonymous —
    `com.etzhayyim.substrate.datasetPin` records are public-readable
    (Charter Rider §2(c) anti-surveillance compatible: read traffic
    leaks only public CID identifiers, not member identity).

    Raises PdsError on any non-2xx response (including 404 for missing
    records; callers should catch and fall back as needed).

    Pattern adapted from `50-infra/ipfs-pinner/src/emit.ts` `getRecord`
    helper. Used by assemble-usd-scene.py to upgrade the W1 sha256
    placeholder to real CID resolution.
    """
    repo, collection, rkey = parse_at_uri(at_uri)
    if collection != COLLECTION:
        raise PdsError(
            f"expected collection={COLLECTION!r}; got {collection!r}"
        )
    base = (pds_url or os.environ.get("ETZ_E7M_PDS_URL", DEFAULT_PDS)).rstrip("/")
    url = f"{base}/xrpc/com.atproto.repo.getRecord"
    params = {"repo": repo, "collection": collection, "rkey": rkey}

    owned = client is None
    c = client or httpx.Client(timeout=timeout_sec, follow_redirects=True)
    try:
        r = c.get(url, params=params)
        if r.status_code >= 300:
            raise PdsError(
                f"getRecord failed: {r.status_code} {r.text!r}"
            )
        body = r.json()
        value = body.get("value")
        if not isinstance(value, dict) or "cid" not in value:
            raise PdsError(
                f"datasetPin record at {at_uri!r} missing required `cid`"
            )
        return value
    finally:
        if owned:
            c.close()


__all__ = [
    "COLLECTION",
    "DEFAULT_PDS",
    "PdsError",
    "build_record",
    "emit",
    "parse_at_uri",
    "resolve_datasetpin",
]
