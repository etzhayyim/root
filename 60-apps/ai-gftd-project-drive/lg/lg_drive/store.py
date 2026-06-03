"""Drive persistence stores.

``DriveStore`` is the narrow interface the handlers use. Two implementations:

- ``KotobaDriveStore`` — production, backed by kotoba datomic (graph
  ``drive-v1``) via :class:`lg_calendar.kotoba_datomic.KotobaDatomic`.
- ``FakeDriveStore`` — in-memory dict, used by the unit/smoke tests so the
  canonical handler logic is verified deterministically without a live pod.

Both speak the same EDN tx-op vocabulary (``[:db/add ...]`` / ``[:db/retract ...]``
/ ``[:db.fn/retractEntity ...]``), so the handlers are storage-agnostic.
"""

from __future__ import annotations

import copy
from typing import Any, Protocol

from . import ids
from .edn import encode
from .kotoba_datomic import KotobaDatomic


class DriveStore(Protocol):
    async def get_file_attrs(self, slug: str) -> dict[str, Any] | None: ...
    async def all_file_attrs(self) -> list[dict[str, Any]]: ...
    async def lookup_slug(self, attr: str, value: Any) -> str | None: ...
    async def write_ops(self, ops: list[list[Any]]) -> None: ...


# ── kotoba datomic implementation ─────────────────────────────────────────────


class KotobaDriveStore:
    def __init__(self, dm: KotobaDatomic) -> None:
        self._dm = dm

    async def get_file_attrs(self, slug: str) -> dict[str, Any] | None:
        return await self._dm.pull(ids.eid_for_slug(slug))

    async def all_file_attrs(self) -> list[dict[str, Any]]:
        rows = await self._dm.q('[:find ?slug :where [?e :drive/type "File"] [?e :drive/slug ?slug]]')
        out: list[dict[str, Any]] = []
        for row in rows:
            if not row:
                continue
            attrs = await self.get_file_attrs(str(row[0]))
            if attrs:
                out.append(attrs)
        return out

    async def lookup_slug(self, attr: str, value: Any) -> str | None:
        # Inline the EDN-encoded value into the query (proven yatabase get_entity
        # pattern: `[?e :kg/qid "{qid}"]`), rather than an `:in $ ?v` binding.
        bare = attr[1:] if attr.startswith(":") else attr
        query = f"[:find ?slug :where [?e :{bare} {encode(value)}] [?e :drive/slug ?slug]]"
        rows = await self._dm.q(query)
        return str(rows[0][0]) if rows and rows[0] else None

    async def write_ops(self, ops: list[list[Any]]) -> None:
        if ops:
            await self._dm.transact(ops)


# ── in-memory fake (tests) ────────────────────────────────────────────────────


class FakeDriveStore:
    """Dict-backed store keyed by slug → ``{cal/*: value}`` attr map."""

    def __init__(self) -> None:
        self._db: dict[str, dict[str, Any]] = {}

    async def get_file_attrs(self, slug: str) -> dict[str, Any] | None:
        attrs = self._db.get(slug)
        return copy.deepcopy(attrs) if attrs else None

    async def all_file_attrs(self) -> list[dict[str, Any]]:
        return [copy.deepcopy(a) for a in self._db.values()]

    async def lookup_slug(self, attr: str, value: Any) -> str | None:
        bare = attr[1:] if attr.startswith(":") else attr
        for slug, attrs in self._db.items():
            if attrs.get(bare) == value:
                return slug
        return None

    async def write_ops(self, ops: list[list[Any]]) -> None:
        for op in ops:
            kind = str(op[0])
            if kind == ":db.fn/retractEntity":
                eid = op[1]
                slug = ids.slug_from_eid(str(eid))
                self._db.pop(slug, None)
                continue
            eid, attr, value = op[1], str(op[2]), op[3]
            bare = attr[1:] if attr.startswith(":") else attr
            slug = ids.slug_from_eid(str(eid))
            row = self._db.setdefault(slug, {})
            if kind == ":db/add":
                row[bare] = value
            elif kind == ":db/retract":
                if row.get(bare) == value:
                    row.pop(bare, None)
