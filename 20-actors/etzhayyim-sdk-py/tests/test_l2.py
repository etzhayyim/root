"""Tests for etzhayyim_sdk.l2 — Base L2 anchor helpers (M5).

Tests:
  1.  test_latest_block_happy            — mock eth_blockNumber, check int return
  2.  test_latest_block_network_error    — httpx.HTTPError → L2NetworkError
  3.  test_latest_block_server_error     — RPC error field → L2ServerError
  4.  test_anchor_no_contract_address    — raises L2ContractError
  5.  test_anchor_no_key                 — raises L2SigningError
  6.  test_anchor_happy                  — full mock RPC path; verifies eth_sendRawTransaction
  7.  test_anchor_gas_price_ceiling      — gas price over ceiling → L2ServerError
  8.  test_read_anchor_happy             — mock eth_getTransactionReceipt, verify decoded fields
  9.  test_read_anchor_not_found         — receipt=null → L2Error
  10. test_read_anchor_reverted          — status=0x0 → L2Error
  11. test_read_anchor_no_anchored_log   — logs without Anchored event → L2Error
  12. test_get_anchor_happy              — mock eth_call returns ABI-encoded struct
  13. test_get_anchor_not_anchored       — blockNumber=0 in return → None
  14. test_cid_to_root_hash_deterministic — same CID → same bytes32
  15. test_encode_anchor_calldata_selector — calldata starts with ANCHOR_FUNCTION_SELECTOR
  16. test_rpc_http_500_raises_server_error

ADR references:
  ADR-2605171800 Stage 4 — Base L2 anchor pipeline
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
_sdk_src = Path(__file__).resolve().parents[1] / "src"
if str(_sdk_src) not in sys.path:
    sys.path.insert(0, str(_sdk_src))

# ── Helpers ───────────────────────────────────────────────────────────────────

FAKE_TX_HASH = "0x" + "ab" * 32
FAKE_CONTRACT = "0x1234567890123456789012345678901234567890"
# secp256k1 order N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
# key must be in [1, N-1].  0x...01 is always valid.
FAKE_ANCHOR_KEY = "0x" + "00" * 31 + "01"  # minimal valid secp256k1 private key
FAKE_CID = "bafybeig5abc123testkeccak"

# Minimal fake ABI-encoded return for anchors(bytes32) with blockNumber > 0.
# Layout: rootHash(32) + offset(32) + blockNumber(32) + anchorer(32) + batchSize(32) + anchoredAt(32) + cid_len(32) + cid_data(32-padded)
def _make_anchors_return(cid: str = FAKE_CID, block_number: int = 100) -> str:
    root_hash = hashlib.sha256(cid.encode()).digest()
    cid_bytes = cid.encode("utf-8")
    cid_len = len(cid_bytes)
    # Dynamic offset: 6 slots × 32 = 192 = 0xC0
    offset = 6 * 32
    anchorer = b"\x00" * 12 + bytes.fromhex("DeadBeefDeadBeefDeadBeefDeadBeefDeadBeef")
    batch_size = 1
    anchored_at = 1716300000

    padding = (32 - (cid_len % 32)) % 32
    cid_padded = cid_bytes + b"\x00" * padding

    data = (
        root_hash                                        # slot 0: rootHash
        + offset.to_bytes(32, "big")                     # slot 1: offset of bytes
        + block_number.to_bytes(32, "big")               # slot 2: blockNumber
        + anchorer                                        # slot 3: anchorer
        + batch_size.to_bytes(32, "big")                 # slot 4: batchSize
        + anchored_at.to_bytes(32, "big")                # slot 5: anchoredAt
        + cid_len.to_bytes(32, "big")                    # cid length
        + cid_padded                                      # cid data
    )
    return "0x" + data.hex()


def _make_anchored_log(cid: str = FAKE_CID, block_number: int = 100) -> dict[str, Any]:
    """Build a fake eth_getTransactionReceipt log for the Anchored event."""
    from etzhayyim_sdk.l2 import ANCHORED_EVENT_TOPIC, _cid_to_root_hash

    root_hash_bytes = _cid_to_root_hash(cid)
    root_hash_topic = "0x" + root_hash_bytes.hex()
    anchorer_topic = "0x" + "00" * 12 + "deadbeef" * 5  # 32 bytes, last 20 = anchorer addr

    # Non-indexed data: (bytes ipfsCid, uint256 blockNumber, uint64 batchSize)
    cid_bytes = cid.encode("utf-8")
    cid_len = len(cid_bytes)
    # offset(32) + blockNumber(32) + batchSize(32) + cid_len(32) + cid_data
    offset = 3 * 32  # 3 head slots before dynamic data
    padding = (32 - (cid_len % 32)) % 32
    cid_padded = cid_bytes + b"\x00" * padding

    data = (
        offset.to_bytes(32, "big")           # offset of bytes
        + block_number.to_bytes(32, "big")   # blockNumber
        + (1).to_bytes(32, "big")            # batchSize
        + cid_len.to_bytes(32, "big")        # cid length
        + cid_padded                          # cid data
    )

    return {
        "topics": [ANCHORED_EVENT_TOPIC, root_hash_topic, anchorer_topic],
        "data": "0x" + data.hex(),
    }


def _make_receipt(
    status: str = "0x1",
    cid: str = FAKE_CID,
    block_number: str = "0x64",
    include_anchored_log: bool = True,
) -> dict[str, Any]:
    logs = [_make_anchored_log(cid=cid)] if include_anchored_log else []
    return {
        "status": status,
        "blockNumber": block_number,
        "transactionHash": FAKE_TX_HASH,
        "logs": logs,
    }


def _inject_mock_transport(responses: list[dict[str, Any]]) -> None:
    """Inject a MockTransport into l2 module that returns each response in sequence."""
    from etzhayyim_sdk import l2

    call_index = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_index
        body = json.loads(request.content)
        resp = responses[call_index % len(responses)]
        call_index += 1
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body.get("id", 1), "result": resp})

    transport = httpx.MockTransport(handler)
    l2._inject_transport(transport)


def _inject_mock_transport_seq(method_responses: dict[str, Any]) -> None:
    """Inject transport that routes by RPC method name."""
    from etzhayyim_sdk import l2

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        method = body.get("method", "")
        result = method_responses.get(method, "0x0")
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body.get("id", 1), "result": result})

    transport = httpx.MockTransport(handler)
    l2._inject_transport(transport)


def _inject_error_transport(status_code: int = 500) -> None:
    from etzhayyim_sdk import l2

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    l2._inject_transport(transport)


def _inject_rpc_error_transport() -> None:
    from etzhayyim_sdk import l2

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": body.get("id", 1),
                "error": {"code": -32603, "message": "Internal error"},
            },
        )

    transport = httpx.MockTransport(handler)
    l2._inject_transport(transport)


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_latest_block_happy():
    """eth_blockNumber returns hex → latest_block() returns int."""
    from etzhayyim_sdk import l2

    _inject_mock_transport_seq({"eth_blockNumber": "0x1a2b3c"})
    block = await l2.latest_block()
    assert block == 0x1A2B3C
    assert isinstance(block, int)


@pytest.mark.asyncio
async def test_latest_block_network_error():
    """httpx.HTTPError during RPC → L2NetworkError."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2NetworkError

    def error_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    l2._inject_transport(httpx.MockTransport(error_handler))

    with pytest.raises(L2NetworkError, match="network error"):
        await l2.latest_block()


