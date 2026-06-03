"""Canonical document <-> :doc/* datom mapping (ADR-2606010500 D5).

One document = one datomic entity ``doc:doc:{slug}``. Body is an ordered list of
structural elements stored as JSON (``:doc/bodyJson``). ``:doc/revisionId`` is the
writeControl/ETag token.
"""

from __future__ import annotations

import json
from typing import Any

from . import ids
from .edn import tx_add, tx_retract

SCALAR_FIELDS: dict[str, str] = {
    "googleDocumentId": "doc/googleDocumentId",
    "msDriveItemId": "doc/msDriveItemId",
    "title": "doc/title",
    "revisionId": "doc/revisionId",
    "ownerDid": "doc/ownerDid",
    "createdAtMs": "doc/createdAtMs",
    "updatedAtMs": "doc/updatedAtMs",
}
JSON_FIELDS = {"body": "doc/bodyJson"}


def _dumps(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"))


def create_ops(slug: str, doc: dict[str, Any]) -> list[list[Any]]:
    eid = ids.eid_for_slug(slug)
    ops: list[list[Any]] = [
        tx_add(eid, "doc/type", "Document"),
        tx_add(eid, "doc/id", eid),
        tx_add(eid, "doc/slug", slug),
    ]
    for field, attr in SCALAR_FIELDS.items():
        if doc.get(field) is not None:
            ops.append(tx_add(eid, attr, doc[field]))
    for field, attr in JSON_FIELDS.items():
        ops.append(tx_add(eid, attr, _dumps(doc.get(field) or [])))
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
        new_json = _dumps(patch[field] or [])
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


def attrs_to_raw_body(attrs: dict[str, Any]) -> list[dict[str, Any]]:
    return _loads(attrs.get("doc/bodyJson"), [])


def attrs_to_document_meta(attrs: dict[str, Any]) -> dict[str, Any]:
    """Document metadata WITHOUT body (handler attaches indexed body)."""
    slug = attrs.get("doc/slug") or ids.slug_from_eid(attrs.get("doc/id", "doc:doc:unknown"))
    doc: dict[str, Any] = {"documentId": slug}
    for field, attr in SCALAR_FIELDS.items():
        if attr in attrs and attrs[attr] is not None:
            doc[field] = attrs[attr]
    return doc
