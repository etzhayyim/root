"""Tests for ADR-2605262400 W2 fetchers (ripe_ris / routeviews).

Network access is mocked via httpx.MockTransport — no live BGP feed
contact (per ADR-2605262400 §7 passive-only invariant) and no upstream
hits.
"""

from __future__ import annotations

import gzip
import io

import httpx
import pytest

from e7m_dataset.fetchers import ripe_ris, routeviews


# ── RIPE RIS ───────────────────────────────────────────────────────────


def test_ripe_ris_fetch_writes_mrt(tmp_path):
    body = gzip.compress(b"MRT_RIB_PLACEHOLDER")

    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = ripe_ris.fetch(
            tmp_path,
            ripe_ris.RipeRisFetchOpts(
                collector="rrc00",
                year=2026,
                month=5,
                day=26,
                hour=8,
                minute=0,
                base_url="https://mock/ris",
                client=client,
            ),
        )

    assert "rrc00/2026.05/bview.20260526.0800.gz" in captured["url"]
    assert result.name.startswith("ris-mrt:rrc00:20260526T0800Z")
    assert result.staging_path.exists()
    mrt_files = list(result.staging_path.glob("*.gz"))
    assert len(mrt_files) == 1
    assert mrt_files[0].read_bytes() == body
    assert result.source["tier"] == "A"
    assert result.source["license"] == "ripe-tou-open"
    assert result.source["collector"] == "rrc00"


def test_ripe_ris_rejects_unknown_collector(tmp_path):
    with pytest.raises(ValueError):
        ripe_ris.fetch(
            tmp_path,
            ripe_ris.RipeRisFetchOpts(collector="rrc99"),
        )


# ── Routeviews ─────────────────────────────────────────────────────────


def test_routeviews_fetch_writes_mrt(tmp_path):
    # Routeviews bzip2 is opaque to the fetcher; we just stage bytes.
    body = b"MRT_RIB_BZ2_PLACEHOLDER"

    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = routeviews.fetch(
            tmp_path,
            routeviews.RouteviewsFetchOpts(
                collector="route-views.wide",
                year=2026,
                month=5,
                day=26,
                hour=10,
                minute=0,
                base_url="http://mock/rv",
                client=client,
            ),
        )

    assert "/route-views.wide/bgpdata/2026.05/RIBS/rib.20260526.1000.bz2" in captured["url"]
    assert result.name.startswith("routeviews:route-views.wide:20260526T1000Z")
    assert result.staging_path.exists()
    mrt_files = list(result.staging_path.glob("*.bz2"))
    assert len(mrt_files) == 1
    assert mrt_files[0].read_bytes() == body
    assert result.source["tier"] == "A"
    assert result.source["license"] == "uo-tou-open"
    assert result.source["collector"] == "route-views.wide"


def test_routeviews_default_collector_no_subpath(tmp_path):
    """Empty collector string → route-views2 (no /<collector>/ subpath)."""
    body = b"_"

    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        return httpx.Response(200, content=body)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = routeviews.fetch(
            tmp_path,
            routeviews.RouteviewsFetchOpts(
                collector="",
                year=2026,
                month=5,
                day=26,
                hour=12,
                base_url="http://mock/rv",
                client=client,
            ),
        )

    # No collector subpath in the URL.
    assert "/bgpdata/2026.05/RIBS/rib.20260526.1200.bz2" in captured["url"]
    assert "/route-views" not in captured["url"].rsplit("/bgpdata/", 1)[0]
    assert result.source["collector"] == "route-views2"


def test_routeviews_rejects_unknown_collector(tmp_path):
    with pytest.raises(ValueError):
        routeviews.fetch(
            tmp_path,
            routeviews.RouteviewsFetchOpts(collector="route-views.invalid"),
        )
