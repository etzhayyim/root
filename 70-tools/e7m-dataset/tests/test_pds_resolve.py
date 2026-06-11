"""Tests for e7m_dataset.pds.parse_at_uri + resolve_datasetpin.

Validates the W2 PDS resolver: at-uri parsing, collection-mismatch
rejection, mock HTTP roundtrip for `com.atproto.repo.getRecord`,
and error paths (404 / missing cid / bad shape).
"""

from __future__ import annotations

import httpx
import pytest

from e7m_dataset import pds


# ─── parse_at_uri ───────────────────────────────────────────────────


def test_parse_at_uri_canonical():
    repo, collection, rkey = pds.parse_at_uri(
        "at://did:web:dataset-pinner.etzhayyim.com/com.etzhayyim.substrate.datasetPin/3kpqab"
    )
    assert repo == "did:web:dataset-pinner.etzhayyim.com"
    assert collection == "com.etzhayyim.substrate.datasetPin"
    assert rkey == "3kpqab"


def test_parse_at_uri_with_handle():
    repo, collection, rkey = pds.parse_at_uri(
        "at://etzhayyim.com/com.etzhayyim.substrate.datasetPin/abc123"
    )
    assert repo == "etzhayyim.com"
    assert collection == "com.etzhayyim.substrate.datasetPin"
    assert rkey == "abc123"


def test_parse_at_uri_rejects_bad_shape():
    for bad in [
        "https://example.com/x/y/z",
        "at://only-one-segment",
        "at://repo/collection",   # missing rkey
        "not-an-at-uri",
        "",
    ]:
        with pytest.raises(pds.PdsError, match="bad at-uri shape"):
            pds.parse_at_uri(bad)


# ─── resolve_datasetpin (httpx MockTransport) ───────────────────────


def _at_uri(rkey: str) -> str:
    return f"at://did:web:dataset-pinner.etzhayyim.com/com.etzhayyim.substrate.datasetPin/{rkey}"


def test_resolve_datasetpin_happy_path():
    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        captured["params"] = dict(req.url.params)
        return httpx.Response(
            200,
            json={
                "uri": _at_uri("rkey001"),
                "cid": "bafyrecordcid001",
                "value": {
                    "cid": "bafyactualpinmapcid001",
                    "name": "test-subdataset",
                    "revision": "sha256:abc",
                },
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        rec = pds.resolve_datasetpin(_at_uri("rkey001"), client=client)
    assert rec["cid"] == "bafyactualpinmapcid001"
    assert captured["params"]["collection"] == "com.etzhayyim.substrate.datasetPin"
    assert captured["params"]["rkey"] == "rkey001"
    assert "com.atproto.repo.getRecord" in captured["url"]


def test_resolve_datasetpin_rejects_404():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "RecordNotFound"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(pds.PdsError, match="getRecord failed: 404"):
            pds.resolve_datasetpin(_at_uri("missing"), client=client)


def test_resolve_datasetpin_rejects_record_without_cid():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"value": {"name": "no-cid-here"}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(pds.PdsError, match="missing required `cid`"):
            pds.resolve_datasetpin(_at_uri("nocid"), client=client)


def test_resolve_datasetpin_rejects_wrong_collection():
    # collection is wrong → fails BEFORE any HTTP call.
    bad_uri = "at://did:web:x/app.bsky.feed.post/abc"
    with pytest.raises(pds.PdsError, match="expected collection="):
        pds.resolve_datasetpin(bad_uri)


def test_resolve_datasetpin_propagates_500():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="upstream PDS gateway timeout")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(pds.PdsError, match="getRecord failed: 500"):
            pds.resolve_datasetpin(_at_uri("err"), client=client)