@pytest.mark.asyncio
async def test_latest_block_server_error():
    """RPC error field in body → L2ServerError."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2ServerError

    _inject_rpc_error_transport()
    with pytest.raises(L2ServerError, match="error"):
        await l2.latest_block()


@pytest.mark.asyncio
async def test_anchor_no_contract_address(monkeypatch: pytest.MonkeyPatch):
    """anchor() with unset/placeholder contract → L2ContractError."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2ContractError

    monkeypatch.delenv("ETZHAYYIM_L2_CONTRACT_ADDRESS", raising=False)
    with pytest.raises(L2ContractError, match="ETZHAYYIM_L2_CONTRACT_ADDRESS"):
        await l2.anchor(FAKE_CID)


@pytest.mark.asyncio
async def test_anchor_no_key(monkeypatch: pytest.MonkeyPatch):
    """anchor() with missing key and valid contract → L2SigningError."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2SigningError

    monkeypatch.setenv("ETZHAYYIM_L2_CONTRACT_ADDRESS", FAKE_CONTRACT)
    monkeypatch.delenv("ETZHAYYIM_L2_ANCHOR_KEY", raising=False)
    with pytest.raises(L2SigningError, match="ETZHAYYIM_L2_ANCHOR_KEY"):
        await l2.anchor(FAKE_CID)


@pytest.mark.asyncio
async def test_anchor_happy(monkeypatch: pytest.MonkeyPatch):
    """anchor() happy path: verifies eth_sendRawTransaction is called."""
    from etzhayyim_sdk import l2

    monkeypatch.setenv("ETZHAYYIM_L2_CONTRACT_ADDRESS", FAKE_CONTRACT)
    monkeypatch.setenv("ETZHAYYIM_L2_ANCHOR_KEY", FAKE_ANCHOR_KEY)

    calls_log: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        method = body.get("method", "")
        calls_log.append(method)

        if method == "eth_getTransactionCount":
            result = "0x0"
        elif method == "eth_gasPrice":
            result = hex(1 * 10**9)  # 1 Gwei, well under 20 Gwei ceiling
        elif method == "eth_chainId":
            result = hex(l2.BASE_SEPOLIA_CHAIN_ID)
        elif method == "eth_sendRawTransaction":
            result = FAKE_TX_HASH
        else:
            result = "0x0"

        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body.get("id", 1), "result": result})

    l2._inject_transport(httpx.MockTransport(handler))

    # eth_account is likely not installed; if so, expect L2SigningError
    try:
        import eth_account  # noqa: F401
        eth_account_available = True
    except ImportError:
        eth_account_available = False

    if eth_account_available:
        tx_hash = await l2.anchor(FAKE_CID)
        assert tx_hash == FAKE_TX_HASH
        assert "eth_sendRawTransaction" in calls_log
        assert "eth_getTransactionCount" in calls_log
        assert "eth_gasPrice" in calls_log
        assert "eth_chainId" in calls_log
    else:
        from etzhayyim_sdk.errors import L2SigningError
        with pytest.raises(L2SigningError, match="eth_account"):
            await l2.anchor(FAKE_CID)
        # Verify that nonce, gas, and chainId RPC calls were still made before signing
        assert "eth_getTransactionCount" in calls_log
        assert "eth_gasPrice" in calls_log


@pytest.mark.asyncio
async def test_anchor_gas_price_ceiling(monkeypatch: pytest.MonkeyPatch):
    """anchor() raises L2ServerError if gas price exceeds ceiling."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2ServerError

    monkeypatch.setenv("ETZHAYYIM_L2_CONTRACT_ADDRESS", FAKE_CONTRACT)
    monkeypatch.setenv("ETZHAYYIM_L2_ANCHOR_KEY", FAKE_ANCHOR_KEY)
    monkeypatch.setenv("ETZHAYYIM_L2_MAX_GAS_GWEI", "1")  # 1 Gwei ceiling

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        method = body.get("method", "")
        if method == "eth_getTransactionCount":
            result = "0x0"
        elif method == "eth_gasPrice":
            result = hex(50 * 10**9)  # 50 Gwei — over ceiling
        else:
            result = "0x0"
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body.get("id", 1), "result": result})

    l2._inject_transport(httpx.MockTransport(handler))

    with pytest.raises(L2ServerError, match="gas price"):
        await l2.anchor(FAKE_CID)


