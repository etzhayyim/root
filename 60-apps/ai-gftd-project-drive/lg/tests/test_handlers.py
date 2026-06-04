"""Deterministic drive-handler tests using the in-memory FakeDriveStore.

Verifies create→read round-trip, list filtering (parent / q / trashed) +
offset/limit/total pagination, version-based optimistic concurrency, the change
feed cursor, and provider-id lookup — without a live kotoba pod.
"""

from __future__ import annotations

import pytest

from lg_drive import handlers
from lg_drive.store import FakeDriveStore


@pytest.fixture()
def store() -> FakeDriveStore:
    return FakeDriveStore()


async def test_create_get_roundtrip(store: FakeDriveStore) -> None:
    res = await handlers.files_create(store, {"name": "report.pdf", "mimeType": "application/pdf", "sizeBytes": 1234, "sha256": "abc"})
    assert res["file"]["name"] == "report.pdf"
    assert res["file"]["version"] == 0
    got = await handlers.files_get(store, {"fileId": res["fileId"]})
    assert got["found"] is True
    assert got["file"]["sizeBytes"] == 1234


async def test_get_missing(store: FakeDriveStore) -> None:
    assert await handlers.files_get(store, {"fileId": "missing000001"}) == {"found": False}


async def test_lookup_by_provider_id_and_sha(store: FakeDriveStore) -> None:
    await handlers.files_create(store, {"name": "x", "googleFileId": "gdrive_1", "sha256": "deadbeef"})
    assert (await handlers.files_get(store, {"fileId": "gdrive_1"}))["found"] is True
    assert (await handlers.files_get(store, {"fileId": "deadbeef"}))["found"] is True


async def test_list_parent_trash_pagination(store: FakeDriveStore) -> None:
    await handlers.files_create(store, {"name": "a", "parentId": "root"})
    await handlers.files_create(store, {"name": "b", "parentId": "root"})
    await handlers.files_create(store, {"name": "c", "parentId": "folder1"})
    trashed = await handlers.files_create(store, {"name": "d", "parentId": "root"})
    await handlers.files_update(store, {"fileId": trashed["fileId"], "trashed": True})

    root = await handlers.files_list(store, {"parentId": "root"})
    assert root["total"] == 2  # a, b (trashed d excluded)
    assert {f["name"] for f in root["files"]} == {"a", "b"}

    withtrash = await handlers.files_list(store, {"parentId": "root", "includeTrashed": "true"})
    assert withtrash["total"] == 3

    page = await handlers.files_list(store, {"offset": 0, "limit": 2})
    assert page["offset"] == 0 and page["limit"] == 2 and len(page["files"]) == 2

    byname = await handlers.files_list(store, {"q": "c"})
    assert {f["name"] for f in byname["files"]} == {"c"}


async def test_update_version_concurrency(store: FakeDriveStore) -> None:
    res = await handlers.files_create(store, {"name": "v0"})
    fid = res["fileId"]
    ok = await handlers.files_update(store, {"fileId": fid, "ifVersion": 0, "name": "v1"})
    assert ok["ok"] is True and ok["file"]["name"] == "v1" and ok["file"]["version"] == 1
    stale = await handlers.files_update(store, {"fileId": fid, "ifVersion": 0, "name": "v2"})
    assert stale == {"ok": False, "conflict": True}
    assert await handlers.files_update(store, {"fileId": "nope01", "name": "x"}) == {"ok": False, "notFound": True}


async def test_delete_concurrency(store: FakeDriveStore) -> None:
    res = await handlers.files_create(store, {"name": "del"})
    fid = res["fileId"]
    assert await handlers.files_delete(store, {"fileId": fid, "ifVersion": 9}) == {"ok": False, "conflict": True}
    assert await handlers.files_delete(store, {"fileId": fid, "ifVersion": 0}) == {"ok": True}
    assert await handlers.files_get(store, {"fileId": fid}) == {"found": False}


async def test_changes_feed_cursor(store: FakeDriveStore) -> None:
    await handlers.files_create(store, {"name": "f1"})
    first = await handlers.changes(store, {})
    assert len(first["changes"]) == 1
    token = first["newStartPageToken"]
    # nothing new since the token
    second = await handlers.changes(store, {"pageToken": token})
    assert second["changes"] == []


async def test_about_quota(store: FakeDriveStore) -> None:
    await handlers.files_create(store, {"name": "big", "sizeBytes": 100})
    await handlers.files_create(store, {"name": "small", "sizeBytes": 23})
    res = await handlers.about(store, {})
    assert res["about"]["quotaUsedBytes"] == 123
