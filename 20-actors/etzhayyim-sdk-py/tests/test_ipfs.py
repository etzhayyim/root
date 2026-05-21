"""Tests for etzhayyim_sdk.ipfs — Kubo HTTP RPC real impl (M4).

All tests use httpx.MockTransport injected via ipfs._inject_transport() — no
real network calls are made.

Coverage:
  test_pin_happy             — 200 + CID confirmed in Pins
  test_pin_unconfirmed       — 200 but CID absent from Pins → IpfsServerError
  test_pin_500               — HTTP 500 → IpfsServerError
  test_pin_network_error     — ConnectError → IpfsNetworkError
  test_pin_many              — 3 CIDs → 3 POST calls, all confirmed
  test_unpin                 — 200 → None
  test_unpin_500             — HTTP 500 → IpfsServerError
  test_fetch                 — 200 → raw bytes returned
  test_fetch_network_error   — ConnectError → IpfsNetworkError
  test_add                   — multipart POST, returns CID from Hash field
  test_add_missing_hash      — 200 but no Hash → IpfsServerError
  test_add_500               — HTTP 500 → IpfsServerError
  test_pin_ls_all            — lists all pins as list[dict]
  test_pin_ls_filtered       — filtered by cid arg
  test_pin_ls_empty          — empty Keys → []
  test_subscribe_stub        — raises NotImplementedError mentioning M5

ADR-2605215200 §4 — M4 milestone IPFS impl.
ADR-2605171800 Stage 3 — Kubo HTTP API on simeon.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
_sdk_src = Path(__file__).resolve().parents[1] / "src"
if str(_sdk_src) not in sys.path:
    sys.path.insert(0, str(_sdk_src))


# ── Helpers ───────────────────────────────────────────────────────────────────


def _inject(handler):
    """Inject a MockTransport handler into the ipfs module singleton."""
    from etzhayyim_sdk import ipfs as ipfs_module

    transport = httpx.MockTransport(handler)
    ipfs_module._inject_transport(transport)


# ── pin ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pin_happy():
    """pin() calls POST /api/v0/pin/add and confirms the CID in Pins."""
    from etzhayyim_sdk import ipfs

    cid = "bafybeig5abc123"
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/v0/pin/add" in request.url.path
        assert request.url.params["arg"] == cid
        assert request.url.params["recursive"] == "true"
        calls.append("pin")
        return httpx.Response(200, json={"Pins": [cid], "Progress": ""})

    _inject(handler)
    result = await ipfs.pin(cid)
    assert result is None
    assert calls == ["pin"]


@pytest.mark.asyncio
async def test_pin_unconfirmed():
    """pin() raises IpfsServerError when CID is absent from Pins list."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsServerError

    cid = "bafybeig5abc123"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Pins": [], "Progress": ""})

    _inject(handler)
    with pytest.raises(IpfsServerError, match="did not confirm"):
        await ipfs.pin(cid)


@pytest.mark.asyncio
async def test_pin_500():
    """pin() raises IpfsServerError on HTTP 500."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsServerError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    _inject(handler)
    with pytest.raises(IpfsServerError) as exc_info:
        await ipfs.pin("bafybeig5abc123")
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_pin_network_error():
    """pin() raises IpfsNetworkError when the transport raises ConnectError."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsNetworkError

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    _inject(handler)
    with pytest.raises(IpfsNetworkError, match="network error pinning"):
        await ipfs.pin("bafybeig5abc123")


# ── pin_many ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pin_many():
    """pin_many() sends one POST per CID and succeeds for all 3."""
    from etzhayyim_sdk import ipfs

    cids = ["bafy001", "bafy002", "bafy003"]
    seen_args: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        arg = request.url.params["arg"]
        seen_args.append(arg)
        return httpx.Response(200, json={"Pins": [arg], "Progress": ""})

    _inject(handler)
    await ipfs.pin_many(cids)
    assert seen_args == cids


@pytest.mark.asyncio
async def test_pin_many_first_failure_aborts():
    """pin_many() stops at the first failing CID (first-failure semantics)."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsServerError

    cids = ["bafy001", "bafy002", "bafy003"]
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        arg = request.url.params["arg"]
        if arg == "bafy001":
            return httpx.Response(500, text="error")
        return httpx.Response(200, json={"Pins": [arg]})

    _inject(handler)
    with pytest.raises(IpfsServerError):
        await ipfs.pin_many(cids)
    # Only 1 call made (stopped after first failure)
    assert call_count == 1


# ── unpin ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unpin():
    """unpin() calls POST /api/v0/pin/rm and returns None on 200."""
    from etzhayyim_sdk import ipfs

    cid = "bafybeig5abc123"
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/v0/pin/rm" in request.url.path
        assert request.url.params["arg"] == cid
        calls.append("unpin")
        return httpx.Response(200, json={"Pins": [cid]})

    _inject(handler)
    result = await ipfs.unpin(cid)
    assert result is None
    assert calls == ["unpin"]


@pytest.mark.asyncio
async def test_unpin_500():
    """unpin() raises IpfsServerError on HTTP 500 (e.g. CID not pinned)."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsServerError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="not pinned or pinning")

    _inject(handler)
    with pytest.raises(IpfsServerError) as exc_info:
        await ipfs.unpin("bafybeig5abc123")
    assert exc_info.value.status_code == 500


# ── fetch ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch():
    """fetch() calls POST /api/v0/cat and returns raw bytes."""
    from etzhayyim_sdk import ipfs

    cid = "bafybeig5abc123"
    payload = b"hello ipfs content"

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/v0/cat" in request.url.path
        assert request.url.params["arg"] == cid
        return httpx.Response(200, content=payload)

    _inject(handler)
    data = await ipfs.fetch(cid)
    assert data == payload