@pytest.mark.asyncio
async def test_read_anchor_happy():
    """read_anchor() decodes Anchored event from receipt."""
    from etzhayyim_sdk import l2

    receipt = _make_receipt(cid=FAKE_CID)
    _inject_mock_transport_seq({"eth_getTransactionReceipt": receipt})

    result = await l2.read_anchor(FAKE_TX_HASH)
    assert result["tx_hash"] == FAKE_TX_HASH
    assert result["block_number"] == 100
    assert result["status"] == 1
    assert result["ipfs_cid"] == FAKE_CID
    assert result["batch_size"] == 1


@pytest.mark.asyncio
async def test_read_anchor_not_found():
    """read_anchor() raises L2Error if tx receipt is null."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2Error

    _inject_mock_transport_seq({"eth_getTransactionReceipt": None})

    with pytest.raises(L2Error, match="not found"):
        await l2.read_anchor(FAKE_TX_HASH)


@pytest.mark.asyncio
async def test_read_anchor_reverted():
    """read_anchor() raises L2Error if tx status is 0 (reverted)."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2Error

    receipt = _make_receipt(status="0x0")
    _inject_mock_transport_seq({"eth_getTransactionReceipt": receipt})

    with pytest.raises(L2Error, match="reverted"):
        await l2.read_anchor(FAKE_TX_HASH)


