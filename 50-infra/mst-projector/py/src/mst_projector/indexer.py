"""indexer — LanceDB write path for MST commit events.

Receives decoded commit ops from subscriber.py and writes them into
per-collection LanceDB tables.  Each table schema is:

  did        : str     — repo DID that authored the record
  rkey       : str     — record key within the collection
  record_cid : str     — CID of the record in the AT Protocol commit
  indexed_at : str     — ISO 8601 UTC timestamp of when this was indexed
  record_json: str     — full record value as JSON blob
  <flat fields from top-level primitives in the record value>

Schema is open-ended: the indexer stores the full record value as a JSON
blob column (``record_json``) plus top-level primitive flat fields for
query efficiency.  Schema evolution (new fields) requires operator-assisted
replay from cursor=0 (no auto-migration at M1).

Storage rule (ADR-2605172000): LanceDB only — no Postgres/RW.

Design doc: 50-infra/mst-projector/README.md §Storage
ADR: ADR-2605215500 §2 (storage) + ADR-2605212000 (Phase 3 architecture)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import lancedb
import pyarrow as pa

_log = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = "/data/mst-projector"


def _data_dir() -> str:
    """LanceDB storage root.

    Defaults to /data/mst-projector/ in production, or
    ETZHAYYIM_MST_PROJECTOR_DATA_DIR env override for tests.
    """
    return os.environ.get("ETZHAYYIM_MST_PROJECTOR_DATA_DIR", _DEFAULT_DATA_DIR)


def _table_name(collection: str) -> str:
    """Convert NSID to LanceDB table name (LanceDB rejects '.' in names).

    Args:
        collection: AT Protocol collection NSID.

    Returns:
        Underscore-safe table name string.
    """
    return collection.replace(".", "_")


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string (Z suffix)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    """Flatten a record dict for LanceDB columnar storage.

    Top-level scalars (str, int, float, bool, None) stay typed.
    Nested dicts/lists are JSON-stringified into str columns.

    Args:
        record: Decoded AT Protocol record value dict.

    Returns:
        Flat dict ready for LanceDB row insertion.
    """
    flat: dict[str, Any] = {}
    for k, v in record.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            flat[k] = v
        else:
            flat[k] = json.dumps(v, ensure_ascii=False)
    return flat


def _build_schema(sample_row: dict[str, Any]) -> list[pa.Field]:
    """Build a PyArrow schema from a fully-assembled sample row.

    Base columns (did, rkey, record_cid, indexed_at, record_json) are
    always present.  Additional per-collection flat fields are appended
    using Python type → Arrow type mapping.

    Args:
        sample_row: A fully-assembled row dict (base + flat fields).

    Returns:
        List of PyArrow fields for schema creation.
    """
    _type_map: dict[type, pa.DataType] = {
        str: pa.string(),
        int: pa.int64(),
        float: pa.float64(),
        bool: pa.bool_(),
    }
    base_keys = {"did", "rkey", "record_cid", "indexed_at", "record_json"}
    fields: list[pa.Field] = [
        pa.field("did", pa.string()),
        pa.field("rkey", pa.string()),
        pa.field("record_cid", pa.string()),
        pa.field("indexed_at", pa.string()),
        pa.field("record_json", pa.string()),
    ]
    for k, v in sample_row.items():
        if k in base_keys:
            continue
        arrow_type = _type_map.get(type(v), pa.string())
        fields.append(pa.field(k, arrow_type))
    return fields


class Indexer:
    """LanceDB-backed indexed-view writer for MST records.

    Per ADR-2605215500 §1 architecture.  Tables-per-collection schema:
        did        : str   — authoring DID
        rkey       : str   — within-collection record key
        record_cid : str   — current CID
        indexed_at : str   — when this projector saw the record (ISO 8601 Z)
        record_json: str   — full record as JSON blob
        + per-collection flat fields derived from top-level primitives

    Upsert semantics: (did, rkey) is the logical primary key.
    On update ops the row is replaced.  On delete ops (MST tombstones)
    the row is removed via LanceDB delete_rows.

    Usage::

        indexer = Indexer()
        await indexer.index_op(collection, did, rkey, cid, record_value)
        await indexer.delete_op(collection, did, rkey)
        await indexer.close()
    """

    def __init__(self) -> None:
        data_dir = _data_dir()
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(data_dir)
        self._tables: dict[str, Any] = {}

    def _list_tables(self) -> list[str]:
        """Return current table names from LanceDB."""
        return self._db.table_names()

    def _table_exists(self, collection: str) -> bool:
        return _table_name(collection) in self._list_tables()

    def _get_or_create_table(
        self, collection: str, sample_row: dict[str, Any]
    ) -> Any:
        """Open or create a LanceDB table for a collection.

        Args:
            collection:  AT Protocol collection NSID.
            sample_row:  A fully-assembled row dict used to bootstrap schema
                         on first creation.

        Returns:
            lancedb Table object.
        """
        tname = _table_name(collection)
        if tname in self._tables:
            return self._tables[tname]
        if tname in self._list_tables():
            tbl = self._db.open_table(tname)
        else:
            schema = pa.schema(_build_schema(sample_row))
            tbl = self._db.create_table(tname, schema=schema, mode="overwrite")
            _log.info("indexer: created table %r for collection %r", tname, collection)
        self._tables[tname] = tbl
        return tbl

    async def index_op(
        self,
        collection: str,
        did: str,
        rkey: str,
        record_cid: str,
        record_value: dict[str, Any],
    ) -> None:
        """Write a single record op into the LanceDB index.

        Upserts by (did, rkey) primary key.  If a record with the same
        (did, rkey) already exists it is replaced (covers update ops).
        Delete ops should call ``delete_op()`` instead.

        Args:
            collection:   AT Protocol collection NSID (table routing key).
            did:          Repo DID that authored the record.
            rkey:         Record key within the collection.
            record_cid:   CID of the record in the commit.
            record_value: Decoded record value dict (CBOR-decoded payload).
        """
        flat = _flatten_record(record_value)
        row = {
            "did": did,
            "rkey": rkey,
            "record_cid": record_cid,
            "indexed_at": _now_iso(),
            "record_json": json.dumps(record_value, ensure_ascii=False),
            **flat,
        }
        tbl = self._get_or_create_table(collection, row)
        # Delete-before-upsert to maintain (did, rkey) uniqueness
        try:
            tbl.delete(f"did = '{did}' AND rkey = '{rkey}'")
        except Exception as exc:
            _log.warning(
                "indexer: delete-before-upsert failed for did=%r rkey=%r: %s",
                did,
                rkey,
                exc,
            )
        tbl.add([row])
        _log.debug(
            "indexer: indexed did=%r rkey=%r collection=%r", did, rkey, collection
        )

    async def delete_op(self, collection: str, did: str, rkey: str) -> None:
        """Remove a record from the LanceDB index (MST tombstone / delete op).

        No-op if the collection table does not exist yet (e.g. delete arrives
        before any create for that collection).

        Args:
            collection: AT Protocol collection NSID.
            did:        Repo DID that authored the record.
            rkey:       Record key to delete.
        """
        if not self._table_exists(collection):
            _log.debug(
                "indexer: delete_op no-op — table %r not yet created",
                _table_name(collection),
            )
            return
        tbl = self._get_or_create_table(
            collection, {"did": "", "rkey": "", "record_cid": "", "indexed_at": "", "record_json": ""}
        )
        tbl.delete(f"did = '{did}' AND rkey = '{rkey}'")
        _log.debug(
            "indexer: deleted did=%r rkey=%r collection=%r", did, rkey, collection
        )

    async def close(self) -> None:
        """Flush pending writes and release resources.

        LanceDB's synchronous client has no explicit close; this method
        clears the table cache and drops the connection reference so the
        GC can reclaim file handles.
        """
        self._tables.clear()
        _log.info("indexer: closed")

    async def count_rows(self, collection: str) -> int:
        """Return total row count for a collection using LanceDB native count.

        Avoids a full-scan fetch; uses LanceDB's Table.count_rows() which
        reads only metadata (O(1) on compacted tables).

        Args:
            collection: AT Protocol collection NSID.

        Returns:
            Integer row count; 0 if the collection has not been indexed yet.
        """
        name = _table_name(collection)
        if name not in self._db.table_names():
            return 0
        tbl = self._db.open_table(name)
        return tbl.count_rows()

    async def list_collections(self) -> list[str]:
        """List indexed collections (table names mapped back to NSID-ish form).

        Note: the reverse mapping (underscore → dot) is lossy for NSIDs
        that contain hyphens; this is acceptable for diagnostics.

        Returns:
            List of collection-style strings.
        """
        return [t.replace("_", ".") for t in self._list_tables()]

    async def query(
        self,
        collection: str,
        filter_sql: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query records via LanceDB where clause.

        Args:
            collection:  AT Protocol collection NSID.
            filter_sql:  SQL-style where predicate (LanceDB dialect).
            limit:       Maximum rows to return (default 100).

        Returns:
            List of row dicts.  Empty list if collection not yet indexed.
        """
        if not self._table_exists(collection):
            return []
        tbl = self._get_or_create_table(
            collection, {"did": "", "rkey": "", "record_cid": "", "indexed_at": "", "record_json": ""}
        )
        q = tbl.search().limit(limit)
        if filter_sql:
            q = q.where(filter_sql)
        try:
            df = q.to_pandas()
            return df.to_dict(orient="records")
        except Exception as exc:
            _log.warning("indexer: query failed for collection=%r: %s", collection, exc)
            return []


_singleton: Indexer | None = None


def get_indexer() -> Indexer:
    """Return the module-level singleton Indexer, creating it on first call."""
    global _singleton
    if _singleton is None:
        _singleton = Indexer()
    return _singleton