@pytest.mark.asyncio
async def test_fetch_network_error():
    """fetch() raises IpfsNetworkError on transport failure."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsNetworkError

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("timeout")

    _inject(handler)
    with pytest.raises(IpfsNetworkError, match="network error fetching"):
        await ipfs.fetch("bafybeig5abc123")


@pytest.mark.asyncio
async def test_fetch_500():
    """fetch() raises IpfsServerError on HTTP 500."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsServerError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="no content found")

    _inject(handler)
    with pytest.raises(IpfsServerError) as exc_info:
        await ipfs.fetch("bafybeig5abc123")
    assert exc_info.value.status_code == 500


# ── add ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add():
    """add() posts multipart data and returns the CID from Hash field."""
    from etzhayyim_sdk import ipfs

    raw = b"the quick brown fox"
    expected_cid = "bafybeig5newcid456"

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/v0/add" in request.url.path
        # Verify multipart body contains the data
        assert b"the quick brown fox" in request.content
        # Verify pin param
        assert request.url.params.get("pin") == "true"
        return httpx.Response(
            200,
            json={"Name": "blob", "Hash": expected_cid, "Size": str(len(raw))},
        )

    _inject(handler)
    cid = await ipfs.add(raw)
    assert cid == expected_cid


@pytest.mark.asyncio
async def test_add_pin_false():
    """add(pin=False) sends pin=false query param."""
    from etzhayyim_sdk import ipfs

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("pin") == "false"
        return httpx.Response(200, json={"Name": "blob", "Hash": "bafyXYZ", "Size": "3"})

    _inject(handler)
    cid = await ipfs.add(b"xyz", pin=False)
    assert cid == "bafyXYZ"


@pytest.mark.asyncio
async def test_add_missing_hash():
    """add() raises IpfsServerError when Hash is absent from Kubo response."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsServerError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Name": "blob", "Size": "5"})

    _inject(handler)
    with pytest.raises(IpfsServerError, match="missing Hash"):
        await ipfs.add(b"hello")


@pytest.mark.asyncio
async def test_add_500():
    """add() raises IpfsServerError on HTTP 500."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsServerError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="storage error")

    _inject(handler)
    with pytest.raises(IpfsServerError) as exc_info:
        await ipfs.add(b"data")
    assert exc_info.value.status_code == 500


# ── pin_ls ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pin_ls_all():
    """pin_ls() without cid returns all pins as list[dict]."""
    from etzhayyim_sdk import ipfs

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/api/v0/pin/ls" in request.url.path
        assert "arg" not in request.url.params
        return httpx.Response(
            200,
            json={
                "Keys": {
                    "bafy001": {"Type": "recursive"},
                    "bafy002": {"Type": "direct"},
                }
            },
        )

    _inject(handler)
    pins = await ipfs.pin_ls()
    assert len(pins) == 2
    cids = {p["cid"] for p in pins}
    assert "bafy001" in cids
    assert "bafy002" in cids
    types = {p["cid"]: p["type"] for p in pins}
    assert types["bafy001"] == "recursive"
    assert types["bafy002"] == "direct"


@pytest.mark.asyncio
async def test_pin_ls_filtered():
    """pin_ls(cid=…) passes arg param and returns filtered list."""
    from etzhayyim_sdk import ipfs

    target = "bafy001"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("arg") == target
        return httpx.Response(
            200,
            json={"Keys": {target: {"Type": "recursive"}}},
        )

    _inject(handler)
    pins = await ipfs.pin_ls(cid=target)
    assert len(pins) == 1
    assert pins[0]["cid"] == target
    assert pins[0]["type"] == "recursive"


@pytest.mark.asyncio
async def test_pin_ls_empty():
    """pin_ls() returns empty list when Keys is absent or empty."""
    from etzhayyim_sdk import ipfs

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Keys": {}})

    _inject(handler)
    pins = await ipfs.pin_ls()
    assert pins == []


@pytest.mark.asyncio
async def test_pin_ls_500():
    """pin_ls() raises IpfsServerError on HTTP 500."""
    from etzhayyim_sdk import ipfs
    from etzhayyim_sdk.errors import IpfsServerError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="error")

    _inject(handler)
    with pytest.raises(IpfsServerError):
        await ipfs.pin_ls()


# ── error hierarchy ───────────────────────────────────────────────────────────


def test_ipfs_error_hierarchy():
    """IpfsNetworkError and IpfsServerError both extend IpfsError."""
    from etzhayyim_sdk.errors import IpfsError, IpfsNetworkError, IpfsServerError

    assert issubclass(IpfsNetworkError, IpfsError)
    assert issubclass(IpfsServerError, IpfsError)


def test_ipfs_server_error_attrs():
    """IpfsServerError carries status_code and body attributes."""
    from etzhayyim_sdk.errors import IpfsServerError

    err = IpfsServerError("pin failed", status_code=503, body="Service Unavailable")
    assert err.status_code == 503
    assert err.body == "Service Unavailable"
    assert "503" in str(err) or "pin failed" in str(err)


# ── mst.subscribe: M5 real impl — detailed tests in tests/test_mst_subscribe.py ──


def test_subscribe_is_async_generator_function():
    """mst.subscribe is now a real async generator function (M5 impl complete)."""
    import inspect

    from etzhayyim_sdk import mst

    assert inspect.isasyncgenfunction(mst.subscribe)