@pytest.mark.asyncio
async def test_read_anchor_no_anchored_log():
    """read_anchor() raises L2Error if receipt has no Anchored event."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2Error

    receipt = _make_receipt(include_anchored_log=False)
    _inject_mock_transport_seq({"eth_getTransactionReceipt": receipt})

    with pytest.raises(L2Error, match="No Anchored event"):
        await l2.read_anchor(FAKE_TX_HASH)


@pytest.mark.asyncio
async def test_get_anchor_happy(monkeypatch: pytest.MonkeyPatch):
    """get_anchor() calls eth_call and decodes the AnchorEntry struct."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2ContractError

    monkeypatch.setenv("ETZHAYYIM_L2_CONTRACT_ADDRESS", FAKE_CONTRACT)

    abi_return = _make_anchors_return(cid=FAKE_CID, block_number=100)
    _inject_mock_transport_seq({"eth_call": abi_return})

    result = await l2.get_anchor(FAKE_CID)
    assert result is not None
    assert result["block_number"] == 100
    assert result["ipfs_cid"] == FAKE_CID
    assert result["batch_size"] == 1
    assert result["anchored_at"] == 1716300000


@pytest.mark.asyncio
async def test_get_anchor_not_anchored(monkeypatch: pytest.MonkeyPatch):
    """get_anchor() returns None when blockNumber is 0 (never anchored)."""
    from etzhayyim_sdk import l2

    monkeypatch.setenv("ETZHAYYIM_L2_CONTRACT_ADDRESS", FAKE_CONTRACT)

    # All-zero return = empty struct = never anchored
    abi_return = "0x" + "00" * (7 * 32 + 32)  # 8 slots of zeros
    _inject_mock_transport_seq({"eth_call": abi_return})

    result = await l2.get_anchor(FAKE_CID)
    assert result is None


@pytest.mark.asyncio
async def test_get_anchor_no_contract(monkeypatch: pytest.MonkeyPatch):
    """get_anchor() raises L2ContractError if contract unset."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2ContractError

    monkeypatch.delenv("ETZHAYYIM_L2_CONTRACT_ADDRESS", raising=False)
    with pytest.raises(L2ContractError):
        await l2.get_anchor(FAKE_CID)


@pytest.mark.asyncio
async def test_rpc_http_500_raises_server_error():
    """HTTP 500 from RPC endpoint → L2ServerError."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2ServerError

    _inject_error_transport(500)
    with pytest.raises(L2ServerError, match="HTTP 500"):
        await l2.latest_block()


def test_cid_to_root_hash_deterministic():
    """Same CID always produces the same 32-byte hash."""
    from etzhayyim_sdk.l2 import _cid_to_root_hash

    h1 = _cid_to_root_hash(FAKE_CID)
    h2 = _cid_to_root_hash(FAKE_CID)
    assert h1 == h2
    assert len(h1) == 32
    assert isinstance(h1, bytes)

    # Different CIDs produce different hashes
    h3 = _cid_to_root_hash("bafybeig_different")
    assert h1 != h3


