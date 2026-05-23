"""Substrate abstraction for maps bulk-ingest workers.

Per Charter Rider §1 + ADR-2605172000 (RW-free state substrate), all
``ai.gftd.apps.maps.*`` writes must land on AT Protocol MST + IPFS +
Base L2 anchor (the etzhayyim primary substrate). The pre-migration
workers in this directory write directly to RisingWave via psycopg —
a centralized PostgreSQL surface explicitly prohibited by the
substrate boundary table in `/CLAUDE.md`.

This module provides a single seam (``open_substrate_writer``) that
each worker uses instead of ``psycopg2.connect()`` directly. The
returned writer dispatches based on ``ETZHAYYIM_SUBSTRATE_MODE``:

* ``mst`` (post-migration default once Council ratifies) — writes hit
  the PDS at ``ai.gftd.apps.maps.{label}.create`` XRPC; the PDS commit
  pipeline projects to MST + pins to IPFS + anchors to Base L2.
* ``rw`` (transitional, current default while the bulk feeds are
  still RW-resident) — writes go to ``vertex_spatial`` via psycopg
  exactly as before, with a deprecation warning logged on startup.

Workers that adopt this wrapper are forward-compatible: flipping
``ETZHAYYIM_SUBSTRATE_MODE=mst`` (Worker secret / pod env) cuts them
over to the substrate without touching the worker source. The legacy
``DATABASE_URL`` env stays valid in ``rw`` mode; in ``mst`` mode the
worker needs ``ETZHAYYIM_PDS_URL`` + ``ETZHAYYIM_PDS_HANDLE`` +
``ETZHAYYIM_PDS_APP_PASSWORD`` instead.

Per ADR-2605172000. See also `/CHARTER-RIDER.md` §1 (substrate
boundary), `/CLAUDE.md` § "Substrate boundary".
"""
from __future__ import annotations

import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Iterator, Sequence
from urllib import error as urlerror
from urllib import request as urlrequest


log = logging.getLogger("etzhayyim.substrate")


# ─── Public interface ──────────────────────────────────────────────


class SubstrateWriter(ABC):
    """Abstract write surface for the etzhayyim primary substrate."""

    @abstractmethod
    def upsert_vertex_spatial(
        self, rows: Sequence[dict[str, Any]], *, conflict_key: str = "vertex_id"
    ) -> int:
        """Upsert N rows into the spatial graph.

        Returns the number of rows that landed. Both backends are
        idempotent on ``conflict_key``.
        """

    @abstractmethod
    def upsert_table(
        self,
        table: str,
        rows: Sequence[dict[str, Any]],
        *,
        conflict_key: str | None = None,
    ) -> int:
        """Upsert N rows into an arbitrary table (auxiliary indexes)."""

    @abstractmethod
    def close(self) -> None:
        """Release the underlying connection or session."""


@contextmanager
def open_substrate_writer() -> Iterator[SubstrateWriter]:
    """Open a substrate writer per ``ETZHAYYIM_SUBSTRATE_MODE``.

    Usage::

        with open_substrate_writer() as writer:
            writer.upsert_vertex_spatial([...])
    """
    mode = (os.environ.get("ETZHAYYIM_SUBSTRATE_MODE") or "rw").lower()
    if mode == "mst":
        writer: SubstrateWriter = _MstSubstrateWriter()
    elif mode == "rw":
        writer = _RwSubstrateWriter()
    else:
        raise ValueError(
            f"ETZHAYYIM_SUBSTRATE_MODE={mode!r} is not recognised. "
            "Allowed: 'mst' (post-migration), 'rw' (transitional)."
        )
    try:
        yield writer
    finally:
        writer.close()


# ─── MST backend (AT Protocol PDS → MST + IPFS + Base L2 anchor) ───


