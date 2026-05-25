"""Blockchain head-delta ingest tasks for Zeebe workers.

The node pods own chain sync. These helpers only read stable RPC endpoints and
write deterministic RisingWave rows plus the generic ingest cursor.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

import sqlite3
from contextlib import contextmanager
from pymagatama.ingest.core import now_iso, today, upsert_cursor




@contextmanager
def sync_cursor():
    db_dir = os.environ.get("ORGANISM_SQLITE_DIR", "/var/lib/etzhayyim/organism")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "ingest_blockchain.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_ingest_cursor (
            vertex_id TEXT PRIMARY KEY,
            cursor_value TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_blockchain_actor (
            vertex_id TEXT PRIMARY KEY, _seq INTEGER, created_date TEXT, sensitivity_ord INTEGER, owner_did TEXT,
            rkey TEXT, repo TEXT, label TEXT, did TEXT, chain TEXT, address TEXT, name TEXT, balance INTEGER,
            total_received INTEGER, total_sent INTEGER, tx_count INTEGER, unconfirmed_tx_count INTEGER,
            risk_score REAL, source TEXT, observed_at TEXT, props TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_blockchain_block (
            vertex_id TEXT PRIMARY KEY, _seq INTEGER, created_date TEXT, sensitivity_ord INTEGER, owner_did TEXT,
            chain TEXT, source_id TEXT, height INTEGER, block_hash TEXT, parent_hash TEXT, block_time TEXT,
            tx_count INTEGER, raw_sha256 TEXT, raw_json TEXT, canonical_status TEXT, ingested_at TEXT, run_id TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS vertex_blockchain_tx (
            vertex_id TEXT PRIMARY KEY, _seq INTEGER, created_date TEXT, sensitivity_ord INTEGER, owner_did TEXT,
            chain TEXT, source_id TEXT, block_hash TEXT, block_height INTEGER, tx_hash TEXT, tx_index INTEGER,
            from_addr TEXT, to_addr TEXT, value_wei TEXT, raw_sha256 TEXT, raw_json TEXT, canonical_status TEXT, ingested_at TEXT, run_id TEXT
        )''')
        yield conn.cursor()

OWNER_DID = "did:web:blockchain.etzhayyim.com"
_BLOCK_TABLES_AVAILABLE: bool | None = None


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _http_json(url: str, payload: dict[str, Any], *, headers: dict[str, str] | None = None, timeout: int = 20) -> Any:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        body = e.read(4096).decode("utf-8", errors="replace")
        raise RuntimeError(f"RPC HTTP {e.code}: {body}") from e
    decoded = json.loads(body.decode("utf-8"))
    if decoded.get("error"):
        raise RuntimeError(f"RPC error: {decoded['error']}")
    return decoded.get("result")


def _bitcoin_rpc(method: str, params: list[Any] | None = None) -> Any:
    url = os.environ.get(
        "BITCOIN_RPC_URL",
        "http://bitcoin-mainnet.blockchain.svc.cluster.local:8332",
    )
    user = os.environ.get("BITCOIN_RPC_USER", "")
    password = os.environ.get("BITCOIN_RPC_PASSWORD", "")
    if not user or not password:
        raise RuntimeError("BITCOIN_RPC_USER/BITCOIN_RPC_PASSWORD are required")
    token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return _http_json(
        url,
        {"jsonrpc": "1.0", "id": "pymagatama-blockchain", "method": method, "params": params or []},
        headers={"Authorization": f"Basic {token}"},
    )


def _ethereum_rpc(method: str, params: list[Any] | None = None) -> Any:
    url = os.environ.get(
        "ETHEREUM_RPC_URL",
        "http://ethereum-mainnet.blockchain.svc.cluster.local:8545",
    )
    return _http_json(
        url,
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []},
    )


def _get_cursor_height(source_id: str) -> int | None:
    vid = f"at://did:web:ingest.etzhayyim.com/app.etzhayyim.apps.ingest.cursor/blockchain-{source_id}-head"
    try:
        with sync_cursor() as cur:
            cur.execute("SELECT cursor_value FROM vertex_ingest_cursor WHERE vertex_id = ?", (vid,))
            row = cur.fetchone()
        if not row or row[0] is None:
            return None
        return int(str(row[0]))
    except Exception:
        return None


def _block_tables_available() -> bool:
    global _BLOCK_TABLES_AVAILABLE
    if _BLOCK_TABLES_AVAILABLE is not None:
        return _BLOCK_TABLES_AVAILABLE
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('vertex_blockchain_block', 'vertex_blockchain_tx')
                """
            )
            row = cur.fetchone()
        _BLOCK_TABLES_AVAILABLE = int(row[0] if row else 0) == 2
    except Exception:
        _BLOCK_TABLES_AVAILABLE = False
    return _BLOCK_TABLES_AVAILABLE