def test_encode_anchor_calldata_selector():
    """Calldata for anchor() starts with the correct 4-byte function selector."""
    from etzhayyim_sdk.l2 import (
        ANCHOR_FUNCTION_SELECTOR,
        _cid_to_root_hash,
        _encode_anchor_calldata,
    )

    root_hash = _cid_to_root_hash(FAKE_CID)
    calldata = _encode_anchor_calldata(root_hash, FAKE_CID.encode(), 1)

    selector_bytes = bytes.fromhex(ANCHOR_FUNCTION_SELECTOR[2:])
    assert calldata[:4] == selector_bytes
    # Total: 4 (selector) + 3×32 (head) + 32 (cid len) + N×32 (cid data padded)
    assert len(calldata) >= 4 + 4 * 32


def test_l2_error_hierarchy():
    """All L2 errors extend L2Error."""
    from etzhayyim_sdk.errors import (
        L2ContractError,
        L2Error,
        L2NetworkError,
        L2ServerError,
        L2SigningError,
    )

    assert issubclass(L2NetworkError, L2Error)
    assert issubclass(L2ServerError, L2Error)
    assert issubclass(L2ContractError, L2Error)
    assert issubclass(L2SigningError, L2Error)


def test_constants_defined():
    """Module-level constants are present and sane."""
    from etzhayyim_sdk import l2

    assert l2.BASE_MAINNET_CHAIN_ID == 8453
    assert l2.BASE_SEPOLIA_CHAIN_ID == 84532
    assert l2.ANCHOR_FUNCTION_SELECTOR.startswith("0x")
    assert len(l2.ANCHOR_FUNCTION_SELECTOR) == 10  # "0x" + 8 hex chars
    assert l2.ANCHORED_EVENT_TOPIC.startswith("0x")
    assert len(l2.ANCHORED_EVENT_TOPIC) == 66  # "0x" + 64 hex chars
    assert l2.DEFAULT_GAS_LIMIT == 80_000


# ── verify() helpers ──────────────────────────────────────────────────────────


def _build_merkle_proof(
    leaves: list[bytes], target_idx: int
) -> tuple[bytes, list[dict]]:
    """Build a binary Merkle tree from *leaves* and return the (root, path)
    for the leaf at *target_idx*.

    Tree layout (example, 4 leaves):
        level 2 (root): H(H01 || H23)
        level 1:        H(L0 || L1)   H(L2 || L3)
        level 0:        L0  L1  L2  L3

    Each path step: {"side": "L"|"R", "hash": "0x<sibling_hex>"}.
    Side = direction of the *sibling* relative to the current node.

    Constraints:
    - len(leaves) must be a power of 2 and >= 2.
    - Each leaf must be exactly 32 bytes.

    Returns:
        (root_bytes_32, path)  — root is 32 bytes, path is leaf-to-root order.
    """
    assert len(leaves) >= 2 and (len(leaves) & (len(leaves) - 1)) == 0, \
        "leaves must be a power-of-2 length >= 2"
    assert all(len(l) == 32 for l in leaves), "each leaf must be 32 bytes"

    current_level = list(leaves)
    path: list[dict] = []
    idx = target_idx

    while len(current_level) > 1:
        next_level: list[bytes] = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1]
            parent = hashlib.sha256(left + right).digest()
            next_level.append(parent)

        # Which pair contains our target?
        pair_idx = idx // 2
        sibling_is_right = (idx % 2 == 0)  # True → sibling is idx+1 (right)

        if sibling_is_right:
            sibling = current_level[idx + 1]
            side = "R"
        else:
            sibling = current_level[idx - 1]
            side = "L"

        path.append({"side": side, "hash": "0x" + sibling.hex()})
        idx = pair_idx
        current_level = next_level

    root = current_level[0]
    return root, path


def _make_verify_proof(
    leaves: list[bytes],
    target_idx: int,
    record_cid: str,
    mst_root_cid: str,
    l2_anchor_tx: str,
) -> dict:
    """Build a full verify() proof dict for the given synthetic tree."""
    _root, path = _build_merkle_proof(leaves, target_idx)
    return {
        "record_uri": f"at://did:web:test/{target_idx}",
        "record_cid": record_cid,
        "mst_path": path,
        "mst_root_cid": mst_root_cid,
        "l2_anchor_tx": l2_anchor_tx,
    }