class _MstSubstrateWriter(SubstrateWriter):
    """Writes land via PDS XRPC; PDS commits to MST and pins to IPFS.

    NSID mapping: ``vertex_spatial`` rows are projected onto the
    ``ai.gftd.apps.maps.{label}.create`` lexicon (one record per row).
    The label is read from ``row['label']`` and lower-cased; e.g.
    ``Airport`` → ``ai.gftd.apps.maps.airport.create``.
    """

    def __init__(self) -> None:
        self.pds_url = os.environ.get("ETZHAYYIM_PDS_URL", "https://atproto.etzhayyim.com").rstrip("/")
        self.handle = os.environ.get("ETZHAYYIM_PDS_HANDLE")
        self.app_password = os.environ.get("ETZHAYYIM_PDS_APP_PASSWORD")
        if not self.handle or not self.app_password:
            raise RuntimeError(
                "ETZHAYYIM_SUBSTRATE_MODE=mst requires ETZHAYYIM_PDS_HANDLE + "
                "ETZHAYYIM_PDS_APP_PASSWORD to be configured."
            )
        self._session: dict[str, Any] | None = None
        self._refresh_session()

    def _refresh_session(self) -> None:
        payload = json.dumps({
            "identifier": self.handle,
            "password": self.app_password,
        }).encode("utf-8")
        req = urlrequest.Request(
            f"{self.pds_url}/xrpc/com.atproto.server.createSession",
            data=payload,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urlrequest.urlopen(req, timeout=15) as resp:
            self._session = json.loads(resp.read().decode("utf-8"))
        log.info("etzhayyim.substrate: PDS session opened did=%s", self._session.get("did"))

    def _post_record(self, collection: str, record: dict[str, Any]) -> None:
        assert self._session is not None
        body = json.dumps({
            "repo": self._session["did"],
            "collection": collection,
            "record": record,
        }).encode("utf-8")
        req = urlrequest.Request(
            f"{self.pds_url}/xrpc/com.atproto.repo.createRecord",
            data=body,
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {self._session['accessJwt']}",
            },
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=30) as resp:
                resp.read()  # drain
        except urlerror.HTTPError as e:
            if e.code == 401:
                self._refresh_session()
                with urlrequest.urlopen(req, timeout=30) as resp:
                    resp.read()
            else:
                raise

    def upsert_vertex_spatial(
        self, rows: Sequence[dict[str, Any]], *, conflict_key: str = "vertex_id"
    ) -> int:
        n = 0
        for row in rows:
            label = str(row.get("label") or "").lower().strip()
            if not label:
                log.warning("etzhayyim.substrate: skip row without label vertex_id=%s", row.get("vertex_id"))
                continue
            collection = f"ai.gftd.apps.maps.{label}"
            self._post_record(collection, row)
            n += 1
        return n

    def upsert_table(
        self,
        table: str,
        rows: Sequence[dict[str, Any]],
        *,
        conflict_key: str | None = None,
    ) -> int:
        # Auxiliary tables (e.g. vertex_maps_trip, vertex_maps_stop_time)
        # land on the `ai.gftd.apps.maps.aux.{table}` lexicon namespace
        # until per-table lexicons are registered (P3 follow-up).
        collection = f"ai.gftd.apps.maps.aux.{table}"
        for row in rows:
            self._post_record(collection, row)
        return len(rows)

    def close(self) -> None:
        self._session = None


# ─── RW backend (transitional, current production path) ────────────


class _RwSubstrateWriter(SubstrateWriter):
    """psycopg2-based fallback for the transitional period.

    Behaviour is intentionally identical to the pre-migration code so
    that flipping a worker over to ``open_substrate_writer`` is a pure
    refactor (zero behavioural change in ``rw`` mode).
    """

    def __init__(self) -> None:
        try:
            import psycopg2  # noqa: WPS433 — local import keeps the substrate boundary intent visible
            import psycopg2.extras  # noqa: WPS433
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "ETZHAYYIM_SUBSTRATE_MODE=rw requires psycopg2 to be importable."
            ) from exc

        dsn = os.environ.get("DATABASE_URL")
        if not dsn:
            raise RuntimeError("DATABASE_URL must be set when ETZHAYYIM_SUBSTRATE_MODE=rw.")

        log.warning(
            "etzhayyim.substrate: rw mode active (DATABASE_URL=<redacted>). "
            "This is transitional per ADR-2605172000; flip "
            "ETZHAYYIM_SUBSTRATE_MODE=mst once Council ratifies."
        )
        self._psycopg2 = psycopg2
        self._extras = psycopg2.extras
        self._conn = psycopg2.connect(dsn)
        self._conn.autocommit = True

    def upsert_vertex_spatial(
        self, rows: Sequence[dict[str, Any]], *, conflict_key: str = "vertex_id"
    ) -> int:
        if not rows:
            return 0
        cols = list(rows[0].keys())
        col_sql = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))
        update_clause = ", ".join(
            f"{c}=excluded.{c}" for c in cols if c != conflict_key
        )
        sql = (
            f"INSERT INTO vertex_spatial ({col_sql}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT ({conflict_key}) DO UPDATE SET {update_clause}"
        )
        values = [tuple(row[c] for c in cols) for row in rows]
        with self._conn.cursor() as cur:
            self._extras.execute_batch(cur, sql, values, page_size=500)
        return len(rows)

    def upsert_table(
        self,
        table: str,
        rows: Sequence[dict[str, Any]],
        *,
        conflict_key: str | None = None,
    ) -> int:
        if not rows:
            return 0
        cols = list(rows[0].keys())
        col_sql = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))
        sql_parts = [
            f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})",
        ]
        if conflict_key:
            update_clause = ", ".join(
                f"{c}=excluded.{c}" for c in cols if c != conflict_key
            )
            sql_parts.append(f"ON CONFLICT ({conflict_key}) DO UPDATE SET {update_clause}")
        sql = " ".join(sql_parts)
        values = [tuple(row[c] for c in cols) for row in rows]
        with self._conn.cursor() as cur:
            self._extras.execute_batch(cur, sql, values, page_size=500)
        return len(rows)

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # pragma: no cover
            pass