def _insert_actor_landing(row: dict[str, Any], *, kind: str) -> int:
    raw = row.get("raw") or {}
    props = _json_dumps(
        {
            "kind": kind,
            "sourceId": row.get("source_id", ""),
            "height": row.get("height", row.get("block_height")),
            "blockHash": row.get("block_hash", ""),
            "parentHash": row.get("parent_hash", ""),
            "blockTime": row.get("block_time", ""),
            "txHash": row.get("tx_hash", ""),
            "txIndex": row.get("tx_index"),
            "from": row.get("from_addr", ""),
            "to": row.get("to_addr", ""),
            "valueWei": row.get("value_wei", ""),
            "rawSha256": _sha256_text(_json_dumps(raw)),
            "runId": row.get("run_id", ""),
        }
    )
    address = row.get("block_hash") if kind == "block" else row.get("tx_hash")
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT OR IGNORE INTO vertex_blockchain_actor (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              rkey, repo, label, did, chain, address, name, balance,
              total_received, total_sent, tx_count, unconfirmed_tx_count,
              risk_score, source, observed_at, props
            )
            VALUES (?, NULL, ?, 0, ?,
                   ?, ?, ?, ?, ?, ?, ?, 0,
                   0, 0, ?, 0,
                   0.0, ?, ?, ?)
            """,
            (
                row["vertex_id"],
                today(),
                OWNER_DID,
                row["vertex_id"][-64:],
                OWNER_DID,
                f"{kind}:{row.get('height', row.get('block_height', ''))}",
                f"did:web:blockchain.etzhayyim.com:{kind}:{row['vertex_id'][-48:]}",
                row["chain"],
                address or "",
                row["vertex_id"],
                row.get("tx_count", 0),
                row.get("source_id", ""),
                now_iso(),
                props,
            ),
        )
        return int(cur.rowcount or 0)


def _insert_block(row: dict[str, Any]) -> int:
    if not _block_tables_available():
        return _insert_actor_landing(row, kind="block")
    raw_json = _json_dumps(row.get("raw") or {})
    raw_sha256 = _sha256_text(raw_json)
    now = now_iso()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT OR IGNORE INTO vertex_blockchain_block (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              chain, source_id, height, block_hash, parent_hash, block_time,
              tx_count, raw_sha256, raw_json, canonical_status, ingested_at,
              run_id
            )
            VALUES (?, NULL, ?, 0, ?,
                   ?, ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?,
                   ?)
            """,
            (
                row["vertex_id"],
                today(),
                OWNER_DID,
                row["chain"],
                row["source_id"],
                row["height"],
                row["block_hash"],
                row.get("parent_hash", ""),
                row.get("block_time", ""),
                row.get("tx_count", 0),
                raw_sha256,
                raw_json,
                "canonical",
                now,
                row.get("run_id", ""),
            ),
        )
        return int(cur.rowcount or 0)