def _synthetic_tree() -> tuple[list[bytes], bytes, str, str]:
    """Return (leaves_32, root_bytes, record_cid_str, mst_root_cid_str).

    Builds a 4-leaf tree where leaf[0] = sha256(record_cid).
    mst_root_cid is chosen so that sha256(mst_root_cid) == tree_root.

    Because sha256 is one-way we pick *mst_root_cid* as a plain string whose
    sha256 equals the computed root.  In practice the CID encodes the hash;
    here we cheat by using the root hex itself as the CID string to satisfy
    _cid_to_root_hash(mst_root_cid) == root.  That is: we set
    mst_root_cid_str such that sha256(mst_root_cid_str.encode()) == root.

    Since we can't invert sha256 we instead fix the approach differently:
    we let mst_root_cid be an arbitrary CID string, compute
    target_root = sha256(mst_root_cid.encode()), and then build a tree
    whose root *equals* target_root by using it directly as the parent of
    level-1 nodes.

    Simpler: we build the tree first, get root_bytes, then define
    mst_root_cid as the hex of root_bytes.  _cid_to_root_hash will then
    compute sha256(root_hex_str.encode()) which is NOT equal to root_bytes.

    The cleanest approach for testing: define a helper CID whose sha256 IS
    the root, by setting the CID string to be a fixed value and building the
    tree leaves so that the resulting tree root == sha256(cid.encode()).

    Easiest: just pick record_cid and mst_root_cid freely, compute their
    hashes, build a 4-leaf tree with leaf[0] = hash(record_cid) and
    leaf[1..3] = arbitrary known hashes, compute the real root, then set
    mst_root_cid_str such that sha256(mst_root_cid_str.encode()) == root.

    Since we cannot invert sha256, we use a different encoding: store the
    raw root bytes as a latin-1 string so that .encode('latin-1') == root.
    But that is fragile.

    FINAL decision: build the tree, get root_bytes, then define
    mst_root_cid_str = root_bytes.hex() and verify with a patched
    _cid_to_root_hash that returns root_bytes when given mst_root_cid_str.
    But that requires patching the module helper.

    CLEANEST for tests: define mst_root_cid as a string whose sha256 we
    know in advance by construction.  We fix mst_root_cid = "FIXED_ROOT",
    compute claimed_root_bytes = sha256(b"FIXED_ROOT"), then build leaf
    hashes so the 4-leaf tree root == claimed_root_bytes.

    Steps:
      1. claimed_root_bytes = sha256(b"FIXED_ROOT")
      2. Pick arbitrary h1, h2, h3 (fixed bytes).
      3. level1_left  = sha256(leaf0 || h1)
      4. level1_right = sha256(h2  || h3)
      5. We need: sha256(level1_left || level1_right) == claimed_root_bytes
         → This cannot be forced without inverting sha256.

    Accept the reality: in tests we cannot make the tree root equal an
    independently chosen sha256 value without brute force.  Instead, we
    build the tree with arbitrary leaves, get the real root, and then define
    mst_root_cid as a string that _cid_to_root_hash maps to that root.

    _cid_to_root_hash(s) = sha256(s.encode('utf-8')).  We need a string s
    such that sha256(s.encode()) == tree_root.  Again not invertible.

    Resolution: patch _cid_to_root_hash in the module during the test to
    use an identity-like mapping for test CIDs.  OR — better — don't test
    through _cid_to_root_hash at all: use the SAME convention internally
    in the proof builder: the "CID" strings in the proof are the hex of
    their own sha256 preimage, and the leaves ARE sha256(cid_bytes).

    We implement: record_cid = "record_cid_leaf0", leaf[0] = sha256(record_cid.encode()),
    leaf[1..3] = sha256(fixed_strings).  Build tree, get root.
    mst_root_cid = a fixed string; but we patch _cid_to_root_hash during
    the verify() call to return root directly when given mst_root_cid.

    Actually the simplest approach: DON'T try to match _cid_to_root_hash.
    Instead, define mst_root_cid as the *input* to sha256 that yields root,
    and since we cannot do that, just use a loop to find a random collision —
    NO, too slow.

    FINAL FINAL: Override the CID → hash mapping so mst_root_cid = root_bytes.hex()
    and patch _cid_to_root_hash for the duration of the test to be
    `bytes.fromhex(s)` when s is a 64-char hex string, else the real sha256.
    """
    record_cid = "bafytest_record_leaf_0"
    leaf0 = hashlib.sha256(record_cid.encode()).digest()
    leaf1 = hashlib.sha256(b"leaf1").digest()
    leaf2 = hashlib.sha256(b"leaf2").digest()
    leaf3 = hashlib.sha256(b"leaf3").digest()
    leaves = [leaf0, leaf1, leaf2, leaf3]

    # Build tree to get root
    level1_left = hashlib.sha256(leaf0 + leaf1).digest()
    level1_right = hashlib.sha256(leaf2 + leaf3).digest()
    root = hashlib.sha256(level1_left + level1_right).digest()

    # mst_root_cid is the hex of root so that bytes.fromhex(mst_root_cid) == root.
    # We patch _cid_to_root_hash in tests to handle this.
    mst_root_cid = root.hex()  # 64-char hex string

    return leaves, root, record_cid, mst_root_cid


