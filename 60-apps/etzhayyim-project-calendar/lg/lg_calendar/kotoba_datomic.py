"""kotoba datomic XRPC client for lg-calendar.

Wraps ``ai.etzhayyim.apps.kotoba.datomic.{transact,q,pull}`` — the canonical
write/read surface for calendar events (graph ``calendar-v1``). Adapted from
the proven hakken/yatabase clients.

Endpoint resolution honors the in-cluster deployment var ``KOTOBA_URL``
(default kotoba Service ``:8080``) so writes reach the in-cluster service rather
than silently hitting the public host. Auth = Bearer JWT (``KOTOBA_BEARER``);
``KOTOBA_DEFAULT_VISIBILITY=authenticated`` on the kotoba pod keeps the
dedicated ``calendar-v1`` graph JWT-only (no CACAO) per ADR-2605302130 Option 3.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
from typing import Any

import httpx

from .edn import encode_tx_data, parse_edn_value

KOTOBA_XRPC = (
    os.environ.get("KOTOBA_XRPC_URL")
    or os.environ.get("KOTOBA_URL")
    or "http://kotoba.kotoba.svc.cluster.local:8080"
).rstrip("/")
KOTOBA_BEARER = os.environ.get("KOTOBA_BEARER", "")


def kotoba_cid(payload: bytes) -> str:
    digest = hashlib.sha256(payload).digest()
    cid = bytes((0x01, 0x71, 0x12, 0x20)) + digest
    return "b" + base64.b32encode(cid).rstrip(b"=").decode("ascii").lower()


def graph_cid_for_label(label: str) -> str:
    """Stable kotoba graph CID from a human-readable label (multibase passthrough)."""
    if label.startswith("b") and re.fullmatch(r"b[a-z2-7]{58,80}", label):
        return label
    return kotoba_cid(label.encode("utf-8"))


_GRAPH_LABEL = os.environ.get("KOTOBA_GRAPH", "calendar-v1")
DEFAULT_GRAPH = graph_cid_for_label(_GRAPH_LABEL)


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {KOTOBA_BEARER}"} if KOTOBA_BEARER else {}


class KotobaDatomic:
    """Thin async wrapper over the three datomic XRPC methods used by calendar."""

    def __init__(self, client: httpx.AsyncClient, *, graph: str = DEFAULT_GRAPH) -> None:
        self._c = client
        self._graph = graph

    async def transact(self, ops: list[list[Any]], *, expected_parent: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"graph": self._graph, "tx_edn": encode_tx_data(ops)}
        if expected_parent:
            body["expected_parent"] = expected_parent
        resp = await self._c.post(
            f"{KOTOBA_XRPC}/xrpc/ai.etzhayyim.apps.kotoba.datomic.transact",
            headers=_headers(),
            json=body,
        )
        resp.raise_for_status()
        return resp.json()

    async def q(self, query_edn: str, inputs_edn: list[str] | None = None) -> list[list[Any]]:
        body: dict[str, Any] = {"graph": self._graph, "query_edn": query_edn}
        if inputs_edn:
            body["inputs_edn"] = inputs_edn
        resp = await self._c.post(
            f"{KOTOBA_XRPC}/xrpc/ai.etzhayyim.apps.kotoba.datomic.q",
            headers=_headers(),
            json=body,
        )
        resp.raise_for_status()
        rows = resp.json().get("rows_edn", []) or []
        return [[parse_edn_value(c) for c in row] for row in rows]

    async def pull(self, entity: str) -> dict[str, Any] | None:
        """Return the entity as a flat ``{bare_attr: value}`` dict, or None on miss.

        Mirrors the live-verified yatabase read path
        (``lg_yatabase/kotoba_datomic.py`` ``_datoms_to_entity``): kotoba's
        ``datomic.pull`` returns a ``datoms`` list where each datom is a dict with
        ``a`` (attribute, leading ``:``), ``v_edn`` (EDN-encoded value string), and
        ``added`` (bool). We decode ``v_edn`` and fold added datoms into a plain
        dict keyed by the bare attribute (``cal/summary``).
        """
        body = {"graph": self._graph, "entity": entity}
        resp = await self._c.post(
            f"{KOTOBA_XRPC}/xrpc/ai.etzhayyim.apps.kotoba.datomic.pull",
            headers=_headers(),
            json=body,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return datoms_to_attr_map(resp.json().get("datoms") or [])


def datoms_to_attr_map(datoms: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Fold pull datoms (``{a, v_edn, added}``) into ``{bare_attr: value}``.

    Matches the proven yatabase ``_datoms_to_entity`` shape exactly: attribute
    under ``a`` (with leading colon), EDN-encoded value under ``v_edn``, retractions
    flagged ``added: false``.
    """
    if not datoms:
        return None
    out: dict[str, Any] = {}
    for d in datoms:
        if not isinstance(d, dict) or d.get("added") is False:
            continue
        a = d.get("a")
        if not a:
            continue
        out[_bare_attr(a)] = parse_edn_value(d.get("v_edn", ""))
    return out or None


def _bare_attr(a: Any) -> str:
    """':cal/summary' -> 'cal/summary'."""
    s = str(a)
    return s[1:] if s.startswith(":") else s
