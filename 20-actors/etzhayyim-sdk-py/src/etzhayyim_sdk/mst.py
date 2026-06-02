"""etzhayyim-sdk-py MST client — AT Protocol MST read/query helpers.

Provides `query()`, `council_attestation_details()`, and `council_objections()`
for religious-corp Pregel cells querying AT Protocol MST records.

Per ADR-2605172000: replaces all direct RisingWave/psycopg SQL reads with
MST-backed queries via the AT Protocol PDS + mst-projector.

Configuration:
  ETZHAYYIM_PDS_URL — base URL of the AT Protocol PDS
                      (default: http://atproto.etzhayyim.com)

Usage::

    from etzhayyim_sdk import mst

    records = await mst.query(
        "com.etzhayyim.apps.etzhayyim.shinka.evolutionEvent",
        did="did:plc:abc123",
        limit=10,
    )

    attestations = await mst.council_attestation_details(
        "did:plc:abc123",
        6,
        since_days=365,
    )
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from .errors import EtzhayyimSdkError


class MstError(EtzhayyimSdkError):
    """Base error for MST client failures."""


class MstNetworkError(MstError):
    """Raised when the HTTP request to the MST/PDS fails at the transport layer."""


class MstServerError(MstError):
    """Raised when the PDS/MST service returns HTTP 5xx."""


# ── Configuration ─────────────────────────────────────────────────────────────


def _pds_url() -> str:
    return os.environ.get("ETZHAYYIM_PDS_URL", "http://atproto.etzhayyim.com").rstrip("/")


# ── Singleton client ──────────────────────────────────────────────────────────

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


def _inject_client(client: httpx.AsyncClient) -> None:
    """Replace the singleton client. Used exclusively in tests."""
    global _client
    _client = client


# ── Public API ────────────────────────────────────────────────────────────────


async def query(
    collection: str,
    /,
    *,
    did: str = "",
    filter: dict[str, Any] | None = None,  # noqa: A002
    filter_did: str = "",
    since: str = "",
    limit: int = 50,
    sort: str = "desc",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Query records from an AT Protocol MST collection.

    This function unifies the various query patterns used by Pregel cells:
      - mst.query("collection", did=did, limit=1, sort="desc")
        → queries records authored by *did*
      - mst.query("collection", filter={"subjectDid": did})
        → queries records filtered by field value
      - mst.query("collection", filter_did=did, since=ts, limit=50)
        → queries records by DID with a since timestamp filter

    Until the full MST client is wired (M3), this is a stub that raises
    NotImplementedError. Tests mock this function directly.

    Args:
        collection: AT Protocol collection NSID.
        did:        DID of the repo to query (authoring DID).
        filter:     Dict of field→value filters (e.g. {"subjectDid": "did:..."}).
        filter_did: Alias for did (legacy parameter name).
        since:      ISO 8601 timestamp; only return records after this time.
        limit:      Maximum records to return (default 50).
        sort:       Sort order: "desc" (newest first) or "asc".
        **kwargs:   Additional parameters forwarded to the PDS query endpoint.

    Returns:
        List of record dicts, each with at least {uri, cid, value, recordedAt}.

    Raises:
        NotImplementedError: SDK not yet wired to live PDS (M3 target).
        MstNetworkError:     transport-level failure.
        MstServerError:      PDS returned HTTP 5xx.
        MstError:            PDS returned HTTP 4xx.
    """
    raise NotImplementedError(
        "mst.query: real PDS binding not yet wired (M3 target). "
        "In tests, mock this function with unittest.mock.AsyncMock. "
        "See 20-actors/etzhayyim-sdk-py/src/etzhayyim_sdk/mst.py."
    )


async def council_attestation_details(
    adherent_did: str,
    proposed_level: int,
    *,
    since_days: int = 365,
) -> list[dict[str, Any]]:
    """Query Council attestation details for an evolution claim.

    Returns attestation records for *adherent_did* at *proposed_level*,
    filtered to attestations within *since_days* (recency policy per
    ADR-2605215400 §2).

    Each record includes:
      - attestor_did (str): DID of the attesting council member
      - is_council_lv6 (bool): whether the attestor is a Council Lv6+ member
      - attestation_at (str): ISO 8601 timestamp of the attestation
      - attestation_uri (str): AT URI of the attestation record
      - evidence_cid (str): IPFS CID of the attestation evidence (may be empty)

    Until the full MST client is wired (M3), this is a stub that raises
    NotImplementedError. Tests mock this function directly.

    Args:
        adherent_did:   DID of the adherent seeking level advancement.
        proposed_level: The level being claimed (1–7).
        since_days:     Only count attestations within this many days.

    Returns:
        List of attestation dicts.

    Raises:
        NotImplementedError: SDK not yet wired to live PDS (M3 target).
        MstNetworkError:     transport-level failure.
        MstServerError:      PDS returned HTTP 5xx.
        MstError:            PDS returned HTTP 4xx.
    """
    raise NotImplementedError(
        "mst.council_attestation_details: real PDS binding not yet wired (M3 target). "
        "In tests, mock this function with unittest.mock.AsyncMock. "
        "See 20-actors/etzhayyim-sdk-py/src/etzhayyim_sdk/mst.py."
    )


async def council_objections(
    claim_id: str,
    *,
    since_days: int = 30,
) -> list[dict[str, Any]]:
    """Query Council objections filed against an evolution claim.

    Returns objection records for *claim_id* within *since_days*
    (appeal window per ADR-2605215400 §4).

    Each record includes:
      - objector_did (str): DID of the objecting council member
      - objection_at (str): ISO 8601 timestamp
      - objection_uri (str): AT URI of the objection record
      - reason (str): human-readable objection reason

    Until the full MST client is wired (M3), this is a stub that raises
    NotImplementedError. Tests mock this function directly.

    Args:
        claim_id:   The evolution claim ID being objected to.
        since_days: Only count objections within this many days.

    Returns:
        List of objection dicts.

    Raises:
        NotImplementedError: SDK not yet wired to live PDS (M3 target).
        MstNetworkError:     transport-level failure.
        MstServerError:      PDS returned HTTP 5xx.
        MstError:            PDS returned HTTP 4xx.
    """
    raise NotImplementedError(
        "mst.council_objections: real PDS binding not yet wired (M3 target). "
        "In tests, mock this function with unittest.mock.AsyncMock. "
        "See 20-actors/etzhayyim-sdk-py/src/etzhayyim_sdk/mst.py."
    )
