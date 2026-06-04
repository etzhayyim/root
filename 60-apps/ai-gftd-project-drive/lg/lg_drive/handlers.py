"""Canonical drive method handlers (ai.gftd.apps.drive.*).

Storage-agnostic (takes a :class:`lg_drive.store.DriveStore`). The drive-compat
worker reshapes results into Google Drive v3 / Microsoft Graph (OneDrive) JSON;
these handlers are the SSoT for behavior (concurrency, not-found, pagination,
the change feed). Binary content is NOT handled here — it goes through the PDS
content-addressed blob layer; ``sha256`` links the metadata entity to the blob.
"""

from __future__ import annotations

import base64
import time
from typing import Any

from . import ids, mapping
from .edn import tx_retract_entity
from .store import DriveStore


def _now_ms() -> int:
    return int(time.time() * 1000)


async def _resolve(store: DriveStore, file_id: str | None):
    slug = ids.resolve_slug(file_id or "")
    if slug:
        attrs = await store.get_file_attrs(slug)
        if attrs:
            return slug, attrs
    for attr in ("drive/googleFileId", "drive/msDriveItemId", "drive/sha256"):
        if not file_id:
            break
        found = await store.lookup_slug(attr, file_id)
        if found:
            attrs = await store.get_file_attrs(found)
            if attrs:
                return found, attrs
    return None, None


# ── filesCreate ───────────────────────────────────────────────────────────────


async def files_create(store: DriveStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug = ids.new_slug()
    now = _now_ms()
    f: dict[str, Any] = {
        "name": inp["name"],
        "parentId": inp.get("parentId", "root"),
        "isFolder": bool(inp.get("isFolder", False)),
        "trashed": False,
        "starred": False,
        "version": 0,
        "createdAtMs": now,
        "updatedAtMs": now,
    }
    for opt in ("mimeType", "sizeBytes", "sha256", "googleFileId", "msDriveItemId", "ownerDid", "webUrl", "downloadUrl"):
        if inp.get(opt) is not None:
            f[opt] = inp[opt]
    await store.write_ops(mapping.create_ops(slug, f))
    f["fileId"] = slug
    return {"fileId": slug, "file": mapping.attrs_to_file({**_to_attrs(f), "drive/slug": slug})}


def _to_attrs(f: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field, attr in mapping.SCALAR_FIELDS.items():
        if f.get(field) is not None:
            out[attr] = f[field]
    return out


# ── filesGet ──────────────────────────────────────────────────────────────────


async def files_get(store: DriveStore, params: dict[str, Any]) -> dict[str, Any]:
    _slug, attrs = await _resolve(store, params.get("fileId"))
    if not attrs:
        return {"found": False}
    return {"found": True, "file": mapping.attrs_to_file(attrs)}


# ── filesList ─────────────────────────────────────────────────────────────────


async def files_list(store: DriveStore, params: dict[str, Any]) -> dict[str, Any]:
    parent_id = params.get("parentId")
    q = params.get("q")
    include_trashed = str(params.get("includeTrashed", "false")).lower() == "true"
    order_by = params.get("orderBy", "name")
    offset = int(params.get("offset", 0))
    limit = int(params.get("limit", 100))

    files = [mapping.attrs_to_file(a) for a in await store.all_file_attrs()]

    def keep(f: dict[str, Any]) -> bool:
        if parent_id and f.get("parentId", "root") != parent_id:
            return False
        if not include_trashed and f.get("trashed"):
            return False
        if q:
            name = (f.get("name") or "").lower()
            if not (q.lower() == name or name.startswith(q.lower())):
                return False
        return True

    filtered = [f for f in files if keep(f)]
    key = {"updatedAtMs": "updatedAtMs", "sizeBytes": "sizeBytes"}.get(order_by, "name")
    filtered.sort(key=lambda f: (f.get(key) is None, f.get(key)))
    page = filtered[offset:offset + limit]
    return {"files": page, "total": len(filtered), "offset": offset, "limit": limit}


# ── filesUpdate ───────────────────────────────────────────────────────────────


async def files_update(store: DriveStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, inp.get("fileId"))
    if not attrs:
        return {"ok": False, "notFound": True}
    if "ifVersion" in inp and inp["ifVersion"] is not None:
        if attrs.get("drive/version") != inp["ifVersion"]:
            return {"ok": False, "conflict": True}
    patch: dict[str, Any] = {}
    for f in ("name", "parentId", "trashed", "starred"):
        if f in inp and inp[f] is not None:
            patch[f] = inp[f]
    patch["version"] = int(attrs.get("drive/version", 0)) + 1
    patch["updatedAtMs"] = _now_ms()
    await store.write_ops(mapping.update_ops(slug, attrs, patch))
    new_attrs = await store.get_file_attrs(slug) or attrs
    return {"ok": True, "file": mapping.attrs_to_file(new_attrs)}


# ── filesDelete ───────────────────────────────────────────────────────────────


async def files_delete(store: DriveStore, inp: dict[str, Any]) -> dict[str, Any]:
    slug, attrs = await _resolve(store, inp.get("fileId"))
    if not attrs:
        return {"ok": False, "notFound": True}
    if "ifVersion" in inp and inp["ifVersion"] is not None:
        if attrs.get("drive/version") != inp["ifVersion"]:
            return {"ok": False, "conflict": True}
    await store.write_ops([tx_retract_entity(ids.eid_for_slug(slug))])
    return {"ok": True}


# ── about ─────────────────────────────────────────────────────────────────────


async def about(store: DriveStore, params: dict[str, Any]) -> dict[str, Any]:
    files = await store.all_file_attrs()
    used = sum(int(a.get("drive/sizeBytes", 0) or 0) for a in files)
    return {"about": {
        "ownerDid": params.get("ownerDid", ""),
        "quotaTotalBytes": 0,
        "quotaUsedBytes": used,
    }}


# ── changes ───────────────────────────────────────────────────────────────────


async def changes(store: DriveStore, params: dict[str, Any]) -> dict[str, Any]:
    since = _decode_token(params.get("pageToken"))
    limit = int(params.get("limit", 100))
    files = [mapping.attrs_to_file(a) for a in await store.all_file_attrs()]
    changed = sorted(
        [f for f in files if int(f.get("updatedAtMs", 0) or 0) > since],
        key=lambda f: int(f.get("updatedAtMs", 0) or 0),
    )
    page = changed[:limit]
    high = max([int(f.get("updatedAtMs", 0) or 0) for f in page], default=since)
    out = [{"fileId": f["fileId"], "removed": False, "atMs": f.get("updatedAtMs"), "file": f} for f in page]
    return {"changes": out, "newStartPageToken": _encode_token(high), "hasMore": len(changed) > limit}


def _encode_token(ms: int) -> str:
    return base64.urlsafe_b64encode(f"t:{ms}".encode()).decode().rstrip("=")


def _decode_token(token: str | None) -> int:
    if not token:
        return 0
    try:
        pad = token + "=" * (-len(token) % 4)
        s = base64.urlsafe_b64decode(pad).decode()
        return int(s.split(":", 1)[1]) if s.startswith("t:") else 0
    except (ValueError, IndexError):
        return 0
