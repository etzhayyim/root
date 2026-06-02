"""ICANN CZDS per-TLD zone-file fetcher.

Per ADR-2605262400 W4. ICANN's Centralized Zone Data Service distributes
per-TLD zone files under per-TLD registration agreements. Each TLD's
admissibility differs — many are research-use (Tier C) but some carry
redistribution restrictions that map to Tier D.

Wave-4 admits a TLD only when **both** gates are satisfied:

  1. **Per-TLD operator acceptance flag** at
     ``~/.etzhayyim/source-acceptance/czds-<tld>.toml`` (mirrors the
     ADR-2605262400 W3 acceptance gate pattern).
  2. **Per-TLD Council attestation Lexicon record** at
     ``com.etzhayyim.substrate.tldCouncilAttestation`` with
     ``status = 'approved'`` and ``tld == <tld>``.

The Lexicon resolution is parameterized via the
``CzdsTldAttestationResolver`` Protocol so production code can hit the
PDS while tests pass a stub. Wave-4 ships a ``StaticCouncilAttestation``
helper for both unit-tests and the bootstrap operator dry-runs.

License/TOS: per-TLD CZDS Service Provider Agreement. Tier C / D
depending on TLD. NEVER publishable without explicit per-TLD license
review.

PII-sensitivity: variable per TLD. SOA RNAME records embed registry
operator contact strings; some legacy TLDs include direct registrant
emails. PII filter applied at sensor layer (downstream).
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol

import httpx

from . import FetchResult
from ._acceptance import require_acceptance


_DEFAULT_BASE = "https://czds-api.icann.org"


class CzdsTldAttestationResolver(Protocol):
    """Resolves the per-TLD ``com.etzhayyim.substrate.tldCouncilAttestation``
    Lexicon record."""

    def latest_approved(self, tld: str) -> dict | None:  # pragma: no cover
        ...


class CzdsTldNotAttested(RuntimeError):
    """Raised when no Council attestation record permits the given TLD."""


@dataclass
class StaticCouncilAttestation:
    """In-memory attestation resolver for tests + bootstrap operator runs.

    Production callers replace this with a PDS-backed resolver that
    queries the dataset-pinner repo and verifies signatures.
    """

    approved: dict[str, dict] = field(default_factory=dict)

    def latest_approved(self, tld: str) -> dict | None:
        rec = self.approved.get(tld)
        if rec is None:
            return None
        if rec.get("status") != "approved":
            return None
        return rec


@dataclass
class CzdsFetchOpts:
    tld: str = ""
    base_url: str = _DEFAULT_BASE
    # CZDS API requires an OAuth-style Bearer token per
    # https://github.com/icann/czds-api-client-python — operator obtains
    # it out-of-band and passes via opts or CZDS_BEARER_TOKEN env var.
    bearer_token: Optional[str] = None
    timeout_sec: float = 1800.0
    client: Optional[httpx.Client] = None
    attestation_resolver: Optional[CzdsTldAttestationResolver] = None


class MissingCzdsToken(RuntimeError):
    """Raised when no CZDS Bearer token is available."""


def _resolve_token(opts: CzdsFetchOpts) -> str:
    import os
    tok = opts.bearer_token or os.environ.get("CZDS_BEARER_TOKEN", "")
    if not tok:
        raise MissingCzdsToken(
            "No CZDS Bearer token. Set CZDS_BEARER_TOKEN in the env or "
            "pass bearer_token= to CzdsFetchOpts."
        )
    return tok


def fetch(staging_dir: Path, opts: CzdsFetchOpts) -> FetchResult:
    if not opts.tld:
        raise ValueError("CzdsFetchOpts.tld is required.")
    tld = opts.tld.lower().lstrip(".")
    acceptance_source = f"czds-{tld}"

    # Gate 1: per-TLD operator acceptance flag.
    acceptance = require_acceptance(acceptance_source)

    # Gate 2: per-TLD Council attestation Lexicon record.
    resolver = opts.attestation_resolver
    if resolver is None:
        raise CzdsTldNotAttested(
            f"No CzdsTldAttestationResolver supplied. Per ADR-2605262400 W4 "
            f"the per-TLD Council attestation record at "
            f"com.etzhayyim.substrate.tldCouncilAttestation MUST be "
            f"resolved before any CZDS fetch."
        )
    record = resolver.latest_approved(tld)
    if record is None:
        raise CzdsTldNotAttested(
            f"No approved com.etzhayyim.substrate.tldCouncilAttestation "
            f"record for TLD '{tld}'. Per ADR-2605262400 W4, the Council "
            f"MUST vote (Lv6+ ≥4/7) before any CZDS fetch on this TLD."
        )

    token = _resolve_token(opts)
    url = f"{opts.base_url}/czds/downloads/{tld}.zone"
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"czds-{tld}-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    zone_path = out_dir / f"{tld}.zone"
    headers = {"Authorization": f"Bearer {token}"}

    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True
    )
    try:
        with client.stream("GET", url, headers=headers) as resp:
            resp.raise_for_status()
            with zone_path.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    raw_sha = hashlib.sha256(zone_path.read_bytes()).hexdigest()
    revision = f"sha256:{raw_sha}"

    size_bytes = sum(
        p.stat().st_size for p in out_dir.rglob("*") if p.is_file()
    )
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    declared_tier = str(record.get("tier", "C")).upper()
    if declared_tier not in {"C", "D"}:
        declared_tier = "C"

    return FetchResult(
        name=f"czds:{tld}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "tld": tld,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "license": record.get("expectedLicense", "czds-per-tld"),
            "tier": declared_tier,
            "g13FleetInternalOnly": True,
            "piiSensitiveDefault": True,
            "councilAttestation": {
                "councilSeatDids": record.get("councilSeatDids", []),
                "decidedAt": record.get("decidedAt", ""),
                "expectedLicense": record.get("expectedLicense", ""),
                "expiresAt": record.get("expiresAt", ""),
            },
            "acceptance": {
                "source": acceptance.source,
                "acceptedAt": acceptance.accepted_at,
                "acceptedByDid": acceptance.accepted_by_did,
                "upstreamTosUrl": acceptance.upstream_tos_url,
            },
        },
    )


__all__ = [
    "CzdsFetchOpts",
    "CzdsTldAttestationResolver",
    "CzdsTldNotAttested",
    "MissingCzdsToken",
    "StaticCouncilAttestation",
    "fetch",
]
