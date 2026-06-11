"""Canonical file <-> :drive/* datom mapping (ADR-2606010500 D4).

A canonical file is the ``ai.etzhayyim.apps.drive.defs#file`` shape. In datomic it is
one entity ``drive:file:{slug}`` with ``:drive/*`` attributes. Join key
``:drive/sha256`` (Google sha256Checksum == Microsoft file.hashes.sha256Hash).
"""

from __future__ import annotations

from typing import Any

from . import ids
from .edn import tx_add, tx_retract

SCALAR_FIELDS: dict[str, str] = {
    "googleFileId": "drive/googleFileId",
    "msDriveItemId": "drive/msDriveItemId",
    "name": "drive/name",
    "mimeType": "drive/mimeType",
    "isFolder": "drive/isFolder",
    "parentId": "drive/parentId",
    "sizeBytes": "drive/sizeBytes",
    "sha256": "drive/sha256",
    "webUrl": "drive/webUrl",
    "downloadUrl": "drive/downloadUrl",
    "createdAtMs": "drive/createdAtMs",
    "updatedAtMs": "drive/updatedAtMs",
    "trashed": "drive/trashed",
    "ownerDid": "drive/ownerDid",
    "starred": "drive/starred",
    "version": "drive/version",
}
DEFAULTS = {"isFolder": False, "trashed": False, "starred": False, "version": 0, "parentId": "root"}


def create_ops(slug: str, file: dict[str, Any]) -> list[list[Any]]:
    eid = ids.eid_for_slug(slug)
    ops: list[list[Any]] = [
        tx_add(eid, "drive/type", "File"),
        tx_add(eid, "drive/id", eid),
        tx_add(eid, "drive/slug", slug),
    ]
    for field, attr in SCALAR_FIELDS.items():
        v = file.get(field, DEFAULTS.get(field))
        if v is not None:
            ops.append(tx_add(eid, attr, v))
    return ops


def update_ops(slug: str, current_attrs: dict[str, Any], patch: dict[str, Any]) -> list[list[Any]]:
    eid = ids.eid_for_slug(slug)
    ops: list[list[Any]] = []
    for field, attr in SCALAR_FIELDS.items():
        if field not in patch:
            continue
        new_v = patch[field]
        old_v = current_attrs.get(attr)
        if old_v == new_v:
            continue
        if old_v is not None:
            ops.append(tx_retract(eid, attr, old_v))
        if new_v is not None:
            ops.append(tx_add(eid, attr, new_v))
    return ops


def attrs_to_file(attrs: dict[str, Any]) -> dict[str, Any]:
    slug = attrs.get("drive/slug") or ids.slug_from_eid(attrs.get("drive/id", "drive:file:unknown"))
    f: dict[str, Any] = {"fileId": slug}
    for field, attr in SCALAR_FIELDS.items():
        if attr in attrs and attrs[attr] is not None:
            f[field] = attrs[attr]
    f.setdefault("isFolder", DEFAULTS["isFolder"])
    f.setdefault("trashed", DEFAULTS["trashed"])
    f.setdefault("version", DEFAULTS["version"])
    return f
