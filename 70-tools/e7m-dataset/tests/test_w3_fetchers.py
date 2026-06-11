"""Tests for ADR-2605262400 W3 Tier-C fetchers + acceptance-flag gate.

Network access is mocked via httpx.MockTransport. The acceptance flag
gate is exercised in both directions: a happy path with a TOML file
present, and a fail-closed path with no file.
"""

from __future__ import annotations

import httpx
import pytest

from e7m_dataset.fetchers import caida, openintel, rapid7_sonar
from e7m_dataset.fetchers._acceptance import (
    MissingAcceptanceFlag,
    require_acceptance,
)


# ── Acceptance flag gate ───────────────────────────────────────────────


def _write_acceptance(tmp_path, source, *, accepted_at="2026-05-26T13:40:00Z"):
    acc_dir = tmp_path / "source-acceptance"
    acc_dir.mkdir(parents=True, exist_ok=True)
    (acc_dir / f"{source}.toml").write_text(
        "[acceptance]\n"
        f"source = \"{source}\"\n"
        f"accepted_at = \"{accepted_at}\"\n"
        f"accepted_by_did = \"did:web:etzhayyim.com:actor:test\"\n"
        f"upstream_tos_url = \"https://example.test/tos\"\n",
        encoding="utf-8",
    )
    return acc_dir


def test_require_acceptance_happy_path(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "rapid7-open-data")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    acc = require_acceptance("rapid7-open-data")
    assert acc.source == "rapid7-open-data"
    assert acc.accepted_at == "2026-05-26T13:40:00Z"
    assert acc.accepted_by_did == "did:web:etzhayyim.com:actor:test"


def test_require_acceptance_missing_file_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    with pytest.raises(MissingAcceptanceFlag):
        require_acceptance("rapid7-open-data")


def test_require_acceptance_missing_accepted_at_fails_closed(tmp_path, monkeypatch):
    acc_dir = tmp_path / "source-acceptance"
    acc_dir.mkdir(parents=True)
    (acc_dir / "rapid7-open-data.toml").write_text(
        "[acceptance]\nsource = \"rapid7-open-data\"\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ETZ_SOURCE_ACCEPTANCE_DIR", str(acc_dir))
    with pytest.raises(MissingAcceptanceFlag):
        require_acceptance("rapid7-open-data")


# ── Rapid7 Sonar ───────────────────────────────────────────────────────


def test_rapid7_sonar_fetch_with_acceptance(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "rapid7-open-data")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )

    body = b"FDNS_SHARD_BYTES_PLACEHOLDER"

    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = rapid7_sonar.fetch(
            tmp_path / "stage",
            rapid7_sonar.Rapid7SonarFetchOpts(
                archive_file="2026-05-23-fdns_any.json.gz",
                base_url="https://mock/sonar",
                client=client,
            ),
        )

    assert "2026-05-23-fdns_any.json.gz" in captured["url"]
    assert result.source["tier"] == "C"
    assert result.source["g13FleetInternalOnly"] is True
    assert result.source["piiSensitiveDefault"] is True
    assert result.source["acceptance"]["source"] == "rapid7-open-data"


def test_rapid7_sonar_fails_without_acceptance(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    with pytest.raises(MissingAcceptanceFlag):
        rapid7_sonar.fetch(
            tmp_path / "stage",
            rapid7_sonar.Rapid7SonarFetchOpts(
                archive_file="2026-05-23-fdns_any.json.gz",
            ),
        )


def test_rapid7_sonar_rejects_empty_archive_file(tmp_path):
    with pytest.raises(ValueError):
        rapid7_sonar.fetch(
            tmp_path / "stage",
            rapid7_sonar.Rapid7SonarFetchOpts(archive_file=""),
        )


# ── OpenINTEL ──────────────────────────────────────────────────────────


def test_openintel_fetch_with_acceptance(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "openintel")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )

    body = b"PARQUET_BYTES"

    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = openintel.fetch(
            tmp_path / "stage",
            openintel.OpenIntelFetchOpts(
                zone="tranco1m",
                year=2026,
                month=5,
                day=26,
                archive_file="tranco1m-20260526.parquet",
                base_url="https://mock/openintel",
                client=client,
            ),
        )

    assert "/tranco1m/2026/05/26/tranco1m-20260526.parquet" in captured["url"]
    assert result.source["tier"] == "C"
    assert result.source["license"] == "CC-BY-NC-4.0"
    assert result.source["g13FleetInternalOnly"] is True


def test_openintel_fails_without_acceptance(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    with pytest.raises(MissingAcceptanceFlag):
        openintel.fetch(
            tmp_path / "stage",
            openintel.OpenIntelFetchOpts(
                archive_file="x.parquet",
            ),
        )


# ── CAIDA ──────────────────────────────────────────────────────────────


def test_caida_fetch_with_acceptance(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "caida")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )

    body = b"AS_REL_BYTES"

    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = caida.fetch(
            tmp_path / "stage",
            caida.CaidaFetchOpts(
                dataset="as-relationship",
                archive_path="as-relationships/serial-1/20260501.as-rel.txt.bz2",
                base_url="https://mock/caida",
                client=client,
            ),
        )

    assert "/as-relationships/serial-1/20260501.as-rel.txt.bz2" in captured["url"]
    assert result.source["tier"] == "C"
    assert result.source["license"] == "CC-BY-NC-4.0"
    assert result.source["g13FleetInternalOnly"] is True
    assert result.source["piiSensitiveDefault"] is False


def test_caida_rejects_unknown_dataset(tmp_path):
    with pytest.raises(ValueError):
        caida.fetch(
            tmp_path / "stage",
            caida.CaidaFetchOpts(
                dataset="bogus",
                archive_path="x.bz2",
            ),
        )


def test_caida_rejects_empty_archive_path(tmp_path, monkeypatch):
    _write_acceptance(tmp_path, "caida")
    monkeypatch.setenv(
        "ETZ_SOURCE_ACCEPTANCE_DIR",
        str(tmp_path / "source-acceptance"),
    )
    with pytest.raises(ValueError):
        caida.fetch(
            tmp_path / "stage",
            caida.CaidaFetchOpts(dataset="as-rank", archive_path=""),
        )
