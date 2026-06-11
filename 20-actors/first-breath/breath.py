"""
first-breath — proof-of-life cell for the etzhayyim substrate.

Anchors the cell's evolving state to EtzhayyimAnchor on Base L2 / geth-private
/ local anvil. One invocation = one breath. Loop externally (cron / launchd
/ while-true).

Usage:
    uv run breath.py                                   # local anvil defaults
    ETZ_ANCHOR=0x... ETZ_RPC=http://... uv run breath.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from eth_account import Account
from web3 import Web3

# ─── Config (env-overridable) ───────────────────────────────────────

DEFAULT_RPC = "http://localhost:8545"
DEFAULT_ANCHOR = "0x5fbdb2315678afecb367f032d93f642f64180aa3"  # per deps.toml local_anvil
# Anvil pre-funded acct[0] — well-known testing key, NOT for production.
DEFAULT_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

RPC_URL = os.environ.get("ETZ_RPC", DEFAULT_RPC)
ANCHOR_ADDR = os.environ.get("ETZ_ANCHOR", DEFAULT_ANCHOR)
PRIVATE_KEY = os.environ.get("ETZ_PK", DEFAULT_PRIVATE_KEY)

STATE_PATH = Path(__file__).parent / "state.json"

# Minimal ABI for the only two methods we touch.
ANCHOR_ABI = [
    {
        "type": "function",
        "name": "anchor",
        "inputs": [
            {"name": "rootHash", "type": "bytes32"},
            {"name": "ipfsCid", "type": "bytes"},
            {"name": "batchSize", "type": "uint64"},
        ],
        "outputs": [],
        "stateMutability": "nonpayable",
    },
    {
        "type": "function",
        "name": "rootCount",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
    },
]


# ─── Cell state ─────────────────────────────────────────────────────


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"counter": 0, "last_anchor_tx": None, "last_block": 0}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def mutate_state(state: dict) -> dict:
    state["counter"] = state.get("counter", 0) + 1
    state["last_tick_at"] = datetime.now(tz=timezone.utc).isoformat()
    return state


def state_root(state: dict) -> bytes:
    """Mock MST root = sha256 of canonical-JSON-serialized state.

    Production swaps this for a proper AT Protocol MST root CID (per
    ADR-2605171800), but the on-chain shape stays the same bytes32.
    """
    canon = json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canon).digest()


# ─── Anchor call ────────────────────────────────────────────────────


def breath() -> int:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"[first-breath] cannot reach RPC {RPC_URL}", file=sys.stderr)
        return 2

    acct = Account.from_key(PRIVATE_KEY)
    anchor = w3.eth.contract(
        address=Web3.to_checksum_address(ANCHOR_ADDR), abi=ANCHOR_ABI
    )

    state = mutate_state(load_state())
    root = state_root(state)
    # Mock IPFS CID — production gets this from the ipfs-pinner.
    ipfs_cid = f"bafyreidemo-breath-{state['counter']}".encode()

    print(f"[first-breath] tick #{state['counter']}")
    print(f"[first-breath]   ts:        {state['last_tick_at']}")
    print(f"[first-breath]   root:      0x{root.hex()}")
    print(f"[first-breath]   ipfs_cid:  {ipfs_cid.decode()}")

    tx = anchor.functions.anchor(root, ipfs_cid, state["counter"]).build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "gas": 250_000,
            "gasPrice": w3.eth.gas_price,
            "chainId": w3.eth.chain_id,
        }
    )
    signed = acct.sign_transaction(tx)
    raw = signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

    if receipt.status != 1:
        print(f"[first-breath] anchor tx reverted: {tx_hash.hex()}", file=sys.stderr)
        return 3

    state["last_anchor_tx"] = "0x" + tx_hash.hex()
    state["last_block"] = receipt.blockNumber
    save_state(state)

    count = anchor.functions.rootCount().call()
    print(f"[first-breath]   anchored:  tx 0x{tx_hash.hex()} block {receipt.blockNumber}")
    print(f"[first-breath]   verified:  Anchor.rootCount() = {count}")
    print(f"[first-breath] breath {state['counter']} complete.")
    return 0


if __name__ == "__main__":
    sys.exit(breath())
