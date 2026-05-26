"""Tests for ADR-2605262400 W1 fetchers (rir_delegated / iana_root / maxmind).

Network access is mocked via httpx.MockTransport — no live DNS resolution
(per ADR-2605262400 §7 passive-only invariant) and no upstream hits.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import httpx
import pytest

from e7m_dataset.fetchers import iana_root, maxmind_geolite, rir_delegated


# ── RIR delegated ──────────────────────────────────────────────────────


_SAMPLE_RIR_BODY = """\
2|apnic|20260526|3|19850701|20260526|+1000
apnic|*|asn|*|7|summary
apnic|*|ipv4|*|56789|summary
apnic|*|ipv6|*|9876|summary
apnic|JP|ipv4|1.0.0.0|256|20100101|allocated|A91A0001
apnic|KR|ipv4|1.0.1.0|256|20110101|allocated|A91A0002
apnic|TH|asn|24037|1|20070101|assigned|A91A0050
# comment line ignored
"""


def test_rir_delegated_fetch_writes_raw_and_ndjson(tmp_path):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_SAMPLE_RIR_BODY.encode("utf-8"))

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = rir_delegated.fetch(
            tmp_path,
            rir_delegated.RirDelegatedFetchOpts(
                rir="apnic",
                base_url="https://mock/delegated",
                client=client,
            ),
        )

    assert result.name == "rir-delegated:apnic"
    assert result.staging_path.exists()
    assert (result.staging_path / "delegated-apnic-extended-latest.txt").exists()
    ndjson_path = result.staging_path / "delegated-apnic-extended-latest.ndjson"
    assert ndjson_path.exists()
    rows = [json.loads(l) for l in ndjson_path.read_text().splitlines() if l]
    assert len(rows) == 3
    assert rows[0]["cc"] == "JP"
    assert rows[0]["type"] == "ipv4"
    assert rows[0]["opaqueId"] == "A91A0001"
    assert rows[2]["type"] == "asn"
    assert result.source["tier"] == "A"
    assert result.source["license"] == "public-domain-defacto"


def test_rir_delegated_rejects_unknown_rir(tmp_path):
    with pytest.raises(ValueError):
        rir_delegated.fetch(
            tmp_path,
            rir_delegated.RirDelegatedFetchOpts(rir="bogus"),
        )


def test_rir_delegated_iter_ndjson(tmp_path):
    ndjson_path = tmp_path / "x.ndjson"
    ndjson_path.write_text('{"a": 1}\n\n{"b": 2}\nnotjson\n', encoding="utf-8")
    rows = list(rir_delegated.iter_ndjson_rows(ndjson_path))
    assert rows == [{"a": 1}, {"b": 2}]


# ── IANA root zone ─────────────────────────────────────────────────────


_SAMPLE_ROOT_ZONE = """\
.                       86400   IN      SOA     a.root-servers.net. nstld.verisign-grs.com. 2026052600 1800 900 604800 86400
.                       86400   IN      NS      a.root-servers.net.
example.                86400   IN      NS      a.iana-servers.net.
example.                86400   IN      NS      b.iana-servers.net.
example.                86400   IN      DS      370 13 2 BE74359954660069D5C63D200C39F5603827D7DD02B56F120EE9F3A86764247C
test.                   86400   IN      NS      ns.test.
ns.test.                86400   IN      A       192.0.2.1
ns.test.                86400   IN      AAAA    2001:db8::1
"""


def test_iana_root_fetch_writes_zone_and_ndjson(tmp_path):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=_SAMPLE_ROOT_ZONE.encode("utf-8"))

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = iana_root.fetch(
            tmp_path,
            iana_root.IanaRootFetchOpts(
                base_url="https://mock/root.zone",
                client=client,
            ),
        )

    assert result.name == "iana-root"
    assert (result.staging_path / "root.zone").exists()
    ndjson_path = result.staging_path / "root.zone.ndjson"
    rows = [json.loads(l) for l in ndjson_path.read_text().splitlines() if l]
    tlds = {r["tld"] for r in rows}
    assert tlds == {"example", "test"}
    by_tld = {r["tld"]: r for r in rows}
    assert len(by_tld["example"]["ns"]) == 2
    assert len(by_tld["example"]["ds"]) == 1
    assert len(by_tld["test"]["glue"]) == 2
    assert result.source["tier"] == "A"
    assert result.source["license"] == "public-domain"
    assert result.source["tldCount"] == 2


# ── MaxMind GeoLite2 ───────────────────────────────────────────────────


def _build_geolite_tarball(edition: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        mmdb_bytes = b"\x00" * 128
        info = tarfile.TarInfo(name=f"{edition}_20260526/{edition}.mmdb")
        info.size = len(mmdb_bytes)
        tar.addfile(info, io.BytesIO(mmdb_bytes))
        cr = b"CC-BY-SA-4.0 (c) MaxMind"
        cr_info = tarfile.TarInfo(name=f"{edition}_20260526/COPYRIGHT.txt")
        cr_info.size = len(cr)
        tar.addfile(cr_info, io.BytesIO(cr))
    return buf.getvalue()


def test_maxmind_fetch_extracts_mmdb_and_propagates_sa(tmp_path):
    body = _build_geolite_tarball("GeoLite2-Country")

    def handler(req: httpx.Request) -> httpx.Response:
        assert "license_key" in str(req.url)
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = maxmind_geolite.fetch(
            tmp_path,
            maxmind_geolite.MaxmindGeoliteFetchOpts(
                edition="GeoLite2-Country",
                license_key="DUMMY_KEY",
                base_url="https://mock/geoip_download",
                client=client,
            ),
        )

    assert result.name == "geolite2:geolite2-country"
    assert (result.staging_path / "GeoLite2-Country.tar.gz").exists()
    mmdb_files = list(result.staging_path.rglob("*.mmdb"))
    assert len(mmdb_files) == 1
    assert result.source["license"] == "CC-BY-SA-4.0"
    assert result.source["saPropagates"] is True
    assert result.source["tier"] == "A"


def test_maxmind_rejects_missing_key(tmp_path, monkeypatch):
    monkeypatch.delenv("MAXMIND_LICENSE_KEY", raising=False)
    with pytest.raises(maxmind_geolite.MissingMaxmindKey):
        maxmind_geolite.fetch(
            tmp_path,
            maxmind_geolite.MaxmindGeoliteFetchOpts(edition="GeoLite2-Country"),
        )


def test_maxmind_rejects_unknown_edition(tmp_path):
    with pytest.raises(ValueError):
        maxmind_geolite.fetch(
            tmp_path,
            maxmind_geolite.MaxmindGeoliteFetchOpts(
                edition="GeoLite2-Bogus",
                license_key="DUMMY_KEY",
            ),
        )