def _patched_cid_to_root_hash(cid: str) -> bytes:
    """Test-only CID→hash: if cid is 64 hex chars, decode directly; else sha256."""
    if len(cid) == 64:
        try:
            return bytes.fromhex(cid)
        except ValueError:
            pass
    return hashlib.sha256(cid.encode()).digest()


# ── verify() tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_happy_path():
    """4-leaf Merkle tree: valid proof + matching on-chain rootHash → True."""
    from unittest.mock import AsyncMock, patch

    from etzhayyim_sdk import l2

    leaves, root, record_cid, mst_root_cid = _synthetic_tree()
    _root_check, path = _build_merkle_proof(leaves, target_idx=0)
    assert _root_check == root, "sanity: tree root must match"

    proof = {
        "record_uri": "at://did:web:test/record_0",
        "record_cid": record_cid,
        "mst_path": path,
        "mst_root_cid": mst_root_cid,
        "l2_anchor_tx": FAKE_TX_HASH,
    }

    # on-chain root_hash = root.hex() (matching claimed_root_bytes = root)
    fake_anchor = {
        "tx_hash": FAKE_TX_HASH,
        "block_number": 100,
        "status": 1,
        "root_hash": "0x" + root.hex(),
        "anchorer": "0xdeadbeef" * 5,
        "ipfs_cid": mst_root_cid,
        "batch_size": 1,
    }

    with (
        patch.object(l2, "_cid_to_root_hash", side_effect=_patched_cid_to_root_hash),
        patch.object(l2, "read_anchor", new=AsyncMock(return_value=fake_anchor)),
    ):
        result = await l2.verify(mst_root_cid, proof)

    assert result is True


@pytest.mark.asyncio
async def test_verify_wrong_root():
    """Tampered mst_path step → computed root mismatch → False (no exception)."""
    from unittest.mock import AsyncMock, patch

    from etzhayyim_sdk import l2

    leaves, root, record_cid, mst_root_cid = _synthetic_tree()
    _root_check, path = _build_merkle_proof(leaves, target_idx=0)

    # Tamper: flip one sibling hash
    tampered_path = [dict(step) for step in path]
    tampered_path[0] = {"side": tampered_path[0]["side"], "hash": "0x" + "ff" * 32}

    proof = {
        "record_uri": "at://did:web:test/record_0",
        "record_cid": record_cid,
        "mst_path": tampered_path,
        "mst_root_cid": mst_root_cid,
        "l2_anchor_tx": FAKE_TX_HASH,
    }

    with patch.object(l2, "_cid_to_root_hash", side_effect=_patched_cid_to_root_hash):
        result = await l2.verify(mst_root_cid, proof)

    assert result is False