def _insert_tx(row: dict[str, Any]) -> int:
    if not _block_tables_available():
        return _insert_actor_landing(row, kind="tx")
    raw_json = _json_dumps(row.get("raw") or {})
    raw_sha256 = _sha256_text(raw_json)
    now = now_iso()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT OR IGNORE INTO vertex_blockchain_tx (
              vertex_id, _seq, created_date, sensitivity_ord, owner_did,
              chain, source_id, block_hash, block_height, tx_hash, tx_index,
              from_addr, to_addr, value_wei, raw_sha256, raw_json,
              canonical_status, ingested_at, run_id
            )
            VALUES (?, NULL, ?, 0, ?,
                   ?, ?, ?, ?, ?, ?,
                   ?, ?, ?, ?, ?,
                   ?, ?, ?)
            """,
            (
                row["vertex_id"],
                today(),
                OWNER_DID,
                row["chain"],
                row["source_id"],
                row["block_hash"],
                row["block_height"],
                row["tx_hash"],
                row["tx_index"],
                row.get("from_addr", ""),
                row.get("to_addr", ""),
                row.get("value_wei", ""),
                raw_sha256,
                raw_json,
                "canonical",
                now,
                row.get("run_id", ""),
            ),
        )
        return int(cur.rowcount or 0)


def ingest_bitcoin_head(*, run_id: str, source_id: str, max_blocks: int) -> dict[str, Any]:
    info = _bitcoin_rpc("getblockchaininfo")
    latest = int(info.get("blocks") or 0)
    cursor = _get_cursor_height(source_id)
    catchup_skipped = False
    if cursor is None:
        start = max(0, latest - max_blocks + 1)
    elif latest - cursor > max(1, int(os.environ.get("BLOCKCHAIN_MAX_CATCHUP_LAG_BLOCKS", "100"))):
        start = max(0, latest - max_blocks + 1)
        catchup_skipped = True
    else:
        start = cursor + 1
    end = min(latest, start + max_blocks - 1)
    if latest <= 0 or start > end:
        upsert_cursor(
            ingest_family="blockchain",
            source_id=source_id,
            shard_key="head",
            cursor_value=str(cursor or 0),
            high_watermark=str(latest),
            status="idle",
        )
        return {
            "ok": True,
            "chain": "bitcoin",
            "latest": latest,
            "blocksRead": 0,
            "transactionsRead": 0,
            "rowsWritten": 0,
        }

    rows_written = 0
    tx_seen = 0
    last_height = cursor or 0
    for height in range(start, end + 1):
        block_hash = _bitcoin_rpc("getblockhash", [height])
        block = _bitcoin_rpc("getblock", [block_hash, 1])
        txs = block.get("tx") or []
        if not _write_head_blocks():
            last_height = height
            continue
        rows_written += _insert_block(
            {
                "vertex_id": f"blockchain:bitcoin-mainnet:block:{height}:{block_hash}",
                "chain": "bitcoin-mainnet",
                "source_id": source_id,
                "height": height,
                "block_hash": block_hash,
                "parent_hash": block.get("previousblockhash") or "",
                "block_time": str(block.get("time") or ""),
                "tx_count": len(txs),
                "run_id": run_id,
                "raw": block,
            }
        )
        tx_limit = max(0, int(os.environ.get("BLOCKCHAIN_INGEST_MAX_TX_PER_BLOCK", "0")))
        for idx, tx_hash in enumerate(txs[:tx_limit] if tx_limit else []):
            tx_seen += 1
            rows_written += _insert_tx(
                {
                    "vertex_id": f"blockchain:bitcoin-mainnet:tx:{tx_hash}",
                    "chain": "bitcoin-mainnet",
                    "source_id": source_id,
                    "block_hash": block_hash,
                    "block_height": height,
                    "tx_hash": tx_hash,
                    "tx_index": idx,
                    "run_id": run_id,
                    "raw": {"txid": tx_hash},
                }
            )
        last_height = height

    upsert_cursor(
        ingest_family="blockchain",
        source_id=source_id,
        shard_key="head",
        cursor_value=str(last_height),
        high_watermark=str(latest),
        content_hash=info.get("bestblockhash"),
        status="running" if bool(info.get("initialblockdownload")) else "synced",
    )
    return {
        "ok": True,
        "chain": "bitcoin",
        "latest": latest,
        "fromHeight": start,
        "toHeight": last_height,
        "blocksRead": max(0, end - start + 1),
        "transactionsRead": tx_seen,
        "rowsWritten": rows_written,
        "initialBlockDownload": bool(info.get("initialblockdownload")),
        "catchupSkipped": catchup_skipped,
        "txLimitPerBlock": max(0, int(os.environ.get("BLOCKCHAIN_INGEST_MAX_TX_PER_BLOCK", "0"))),
        "headBlocksWritten": _write_head_blocks(),
    }


def _hex_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    return int(str(value), 16)


def _write_head_blocks() -> bool:
    return os.environ.get("BLOCKCHAIN_HEAD_WRITE_BLOCKS", "1").lower() in ("1", "true", "on", "yes")


def ingest_ethereum_head(*, run_id: str, source_id: str, max_blocks: int) -> dict[str, Any]:
    latest = _hex_int(_ethereum_rpc("eth_blockNumber"))
    syncing = _ethereum_rpc("eth_syncing")
    cursor = _get_cursor_height(source_id)
    if latest <= 0:
        upsert_cursor(
            ingest_family="blockchain",
            source_id=source_id,
            shard_key="head",
            cursor_value=str(cursor or 0),
            high_watermark=str(latest),
            status="syncing",
        )
        return {
            "ok": True,
            "chain": "ethereum",
            "latest": latest,
            "blocksRead": 0,
            "transactionsRead": 0,
            "rowsWritten": 0,
            "syncing": bool(syncing),
        }

    catchup_skipped = False
    if cursor is None:
        start = max(0, latest - max_blocks + 1)
    elif latest - cursor > max(1, int(os.environ.get("BLOCKCHAIN_MAX_CATCHUP_LAG_BLOCKS", "100"))):
        start = max(0, latest - max_blocks + 1)
        catchup_skipped = True
    else:
        start = cursor + 1
    end = min(latest, start + max_blocks - 1)
    if start > end:
        upsert_cursor(
            ingest_family="blockchain",
            source_id=source_id,
            shard_key="head",
            cursor_value=str(cursor or latest),
            high_watermark=str(latest),
            status="idle",
        )
        return {
            "ok": True,
            "chain": "ethereum",
            "latest": latest,
            "blocksRead": 0,
            "transactionsRead": 0,
            "rowsWritten": 0,
            "syncing": bool(syncing),
        }

    rows_written = 0
    tx_seen = 0
    last_height = cursor or 0
    for height in range(start, end + 1):
        block = _ethereum_rpc("eth_getBlockByNumber", [hex(height), True])
        if not block:
            break
        block_hash = str(block.get("hash") or "")
        txs = block.get("transactions") or []
        if not _write_head_blocks():
            last_height = height
            continue
        rows_written += _insert_block(
            {
                "vertex_id": f"blockchain:ethereum-mainnet:block:{height}:{block_hash}",
                "chain": "ethereum-mainnet",
                "source_id": source_id,
                "height": height,
                "block_hash": block_hash,
                "parent_hash": str(block.get("parentHash") or ""),
                "block_time": str(_hex_int(block.get("timestamp"))),
                "tx_count": len(txs),
                "run_id": run_id,
                "raw": block,
            }
        )
        tx_limit = max(0, int(os.environ.get("BLOCKCHAIN_INGEST_MAX_TX_PER_BLOCK", "0")))
        for idx, tx in enumerate(txs[:tx_limit] if tx_limit else []):
            tx_hash = str(tx.get("hash") or "")
            if not tx_hash:
                continue
            tx_seen += 1
            rows_written += _insert_tx(
                {
                    "vertex_id": f"blockchain:ethereum-mainnet:tx:{tx_hash}",
                    "chain": "ethereum-mainnet",
                    "source_id": source_id,
                    "block_hash": block_hash,
                    "block_height": height,
                    "tx_hash": tx_hash,
                    "tx_index": _hex_int(tx.get("transactionIndex")) if tx.get("transactionIndex") is not None else idx,
                    "from_addr": str(tx.get("from") or ""),
                    "to_addr": str(tx.get("to") or ""),
                    "value_wei": str(_hex_int(tx.get("value"))),
                    "run_id": run_id,
                    "raw": tx,
                }
            )
        last_height = height

    upsert_cursor(
        ingest_family="blockchain",
        source_id=source_id,
        shard_key="head",
        cursor_value=str(last_height),
        high_watermark=str(latest),
        status="syncing" if syncing else "synced",
    )
    return {
        "ok": True,
        "chain": "ethereum",
        "latest": latest,
        "fromHeight": start,
        "toHeight": last_height,
        "blocksRead": max(0, last_height - start + 1),
        "transactionsRead": tx_seen,
        "rowsWritten": rows_written,
        "syncing": syncing,
        "catchupSkipped": catchup_skipped,
        "txLimitPerBlock": max(0, int(os.environ.get("BLOCKCHAIN_INGEST_MAX_TX_PER_BLOCK", "0"))),
        "headBlocksWritten": _write_head_blocks(),
    }


def ingest_head_delta(
    *,
    run_id: str,
    source_id: str,
    input_json: str | None = None,
    max_blocks: int | None = None,
) -> dict[str, Any]:
    try:
        payload = json.loads(input_json or "{}")
        if not isinstance(payload, dict):
            payload = {}
    except json.JSONDecodeError:
        payload = {}
    resolved_max = int(max_blocks or payload.get("maxBlocks") or os.environ.get("BLOCKCHAIN_INGEST_MAX_BLOCKS", "3"))
    resolved_max = max(1, min(resolved_max, 25))
    started = time.monotonic()
    if source_id == "bitcoin-mainnet":
        out = ingest_bitcoin_head(run_id=run_id, source_id=source_id, max_blocks=resolved_max)
    elif source_id == "ethereum-mainnet":
        out = ingest_ethereum_head(run_id=run_id, source_id=source_id, max_blocks=resolved_max)
    else:
        raise ValueError(f"unsupported blockchain source_id: {source_id}")
    out["latencyMs"] = int((time.monotonic() - started) * 1000)
    return out
