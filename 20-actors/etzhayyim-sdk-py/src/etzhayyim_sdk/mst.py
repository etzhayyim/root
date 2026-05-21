"""mst — MST query helpers (real impl, M3).

Provides typed wrappers over PDS MST traversal for reading adherent state and
kyumei signals.  All reads delegate to :mod:`etzhayyim_sdk.pds` which owns
the singleton httpx.AsyncClient.

Configuration (env vars):
  ETZHAYYIM_PDS_DEFAULT_REPO — default repo DID/handle when *repo* is None.
                                Falls back to ``"did:web:etzhayyim.com"``.

ADR references:
  ADR-2605171800 — LangGraph MST → IPFS → Base L2 anchor pipeline
  ADR-2605215200 §2 — substrate write-path mapping (SELECT → MST query)
  ADR-2605215300 §3 — per-function SELECT mapping (rows #10/#11/#12/#14)
"""

from __future__ import annotations

import asyncio
import datetime
import io
import logging
import os
from typing import Any, AsyncIterator

import cbor2
import websockets
from websockets.exceptions import ConnectionClosedError, WebSocketException

from etzhayyim_sdk import pds
from etzhayyim_sdk.errors import MstSubscribeError

_log = logging.getLogger(__name__)

# ── Bootstrap Council Lv6 DID roster (ADR-2605192300 § Bootstrap Council) ──────
#
# COUNCIL_LV6_DIDS: Lazy-cached bootstrap fallback set. Contains DIDs of Council
# members at Lv6+. Initially hardcoded (Founder seat 1 only) for offline/test
# scenarios. At runtime, prefer get_council_lv6_dids() which queries the live
# app.etzhayyim.council.member registry.
#
# Bootstrap period: RFP closes 2026-06-19. Seats 2-5 get added via ratified
# council.member records after that. SDK dynamically picks up new members
# via get_council_lv6_dids() queries.
#
# Per ADR-2605215400 §3.4 and ADR-2605192300 § Bootstrap Council.
COUNCIL_LV6_DIDS: set[str] = {
    "did:web:etzhayyim.com",  # Founder seat 1 (per ADR-2605192300)
    # Seats 2-5: populated by post-RFP-close ratification records (2026-06-19+)
}


def _default_repo() -> str:
    return os.environ.get("ETZHAYYIM_PDS_DEFAULT_REPO", "did:web:etzhayyim.com")


