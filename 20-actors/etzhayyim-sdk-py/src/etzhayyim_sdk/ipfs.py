"""ipfs — IPFS pin/fetch helpers (real impl, M4).

Provides typed async wrappers for content-addressed blob storage via the
IPFS Kubo HTTP RPC API.  The singleton ``httpx.AsyncClient`` is compatible
with ``httpx.MockTransport`` injection for testing (see ``_inject_transport``).

Configuration (env vars):
  ETZHAYYIM_IPFS_API_URL — Kubo HTTP API base URL
                           (default: ``http://simeon.local:5001``).
                           The ipfs-pinner daemon on simeon hosts this node
                           (ADR-2605171800 Stage 3).

Auth:
  The Kubo HTTP API is localhost-bound on simeon and is not authenticated by
  default.  If the API is exposed externally, set ``ETZHAYYIM_IPFS_API_KEY``
  and the impl should add it as an ``Authorization`` header.

ADR references:
  ADR-2605171800 Stage 3 — IPFS pinning (simeon is the ipfs-pinner node)
  ADR-2605215200 §1 EvolutionEmissionCell — pins evolution evidence on simeon
  ADR-2605172000 — large blobs go to IPFS; CID embedded in MST record
  ADR-2605215200 §4 — M4 milestone target for full IPFS impl
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from etzhayyim_sdk.errors import IpfsError, IpfsNetworkError, IpfsServerError

# ---------------------------------------------------------------------------
# Module-level singleton client (lazy init, connection pooling)
# ---------------------------------------------------------------------------

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return the module-level singleton httpx.AsyncClient, creating it lazily."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


def _inject_transport(transport: httpx.AsyncBaseTransport) -> None:
    """Replace the module singleton with a client backed by *transport*.

    Called from tests to inject ``httpx.MockTransport`` without touching env
    vars or making real network calls.
    """
    global _client
    _client = httpx.AsyncClient(transport=transport, timeout=30.0)


def _kubo_endpoint() -> str:
    """Return the Kubo HTTP API base URL from env or the default."""
    return os.environ.get("ETZHAYYIM_IPFS_API_URL", "http://simeon.local:5001")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def pin(cid: str, *, recursive: bool = True) -> None:
    """Pin a CID to the local IPFS node (simeon).

    Calls ``POST /api/v0/pin/add?arg=<cid>&recursive=<true|false>`` on the
    Kubo HTTP RPC API.

    Args:
        cid:       CIDv1 (base32 multibase) to pin.
        recursive: Whether to pin recursively (default True, Kubo default).

    Returns:
        None on success.

    Raises:
        IpfsNetworkError: Transport / connection error (wraps httpx.HTTPError).
        IpfsServerError:  Non-200 response, or CID absent from ``Pins`` list.

    Kubo response shape::

        POST /api/v0/pin/add?arg=bafybeig5abc123&recursive=true
        200 {"Pins": ["bafybeig5abc123"], "Progress": ""}

    ADR-2605171800 Stage 3: pin must succeed on at least one local and one
    remote pinning service before the L2 anchor batch can include this CID.
    """
    client = _get_client()
    url = f"{_kubo_endpoint()}/api/v0/pin/add"
    try:
        resp = await client.post(
            url,
            params={"arg": cid, "recursive": str(recursive).lower()},
        )
    except httpx.HTTPError as exc:
        raise IpfsNetworkError(f"network error pinning {cid}: {exc}") from exc

    if resp.status_code != 200:
        raise IpfsServerError(
            f"pin failed for {cid}: HTTP {resp.status_code} body={resp.text[:200]}",
            status_code=resp.status_code,
            body=resp.text[:200],
        )
    body = resp.json()
    if cid not in body.get("Pins", []):
        raise IpfsServerError(
            f"pin response did not confirm {cid}: Pins={body.get('Pins')}",
            body=resp.text[:200],
        )


async def pin_many(cids: list[str], *, recursive: bool = True) -> None:
    """Batch-pin a list of CIDs to the local IPFS node (simeon).

    Iterates over *cids* and calls :func:`pin` for each.  Uses first-failure
    semantics: if any CID fails, the remaining CIDs are not attempted.

    Args:
        cids:      List of CIDv1 strings to pin.
        recursive: Passed through to each :func:`pin` call (default True).

    Raises:
        IpfsNetworkError: On transport failure for any CID.
        IpfsServerError:  On non-200 or unconfirmed pin for any CID.

    Note:
        Kubo's ``/api/v0/pin/add`` is idempotent — pinning an already-pinned
        CID returns 200 with the CID in ``Pins``.  All-or-nothing: if any pin
        fails, the emission must abort per the witness invariant
        (ADR-2605215200 §1 EvolutionEmissionCell).

    ADR-2605171800 Stage 3: no Kubo native batch API as of Kubo 0.27.
    """
    for cid in cids:
        await pin(cid, recursive=recursive)


async def unpin(cid: str, *, recursive: bool = True) -> None:
    """Unpin a CID from the local IPFS node.

    Calls ``POST /api/v0/pin/rm?arg=<cid>&recursive=<true|false>`` on the
    Kubo HTTP RPC API.

    Args:
        cid:       CIDv1 to unpin.
        recursive: Whether to remove recursively (default True).

    Raises:
        IpfsNetworkError: Transport / connection error.
        IpfsServerError:  Non-200 response (e.g. CID not pinned → Kubo 500).

    Warning:
        Use with care — if the CID is referenced by an on-chain L2 anchor,
        removing the pin breaks verifiability for that anchor.
        ADR-2605171800 §Failure modes: IPFS unpinning risk.

    Kubo response shape::

        POST /api/v0/pin/rm?arg=bafybeig5abc123&recursive=true
        200 {"Pins": ["bafybeig5abc123"]}
    """
    client = _get_client()
    url = f"{_kubo_endpoint()}/api/v0/pin/rm"
    try:
        resp = await client.post(
            url,
            params={"arg": cid, "recursive": str(recursive).lower()},
        )
    except httpx.HTTPError as exc:
        raise IpfsNetworkError(f"network error unpinning {cid}: {exc}") from exc

    if resp.status_code != 200:
        raise IpfsServerError(
            f"unpin failed for {cid}: HTTP {resp.status_code} body={resp.text[:200]}",
            status_code=resp.status_code,
            body=resp.text[:200],
        )


async def fetch(cid: str) -> bytes:
    """Fetch raw bytes for a CID from IPFS.

    Calls ``POST /api/v0/cat?arg=<cid>`` on the Kubo HTTP RPC API.
    The response body is the raw file content (not JSON).

    Args:
        cid: CIDv1 to fetch.

    Returns:
        Raw bytes of the content-addressed object.

    Raises:
        IpfsNetworkError: Transport / connection error.
        IpfsServerError:  Non-200 response (e.g. CID not available → 500).

    Note:
        For large blobs (>16 KiB per ADR-2605171800 §Stage 2
        blob_inline_threshold), streaming via ``httpx.AsyncClient.stream()``
        is preferred.  This synchronous-body impl is suitable for small objects.
        Stream upgrade is an M5 follow-up.

    Kubo response::

        POST /api/v0/cat?arg=bafybeig5abc123
        200 <raw bytes>
    """
    client = _get_client()
    url = f"{_kubo_endpoint()}/api/v0/cat"
    try:
        resp = await client.post(url, params={"arg": cid})
    except httpx.HTTPError as exc:
        raise IpfsNetworkError(f"network error fetching {cid}: {exc}") from exc

    if resp.status_code != 200:
        raise IpfsServerError(
            f"fetch failed for {cid}: HTTP {resp.status_code} body={resp.text[:200]}",
            status_code=resp.status_code,
            body=resp.text[:200],
        )
    return resp.content


async def add(data: bytes, *, pin: bool = True) -> str:
    """Add raw bytes to IPFS and return the resulting CID.

    Calls ``POST /api/v0/add`` with the raw bytes as ``multipart/form-data``.
    Kubo responds with ``{"Name":"…","Hash":"<cid>","Size":"…"}``.

    Args:
        data: Raw bytes to add.  Content is automatically content-addressed;
              the same bytes always produce the same CID (CIDv1, sha2-256,
              base32 multibase).
        pin:  Whether Kubo should pin the object automatically (default True,
              matches Kubo default behaviour).  Pass ``False`` for deferred-pin
              workflows.

    Returns:
        CIDv1 string (e.g. ``bafybeig5abc123…``).

    Raises:
        IpfsNetworkError: Transport / connection error.
        IpfsServerError:  Non-200 response or missing ``Hash`` field in body.

    Note:
        Kubo's ``/api/v0/add`` pins automatically by default (``pin=true``).
        An explicit :func:`pin` call after ``add`` is not required unless
        ``pin=False`` was passed here.

    Kubo request / response::

        POST /api/v0/add?pin=true
        Content-Type: multipart/form-data; boundary=…
        <binary body field name "file">
        Response: 200 {"Name":"QmHash","Hash":"bafybeig5abc123","Size":"42"}
    """
    client = _get_client()
    url = f"{_kubo_endpoint()}/api/v0/add"
    try:
        resp = await client.post(
            url,
            params={"pin": str(pin).lower()},
            files={"file": ("blob", data, "application/octet-stream")},
        )
    except httpx.HTTPError as exc:
        raise IpfsNetworkError(f"network error adding data: {exc}") from exc

    if resp.status_code != 200:
        raise IpfsServerError(
            f"add failed: HTTP {resp.status_code} body={resp.text[:200]}",
            status_code=resp.status_code,
            body=resp.text[:200],
        )
    body = resp.json()
    cid = body.get("Hash", "")
    if not cid:
        raise IpfsServerError(
            f"add response missing Hash field: {resp.text[:200]}",
            body=resp.text[:200],
        )
    return cid


async def pin_ls(cid: str | None = None) -> list[dict[str, Any]]:
    """List pinned CIDs on the local IPFS node.

    Calls ``POST /api/v0/pin/ls`` on the Kubo HTTP RPC API.

    Args:
        cid: Optional CIDv1 to filter.  If None, lists all pinned CIDs.

    Returns:
        List of dicts with ``{"cid": str, "type": str}`` entries.
        The ``type`` field is one of ``"recursive"``, ``"direct"``,
        ``"indirect"``.  Returns an empty list if nothing is pinned.

    Raises:
        IpfsNetworkError: Transport / connection error.
        IpfsServerError:  Non-200 response.

    Kubo response shape (abbreviated)::

        POST /api/v0/pin/ls
        200 {"Keys": {"bafybeig5abc123": {"Type": "recursive"}, ...}}
    """
    client = _get_client()
    url = f"{_kubo_endpoint()}/api/v0/pin/ls"
    params: dict[str, str] = {}
    if cid is not None:
        params["arg"] = cid
    try:
        resp = await client.post(url, params=params)
    except httpx.HTTPError as exc:
        raise IpfsNetworkError(f"network error listing pins: {exc}") from exc

    if resp.status_code != 200:
        raise IpfsServerError(
            f"pin/ls failed: HTTP {resp.status_code} body={resp.text[:200]}",
            status_code=resp.status_code,
            body=resp.text[:200],
        )
    body = resp.json()
    keys: dict[str, Any] = body.get("Keys", {})
    return [{"cid": k, "type": v.get("Type", "")} for k, v in keys.items()]


# ---------------------------------------------------------------------------
# Higher-level helpers
# ---------------------------------------------------------------------------


async def pin_record(
    mst_rkey: str,
    evidence_cids: list[str],
) -> str:
    """Pin a set of evidence CIDs + MST rkey reference and return the aggregate CID.

    Used by EvolutionEmissionCell to produce a single pinned CID that captures
    both the MST record reference and the supporting evidence.

    Implementation:
      1. Serialise ``{"mst_rkey": mst_rkey, "evidence_cids": evidence_cids}``
         as UTF-8 JSON bytes.
      2. Call :func:`add` to store + pin the manifest; returns an aggregate CID.
      3. Call :func:`pin_many` on *evidence_cids* so all evidence is locally
         reachable.
      4. Return the aggregate CID.

    ADR-2605215200 §1 EvolutionEmissionCell write path.
    """
    import json as _json

    manifest = _json.dumps(
        {"mst_rkey": mst_rkey, "evidence_cids": evidence_cids},
        sort_keys=True,
    ).encode()
    aggregate_cid = await add(manifest, pin=True)
    if evidence_cids:
        await pin_many(evidence_cids)
    return aggregate_cid