@pytest.mark.asyncio
async def test_verify_commit_cid_mismatch():
    """commit_cid != mst_root_cid → False even if Merkle path is valid."""
    from unittest.mock import AsyncMock, patch

    from etzhayyim_sdk import l2

    leaves, root, record_cid, mst_root_cid = _synthetic_tree()
    _root_check, path = _build_merkle_proof(leaves, target_idx=0)

    proof = {
        "record_uri": "at://did:web:test/record_0",
        "record_cid": record_cid,
        "mst_path": path,
        "mst_root_cid": mst_root_cid,
        "l2_anchor_tx": FAKE_TX_HASH,
    }

    different_commit_cid = "bafydifferentcommit"

    with patch.object(l2, "_cid_to_root_hash", side_effect=_patched_cid_to_root_hash):
        result = await l2.verify(different_commit_cid, proof)

    assert result is False


@pytest.mark.asyncio
async def test_verify_on_chain_mismatch():
    """Local Merkle path verifies but read_anchor returns different rootHash → False."""
    from unittest.mock import AsyncMock, patch

    from etzhayyim_sdk import l2

    leaves, root, record_cid, mst_root_cid = _synthetic_tree()
    _root_check, path = _build_merkle_proof(leaves, target_idx=0)

    proof = {
        "record_uri": "at://did:web:test/record_0",
        "record_cid": record_cid,
        "mst_path": path,
        "mst_root_cid": mst_root_cid,
        "l2_anchor_tx": FAKE_TX_HASH,
    }

    # Return a different root from the chain
    different_root = hashlib.sha256(b"different_root").digest()
    fake_anchor = {
        "tx_hash": FAKE_TX_HASH,
        "block_number": 100,
        "status": 1,
        "root_hash": "0x" + different_root.hex(),
        "anchorer": "0xdeadbeef" * 5,
        "ipfs_cid": mst_root_cid,
        "batch_size": 1,
    }

    with (
        patch.object(l2, "_cid_to_root_hash", side_effect=_patched_cid_to_root_hash),
        patch.object(l2, "read_anchor", new=AsyncMock(return_value=fake_anchor)),
    ):
        result = await l2.verify(mst_root_cid, proof)

    assert result is False


@pytest.mark.asyncio
async def test_verify_missing_keys():
    """proof dict missing 'record_cid' → L2VerificationError."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2VerificationError

    incomplete_proof = {
        "record_uri": "at://did:web:test/record_0",
        # record_cid intentionally omitted
        "mst_path": [],
        "mst_root_cid": "bafy_root",
        "l2_anchor_tx": FAKE_TX_HASH,
    }

    with pytest.raises(L2VerificationError, match="missing keys"):
        await l2.verify("bafy_root", incomplete_proof)


@pytest.mark.asyncio
async def test_verify_invalid_sibling_hex():
    """A mst_path step with non-hex hash → L2VerificationError."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2VerificationError

    proof = {
        "record_uri": "at://did:web:test/record_0",
        "record_cid": FAKE_CID,
        "mst_path": [{"side": "R", "hash": "0xNOT_HEX"}],
        "mst_root_cid": "bafy_root",
        "l2_anchor_tx": FAKE_TX_HASH,
    }

    with pytest.raises(L2VerificationError, match="invalid sibling hash"):
        await l2.verify("bafy_root", proof)


@pytest.mark.asyncio
async def test_verify_invalid_side():
    """A mst_path step with side='X' → L2VerificationError."""
    from etzhayyim_sdk import l2
    from etzhayyim_sdk.errors import L2VerificationError

    sibling_hex = "0x" + "aa" * 32
    proof = {
        "record_uri": "at://did:web:test/record_0",
        "record_cid": FAKE_CID,
        "mst_path": [{"side": "X", "hash": sibling_hex}],
        "mst_root_cid": "bafy_root",
        "l2_anchor_tx": FAKE_TX_HASH,
    }

    with pytest.raises(L2VerificationError, match="invalid side"):
        await l2.verify("bafy_root", proof)