async def get_council_lv6_dids() -> set[str]:
    """Fetch live Council Lv6+ DIDs from app.etzhayyim.council.member registry.

    Queries the Council member registry and returns DIDs of all members with
    level >= 6 and a ratified status (ratifiedAt is set).

    This function is the canonical runtime source for Council membership. It
    replaces the static COUNCIL_LV6_DIDS fallback. Use this in production code
    that needs fresh Council membership data.

    Returns:
        Set of DIDs (strings) for Lv6+ Council members.

    Raises:
        PdsAuthError, PdsNotFoundError, PdsServerError, PdsNetworkError.

    ADR-2605215400 §3.4 Council Lv6+ DID Registry:
        This method queries app.etzhayyim.council.member records where:
        - level >= 6 (Lv6 or Lv7)
        - ratifiedAt is not null (member has been formally seated)
        Returns the set of member DIDs.

    Bootstrap fallback (ADR-2605192300 § Bootstrap Council):
        Before 2026-06-19, only Founder seat 1 is ratified. After RFP close,
        seats 2-5 ratified records are written by Council and this function
        automatically picks them up.
    """
    records = await query(
        "app.etzhayyim.council.member",
        filter={"level": 6},  # Note: also captures level 7 (>= 6)
        limit=100,  # Max 5 for bootstrap, future-proofed for Phase 2 expansion
    )

    council_dids: set[str] = set()
    for rec in records:
        value: dict[str, Any] = rec.get("value", {})
        level: int = value.get("level", 0)
        ratified_at: str = value.get("ratifiedAt", "")
        did: str = value.get("did", "")

        # Include member if level >= 6 and ratifiedAt is set (formally seated).
        if level >= 6 and ratified_at and did:
            council_dids.add(did)

    return council_dids


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def query(
    collection: str,
    *,
    repo: str | None = None,
    filter: dict[str, Any] | None = None,
    limit: int = 100,
    # Legacy kwargs from old signature — kept for backward compat
    did: str = "",
    filter_did: str = "",
    since: str = "",
    sort: str = "desc",
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Query MST records from the PDS by collection + optional client-side filter.

    Wraps :func:`pds.list_records` then applies *filter* client-side.  For
    collections with >100 records, only the first page is returned; use
    pagination via :func:`list_records` directly for deeper traversal.

    Maps vendor pattern:
      SELECT FROM vertex_* WHERE … → listRecords + client-side filter

    Args:
        collection: NSID of the record collection.
        repo:       Repo DID/handle.  Defaults to ``ETZHAYYIM_PDS_DEFAULT_REPO``.
        filter:     Optional dict of field → expected-value pairs applied
                    client-side to ``record["value"]``.  Only records where
                    all filter keys match are returned.
        limit:      Max records to fetch from PDS (1–100).

    Returns:
        List of matching record dicts ``{uri, cid, value}``.

    Raises:
        PdsAuthError, PdsNotFoundError, PdsServerError, PdsNetworkError.

    Used by:
      KarmaHegemonObservationCell — reads ``app.etzhayyim.shinka.kyumeiSignal``
        for a given adherent DID since last evolution timestamp.
      EvolutionValidationCell — reads ``app.etzhayyim.shinka.observeAdherent``
        via the council attestation registry.

    ADR-2605215200 §2:
      SELECT FROM vertex_kyumei_signal → MST listener on kyumeiSignal collection
      SELECT FROM vertex_koji_attestation → MST query via Council attestation registry
    ADR-2605215300 §3 rows #11/#14.
    """
    # Resolve effective repo — prefer explicit arg, then legacy ``did`` kwarg,
    # then env / hardcoded default.
    effective_repo = repo or did or _default_repo()

    # Merge legacy ``filters`` kwarg into ``filter``.
    effective_filter: dict[str, Any] | None = filter or filters or None

    result = await pds.list_records(effective_repo, collection, limit=limit)
    records: list[dict[str, Any]] = result.get("records", [])

    if effective_filter:
        records = [
            r for r in records
            if all(r.get("value", {}).get(k) == v for k, v in effective_filter.items())
        ]

    return records


async def get_by_uri(uri: str) -> dict[str, Any]:
    """Fetch a single MST record by AT URI.

    Wraps :func:`pds.get_record`.  Returns the full record dict
    ``{uri, cid, value}``.

    Args:
        uri: AT URI of the record (``at://repo/collection/rkey``).

    Raises:
        PdsAuthError, PdsNotFoundError, PdsServerError, PdsNetworkError.
        ValueError: if *uri* is malformed.

    ADR-2605215300 §3 (SELECT mapping row #10).
    """
    return await pds.get_record(uri)


async def get(
    collection: str,
    *,
    repo: str,
    rkey: str = "self",
) -> dict[str, Any] | None:
    """Fetch a single MST record by (repo, collection, rkey).

    Maps vendor pattern:
      SELECT FROM vertex_profile WHERE did=… → getRecord(actor.profile, rkey=self)

    Returns None if the record is not found (PdsNotFoundError is swallowed).

    ADR-2605215300 §3 (SELECT mapping rows #10/#11).
    """
    from etzhayyim_sdk.errors import PdsNotFoundError

    uri = f"at://{repo}/{collection}/{rkey}"
    try:
        return await pds.get_record(uri)
    except PdsNotFoundError:
        return None


def _firehose_ws_url() -> str:
    """Construct the firehose WebSocket URL from ETZHAYYIM_PDS_URL env var."""
    pds_url = os.environ.get("ETZHAYYIM_PDS_URL", "https://atproto.etzhayyim.com")
    ws_url = pds_url.replace("https://", "wss://").replace("http://", "ws://")
    return f"{ws_url}/xrpc/com.atproto.sync.subscribeRepos"


async def subscribe(
    collections: list[str] | None = None,
    *,
    since_cursor: int | None = None,
    reconnect_max_attempts: int = 10,
    reconnect_backoff_seconds: float = 2.0,
) -> AsyncIterator[dict[str, Any]]:
    """Subscribe to MST commit firehose via com.atproto.sync.subscribeRepos.

    Yields commit events as dicts::

        {
            "seq":        int,          # monotonic sequence number (use as cursor)
            "repo":       str,          # DID of the repo that committed
            "commit_cid": str,          # CID of the MST commit
            "ops":        list[dict],   # list of record ops {action, path, cid}
            "blocks":     bytes,        # raw CAR-encoded MST blocks (CBOR frames)
        }

    Filters client-side by collection names if *collections* is provided.
    Reconnects on disconnect with exponential backoff up to
    *reconnect_max_attempts*.  Cursor persistence is caller responsibility —
    pass the ``seq`` field of the last yielded event as *since_cursor* on
    reconnect.

    Args:
        collections:             Optional list of NSID collection names to
                                 filter client-side (e.g.
                                 ``["app.etzhayyim.shinka.kyumeiSignal"]``).
                                 ``None`` yields all collections.
        since_cursor:            Integer sequence number to resume from.
                                 Passed as ``?cursor=<n>`` in the WebSocket URL.
        reconnect_max_attempts:  Maximum reconnect attempts before raising
                                 ``MstSubscribeError`` (default 10).
        reconnect_backoff_seconds: Initial backoff in seconds; doubles on each
                                 attempt (exponential, capped at 60 s).

    Raises:
        MstSubscribeError: After *reconnect_max_attempts* exceeded, or on a
                           firehose-level error frame from the server.

    ADR reference: ADR-2605215200 §1 KarmaHegemonObservationCell.
    """
    cursor = since_cursor
    attempt = 0

    while attempt < reconnect_max_attempts:
        url = _firehose_ws_url()
        if cursor is not None:
            url = f"{url}?cursor={cursor}"

        try:
            async with websockets.connect(url, max_size=16 * 1024 * 1024) as ws:
                attempt = 0  # reset on successful connect
                _log.info("subscribed to firehose at %s (cursor=%s)", url, cursor)

                async for message in ws:
                    if isinstance(message, str):
                        _log.warning("unexpected text frame, skipping")
                        continue

                    # AT Protocol firehose frames: 2 concatenated CBOR objects.
                    # header {op: 1, t: "#commit"} + payload {seq, repo, commit, ops, blocks}
                    try:
                        buf = io.BytesIO(message)
                        decoder = cbor2.CBORDecoder(buf)
                        header = decoder.decode()
                        payload = decoder.decode()
                    except Exception as exc:
                        _log.warning("cbor decode failed, skipping frame: %s", exc)
                        continue

                    if header.get("op") == -1:
                        # Error frame from server
                        err = (
                            payload.get("error", "unknown")
                            if isinstance(payload, dict)
                            else str(payload)
                        )
                        raise MstSubscribeError(
                            f"firehose error frame: {err}",
                            attempts=attempt,
                        )

                    if not isinstance(payload, dict):
                        continue

                    # Update cursor tracking
                    if "seq" in payload:
                        cursor = payload["seq"]

                    # Client-side collection filter
                    if collections is not None:
                        ops = payload.get("ops", [])
                        matching_ops = [
                            op for op in ops
                            if any(op.get("path", "").startswith(c) for c in collections)
                        ]
                        if not matching_ops:
                            continue
                        payload = dict(payload)
                        payload["ops"] = matching_ops

                    yield payload

        except (ConnectionClosedError, WebSocketException, OSError) as exc:
            attempt += 1
            if attempt >= reconnect_max_attempts:
                raise MstSubscribeError(
                    f"firehose reconnect exhausted ({attempt} attempts): {exc}",
                    attempts=attempt,
                ) from exc

            wait = min(reconnect_backoff_seconds * (2 ** (attempt - 1)), 60.0)
            _log.warning(
                "firehose disconnect (attempt %d/%d), retry in %.1fs: %s",
                attempt, reconnect_max_attempts, wait, exc,
            )
            await asyncio.sleep(wait)

    raise MstSubscribeError(
        f"firehose reconnect exhausted ({reconnect_max_attempts} attempts)",
        attempts=reconnect_max_attempts,
    )


async def count(
    collection: str,
    *,
    repo: str = "",
    filters: dict[str, Any] | None = None,
) -> int:
    """Count MST records in a collection.

    Low-volume implementation: fetches up to 100 records and returns len().
    For heavy aggregates, use the mst-projector (50-infra/mst-projector/).

    Maps vendor pattern:
      SELECT count(*) FROM vertex_repo_record → listRecords client-side count

    ADR-2605215300 §3 note:
      Low-volume counts can use listRecords client-side until M3.
      Heavy counts must go through mst-projector (50-infra/mst-projector/, scaffold).
    """
    records = await query(collection, repo=repo or None, filters=filters)
    return len(records)


async def council_attestation_details(
    subject_did: str,
    level: int,
    *,
    since_days: int = 365,
    council_dids: set[str] | None = None,
) -> list[dict]:
    """Return list of attestations for advancing subject_did to level.

    Each attestation dict contains:
        attestor_did: str       — who attested
        is_council_lv6: bool    — whether attestor is Council Lv6+
        attestation_at: str     — ISO 8601 timestamp
        attestation_uri: str    — AT URI of the attestation record
        evidence_cid: str | None — IPFS CID if attached

    Filtered to attestations within ``since_days`` of now.

    Built on top of mst.query() of ai.gftd.apps.etzhayyim.charter-attestation.

    Council Lv6 membership is resolved against caller-provided council_dids set,
    or falls back to static COUNCIL_LV6_DIDS (bootstrap roster only, offline use).

    For live Council membership: call get_council_lv6_dids() to fetch current
    app.etzhayyim.council.member records, then pass the result as council_dids.

    Args:
        subject_did:  DID of the adherent whose advancement is being attested.
        level:        Proposed advancement level (1-7).
        since_days:   Only include attestations created within this many days
                      of the current UTC time.  Defaults to 365 (ADR §2).
        council_dids: Optional set of Council Lv6+ DIDs. If None, falls back to
                      static COUNCIL_LV6_DIDS (bootstrap, offline-friendly).
                      Pass get_council_lv6_dids() result for live data.

    Returns:
        List of attestation dicts, each with the keys described above.

    Raises:
        PdsAuthError, PdsNotFoundError, PdsServerError, PdsNetworkError.

    ADR-2605215400 §2 Witness Recency Policy:
        attestations must be within WITNESS_RECENCY_DAYS of the advancement
        event's effective timestamp.
    ADR-2605215400 §3.4 Council Registry:
        Council Lv6+ DIDs resolved from live app.etzhayyim.council.member
        records via get_council_lv6_dids(). Static COUNCIL_LV6_DIDS is used
        only if council_dids is None (fallback for offline/test).
    ADR-2605192300 § Bootstrap Council 5:
        Static COUNCIL_LV6_DIDS contains Founder seat 1 only. Seats 2-5
        are added to app.etzhayyim.council.member after RFP closes (2026-06-19).
    """
    cutoff_dt = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        days=since_days
    )

    # Resolve effective Council DID set: prefer caller-provided, fall back to static.
    effective_council_dids: set[str] = council_dids if council_dids is not None else COUNCIL_LV6_DIDS

    # Query ai.gftd.apps.etzhayyim.charter-attestation for records matching
    # this subject + level.  Client-side filtering is used at M2/M3; a
    # server-side index query is deferred to a later milestone when the
    # mst-projector (50-infra/mst-projector/) is in production.
    raw_records = await query(
        "ai.gftd.apps.etzhayyim.charter-attestation",
        filter={
            "subjectDid": subject_did,
            "proposedLevel": level,
        },
    )

    attestations: list[dict] = []
    for rec in raw_records:
        value: dict[str, Any] = rec.get("value", {})
        attestation_at_str: str = value.get("attestationAt", "")

        # Recency filter: skip attestations older than since_days.
        if attestation_at_str:
            try:
                attestation_dt = datetime.datetime.fromisoformat(
                    attestation_at_str.replace("Z", "+00:00")
                )
                if attestation_dt < cutoff_dt:
                    continue
            except ValueError:
                # Malformed timestamp — skip defensively.
                continue

        attestor_did: str = value.get("attestorDid", "")
        attestations.append(
            {
                "attestor_did": attestor_did,
                # Council Lv6 status resolved against effective_council_dids.
                # Live: caller passes get_council_lv6_dids() result.
                # Offline: falls back to static COUNCIL_LV6_DIDS (Founder seat 1).
                "is_council_lv6": attestor_did in effective_council_dids,
                "attestation_at": attestation_at_str,
                "attestation_uri": rec.get("uri", ""),
                "evidence_cid": value.get("evidenceCid"),
            }
        )

    return attestations


async def council_attestation_count(
    *,
    subject_did: str,
    level: int,
) -> int:
    """Count Council attestations for a proposed level advancement.

    Backward-compatible wrapper around :func:`council_attestation_details`.
    Returns ``len(await council_attestation_details(subject_did, level))``.

    Used by existing callers that only need a count.  New code should call
    :func:`council_attestation_details` directly to access recency and Council
    membership fields (required for Lv6/Lv7 logic per ADR-2605215400 §3).

    ADR-2605215200 §1 EvolutionValidationCell:
      council_approvals = await mst.council_attestation_count(
          subject_did=claim.adherent_did, level=claim.proposed_level
      )
      return council_approvals >= EVOLUTION_WITNESS_MIN
    """
    details = await council_attestation_details(subject_did, level)
    return len(details)


async def council_objections(
    claim_id: str,
    *,
    since_days: int = 30,
) -> list[dict]:
    """Return list of objections filed against a claim within the appeal window.

    Each objection dict contains:
        objector_did: str       — who filed the objection
        filed_at: str           — ISO 8601 timestamp
        reason: str             — objection reason/grounds
        evidence_cid: str | None — IPFS CID of attached evidence (if any)

    Filtered to objections within ``since_days`` of now (default 30 for appeal window).

    Built on top of mst.query() of app.etzhayyim.evolution-objection.

    Args:
        claim_id:    ID of the evolution claim being objected to.
        since_days:  Only include objections filed within this many days of now.
                     Defaults to 30 (ADR-2605215400 §4 appeal window).

    Returns:
        List of objection dicts, each with objector_did, filed_at, reason, evidence_cid.

    Raises:
        PdsAuthError, PdsNotFoundError, PdsServerError, PdsNetworkError.

    ADR-2605215400 §4 Appeal Window:
        Lv7 advancement is subject to 30-day public objection period. If objections
        are filed, evolution validation is marked as pending until window closes.
    """
    cutoff_dt = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
        days=since_days
    )

    raw_records = await query(
        "app.etzhayyim.evolution-objection",
        filter={"claimId": claim_id},
    )

    objections: list[dict] = []
    for rec in raw_records:
        value: dict[str, Any] = rec.get("value", {})
        filed_at_str: str = value.get("filedAt", "")

        # Recency filter: skip objections older than since_days.
        if filed_at_str:
            try:
                filed_dt = datetime.datetime.fromisoformat(
                    filed_at_str.replace("Z", "+00:00")
                )
                if filed_dt < cutoff_dt:
                    continue
            except ValueError:
                # Malformed timestamp — skip defensively.
                continue

        objector_did: str = value.get("objectorDid", "")
        objections.append(
            {
                "objector_did": objector_did,
                "filed_at": filed_at_str,
                "reason": value.get("reason", ""),
                "evidence_cid": value.get("evidenceCid"),
            }
        )

    return objections
