"""Canonical docs method handlers (ai.etzhayyim.apps.docs.*).

Storage-agnostic (takes a :class:`lg_docs.store.DocStore`). The docs-compat worker
reshapes results into Google Docs v1 JSON (structural) and Microsoft Graph Word
content (flattened plaintext — Microsoft has no GA structural Docs API). The
``revisionId`` (writeControl/ETag) guards batchUpdate concurrency.
"""

from __future__ import annotations

import time
from typing import Any

from . import docbody, ids, mapping
from .store import DocStore


def _now_ms() -> int:
    return int(time.time() * 1000)


def _rev(n: int) -> str:
    return f"rev-{n}"


async def _resolve(store: DocStore, document_id: str | None):
    slug = ids.resolve_slug(document_id or "")
    if slug:
        attrs = await store.get_doc_attrs(slug)
        if attrs:
            return slug, attrs
    for attr in ("doc/googleDocumentId", "doc/msDriveItemId"):
        if not document_id:
            break
        found = await store.lookup_slug(attr, document_id)
        if found:
            attrs = await store.get_doc_attrs(found)
            if attrs:
                return found, attrs
    return None, None


def _rev_num(attrs: dict[str, Any]) -> int:
    rid = attrs.get("doc/revisionId", "rev-0")
    try:
        return int(str(rid).split("-", 1)[1])
    except (IndexError, ValueError):
        return 0


# ── documentsCreate ───────────────────────────────────────────────────────────


async def documents_create(store: DocStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug = ids.new_slug()
    now = _now_ms()
    body = []
    for el in inp.get("body", []) or []:
        item: dict[str, Any] = {
            "elementId": el.get("elementId") or ids.new_element_id(),
            "kind": el.get("kind", "paragraph"),
            "text": el.get("text", ""),
        }
        if el.get("headingLevel") is not None:
            item["headingLevel"] = el["headingLevel"]
        body.append(item)
    doc: dict[str, Any] = {"title": inp["title"], "revisionId": _rev(0), "createdAtMs": now, "updatedAtMs": now, "body": body}
    for opt in ("ownerDid", "googleDocumentId", "msDriveItemId"):
        if inp.get(opt) is not None:
            doc[opt] = inp[opt]
    await store.write_ops(mapping.create_ops(slug, doc))
    attrs = await store.get_doc_attrs(slug) or {}
    return {"documentId": slug, "document": _document_view(attrs)}


def _document_view(attrs: dict[str, Any]) -> dict[str, Any]:
    doc = mapping.attrs_to_document_meta(attrs)
    doc["body"] = docbody.with_indices(mapping.attrs_to_raw_body(attrs))
    return doc


# ── documentsGet ──────────────────────────────────────────────────────────────


async def documents_get(store: DocStore, params: dict[str, Any]) -> dict[str, Any]:
    _slug, attrs = await _resolve(store, params.get("documentId"))
    if not attrs:
        return {"found": False}
    return {"found": True, "document": _document_view(attrs)}


# ── documentsBatchUpdate ──────────────────────────────────────────────────────


async def documents_batch_update(store: DocStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, inp.get("documentId"))
    if not attrs:
        return {"ok": False, "notFound": True}
    if inp.get("requiredRevisionId") is not None and attrs.get("doc/revisionId") != inp["requiredRevisionId"]:
        return {"ok": False, "conflict": True}

    body = mapping.attrs_to_raw_body(attrs)
    requests = inp.get("requests", []) or []
    for req in requests:
        docbody.apply_request(body, req)

    new_rev = _rev(_rev_num(attrs) + 1)
    await store.write_ops(mapping.update_ops(slug, attrs, {"body": body, "revisionId": new_rev, "updatedAtMs": _now_ms()}))
    return {"ok": True, "applied": len(requests), "revisionId": new_rev}
