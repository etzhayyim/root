"""Tests for ADR-2605262400 W4 fetchers (czds / commoncrawl_cdx).

Network access is mocked via httpx.MockTransport. The per-TLD Council
attestation gate is exercised in both directions: approved record →
fetch succeeds; missing/revoked record → fetch fails-closed.
"""

from __future__ import annotations

import httpx
import pytest

from e7m_dataset.fetchers import commoncrawl_cdx, czds
from e7m_dataset.fetchers._acceptance import MissingAcceptanceFlag
from e7m_dataset.fetchers.czds import (
    CzdsTldNotAttested,
    MissingCzdsToken,
    StaticCouncilAttestation,
)


def _write_acceptance(tmp_path, source, *, accepted_at="2026-05-26T13:40:00Z"):
    acc_dir = tmp_path / "source-acceptance"
    acc_dir.mkdir(parents=True, exist_ok=True)
    (acc_dir / f"{source}.toml").write_text(
        "[acceptance]\n"
        f"source = \"{source}\"\n"
        f"accepted_at = \"{accepted_at}\"\n"
        f"accepted_by_did = \"did:web:etzhayyim.com:actor:test\"\n",
        encoding="utf-8",
    )
    return acc_dir


# ── CZDS ───────────────────────────────────────────────────────────────


def test_czds_fetch_succeeds_with_both_gates(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "czds-com")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )

    resolver = StaticCouncilAttestation(
        approved={
            "com": {
                "status": "approved",
                "tld": "com",
                "tier": "C",
                "expectedLicense": "czds-research-use",
                "councilSeatDids": [
                    "did:web:etzhayyim.com:actor:council-1",
                    "did:web:etzhayyim.com:actor:council-2",
                    "did:web:etzhayyim.com:actor:council-3",
                    "did:web:etzhayyim.com:actor:council-4",
                ],
                "decidedAt": "2026-05-25T00:00:00Z",
            }
        }
    )

    body = b"ZONE_FILE_BYTES"

    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        captured["auth"] = req.headers.get("Authorization", "")
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = czds.fetch(
            tmp_path / "stage",
            czds.CzdsFetchOpts(
                tld="com",
                base_url="https://mock/czds",
                bearer_token="DUMMY_TOKEN",
                client=client,
                attestation_resolver=resolver,
            ),
        )

    assert "/czds/downloads/com.zone" in captured["url"]
    assert captured["auth"] == "Bearer DUMMY_TOKEN"
    assert result.source["tier"] == "C"
    assert result.source["g13FleetInternalOnly"] is True
    assert result.source["councilAttestation"]["councilSeatDids"] != []
    assert result.source["acceptance"]["source"] == "czds-com"


def test_czds_fails_without_acceptance(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    resolver = StaticCouncilAttestation(
        approved={"com": {"status": "approved", "tld": "com", "tier": "C"}}
    )
    with pytest.raises(MissingAcceptanceFlag):
        czds.fetch(
            tmp_path / "stage",
            czds.CzdsFetchOpts(
                tld="com",
                bearer_token="x",
                attestation_resolver=resolver,
            ),
        )


def test_czds_fails_without_council_attestation(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "czds-com")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    resolver = StaticCouncilAttestation(approved={})  # no record at all
    with pytest.raises(CzdsTldNotAttested):
        czds.fetch(
            tmp_path / "stage",
            czds.CzdsFetchOpts(
                tld="com",
                bearer_token="x",
                attestation_resolver=resolver,
            ),
        )


def test_czds_fails_when_record_is_revoked(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "czds-com")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    resolver = StaticCouncilAttestation(
        approved={
            "com": {
                "status": "revoked",
                "tld": "com",
                "tier": "C",
            }
        }
    )
    with pytest.raises(CzdsTldNotAttested):
        czds.fetch(
            tmp_path / "stage",
            czds.CzdsFetchOpts(
                tld="com",
                bearer_token="x",
                attestation_resolver=resolver,
            ),
        )


def test_czds_fails_when_no_resolver_supplied(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "czds-com")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    with pytest.raises(CzdsTldNotAttested):
        czds.fetch(
            tmp_path / "stage",
            czds.CzdsFetchOpts(tld="com", bearer_token="x"),
        )


def test_czds_fails_when_token_missing(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "czds-com")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    monkeypatch.delenv("CZDS_BEARER_TOKEN", raising=False)
    resolver = StaticCouncilAttestation(
        approved={"com": {"status": "approved", "tld": "com", "tier": "C"}}
    )
    with pytest.raises(MissingCzdsToken):
        czds.fetch(
            tmp_path / "stage",
            czds.CzdsFetchOpts(
                tld="com",
                attestation_resolver=resolver,
            ),
        )


def test_czds_rejects_empty_tld(tmp_path):
    resolver = StaticCouncilAttestation(approved={})
    with pytest.raises(ValueError):
        czds.fetch(
            tmp_path / "stage",
            czds.CzdsFetchOpts(
                tld="",
                bearer_token="x",
                attestation_resolver=resolver,
            ),
        )


# ── Common Crawl CDX ───────────────────────────────────────────────────


def test_commoncrawl_cdx_fetch_with_acceptance(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "commoncrawl")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )

    body = b"CDX_INDEX_BYTES"

    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = commoncrawl_cdx.fetch(
            tmp_path / "stage",
            commoncrawl_cdx.CommonCrawlCdxFetchOpts(
                crawl_id="CC-MAIN-2026-22",
                archive_path="cc-index/collections/CC-MAIN-2026-22/indexes/cdx-00000.gz",
                base_url="https://mock/cc",
                client=client,
            ),
        )

    assert (
        "/cc-index/collections/CC-MAIN-2026-22/indexes/cdx-00000.gz"
        in captured["url"]
    )
    assert result.source["tier"] == "C"
    assert result.source["license"] == "commoncrawl-research-use"
    assert result.source["g13FleetInternalOnly"] is True
    assert result.source["piiSensitiveDefault"] is True
    assert result.source["crawlId"] == "CC-MAIN-2026-22"


def test_commoncrawl_cdx_fails_without_acceptance(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    with pytest.raises(MissingAcceptanceFlag):
        commoncrawl_cdx.fetch(
            tmp_path / "stage",
            commoncrawl_cdx.CommonCrawlCdxFetchOpts(
                crawl_id="CC-MAIN-2026-22",
                archive_path="cc-index/x.gz",
            ),
        )


def test_commoncrawl_cdx_rejects_empty_crawl_id(tmp_path):
    with pytest.raises(ValueError):
        commoncrawl_cdx.fetch(
            tmp_path / "stage",
            commoncrawl_cdx.CommonCrawlCdxFetchOpts(
                crawl_id="",
                archive_path="x.gz",
            ),
        )


def test_commoncrawl_cdx_rejects_empty_archive_path(tmp_path):
    with pytest.raises(ValueError):
        commoncrawl_cdx.fetch(
            tmp_path / "stage",
            commoncrawl_cdx.CommonCrawlCdxFetchOpts(
                crawl_id="CC-MAIN-2026-22",
                archive_path="",
            ),
        )
