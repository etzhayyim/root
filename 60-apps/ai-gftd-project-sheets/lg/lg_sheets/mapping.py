"""Canonical spreadsheet <-> :sheet/* datom mapping (ADR-2606010500 D6).

One spreadsheet = one datomic entity ``sheet:book:{slug}``. Worksheet metadata is
a JSON list (``:sheet/sheetsJson``); cell values are a JSON object keyed by
worksheet title (``:sheet/gridJson`` = ``{title: [[stringified cells]]}``), honoring
the no-float rule (cells are strings, cast at the edge per valueRenderOption).
"""

from __future__ import annotations

import json
from typing import Any

from . import ids
from .edn import tx_add, tx_retract

SCALAR_FIELDS: dict[str, str] = {
    "googleSpreadsheetId": "sheet/googleSpreadsheetId",
    "msDriveItemId": "sheet/msDriveItemId",
    "title": "sheet/title",
    "ownerDid": "sheet/ownerDid",
    "createdAtMs": "sheet/createdAtMs",
    "updatedAtMs": "sheet/updatedAtMs",
    "revision": "sheet/revision",
}
JSON_FIELDS = {"sheets": "sheet/sheetsJson", "grid": "sheet/gridJson"}
DEFAULTS = {"revision": 0}


def _dumps(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def create_ops(slug: str, book: dict[str, Any]) -> list[list[Any]]:
    eid = ids.eid_for_slug(slug)
    ops: list[list[Any]] = [
        tx_add(eid, "sheet/type", "Spreadsheet"),
        tx_add(eid, "sheet/id", eid),
        tx_add(eid, "sheet/slug", slug),
    ]
    for field, attr in SCALAR_FIELDS.items():
        v = book.get(field, DEFAULTS.get(field))
        if v is not None:
            ops.append(tx_add(eid, attr, v))
    for field, attr in JSON_FIELDS.items():
        if book.get(field) is not None:
            ops.append(tx_add(eid, attr, _dumps(book[field])))
    return ops


def update_ops(slug: str, current_attrs: dict[str, Any], patch: dict[str, Any]) -> list[list[Any]]:
    eid = ids.eid_for_slug(slug)
    ops: list[list[Any]] = []
    for field, attr in SCALAR_FIELDS.items():
        if field not in patch:
            continue
        new_v, old_v = patch[field], current_attrs.get(attr)
        if old_v == new_v:
            continue
        if old_v is not None:
            ops.append(tx_retract(eid, attr, old_v))
        if new_v is not None:
            ops.append(tx_add(eid, attr, new_v))
    for field, attr in JSON_FIELDS.items():
        if field not in patch:
            continue
        new_json = _dumps(patch[field])
        old_json = current_attrs.get(attr)
        if old_json == new_json:
            continue
        if old_json is not None:
            ops.append(tx_retract(eid, attr, old_json))
        ops.append(tx_add(eid, attr, new_json))
    return ops


def _loads(raw: Any, default: Any) -> Any:
    if raw is None:
        return default
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default


def attrs_to_book(attrs: dict[str, Any]) -> dict[str, Any]:
    """Spreadsheet metadata (no grid) — for spreadsheetsGet/Create responses."""
    slug = attrs.get("sheet/slug") or ids.slug_from_eid(attrs.get("sheet/id", "sheet:book:unknown"))
    book: dict[str, Any] = {"spreadsheetId": slug}
    for field, attr in SCALAR_FIELDS.items():
        if attr in attrs and attrs[attr] is not None:
            book[field] = attrs[attr]
    book["sheets"] = _loads(attrs.get("sheet/sheetsJson"), [])
    book.setdefault("revision", DEFAULTS["revision"])
    return book


def attrs_to_grid(attrs: dict[str, Any]) -> dict[str, list[list[str]]]:
    return _loads(attrs.get("sheet/gridJson"), {})
