"""Deterministic docs-handler + body-engine tests using FakeDocStore.

Covers create/get, the batchUpdate ops (appendParagraph, insertHeading,
replaceText, insertText at a global index, cross-element deleteRange), computed
startIndex/endIndex, revisionId writeControl concurrency, and not-found.
"""

from __future__ import annotations

import pytest

from lg_docs import docbody, handlers
from lg_docs.store import FakeDocStore


@pytest.fixture()
def store() -> FakeDocStore:
    return FakeDocStore()


def _texts(doc: dict) -> list[str]:
    return [e["text"] for e in doc["body"]]


def test_body_indices() -> None:
    body = [{"text": "hello"}, {"text": "world"}]
    idx = docbody.with_indices(body)
    assert idx[0]["startIndex"] == 0 and idx[0]["endIndex"] == 5
    assert idx[1]["startIndex"] == 6 and idx[1]["endIndex"] == 11  # +1 newline
    assert docbody.flatten_text(body) == "hello\nworld"


async def test_create_get(store: FakeDocStore) -> None:
    res = await handlers.documents_create(store, {"title": "Spec"})
    assert res["document"]["title"] == "Spec"
    assert res["document"]["revisionId"] == "rev-0"
    got = await handlers.documents_get(store, {"documentId": res["documentId"]})
    assert got["found"] is True and got["document"]["title"] == "Spec"


async def test_get_missing(store: FakeDocStore) -> None:
    assert await handlers.documents_get(store, {"documentId": "missing01"}) == {"found": False}


async def test_append_and_heading(store: FakeDocStore) -> None:
    did = (await handlers.documents_create(store, {"title": "T"}))["documentId"]
    res = await handlers.documents_batch_update(store, {"documentId": did, "requests": [
        {"op": "insertHeading", "text": "Intro", "headingLevel": 1},
        {"op": "appendParagraph", "text": "First para."},
        {"op": "appendParagraph", "text": "Second para."},
    ]})
    assert res["ok"] is True and res["applied"] == 3 and res["revisionId"] == "rev-1"
    doc = (await handlers.documents_get(store, {"documentId": did}))["document"]
    assert _texts(doc) == ["Intro", "First para.", "Second para."]
    assert doc["body"][0]["kind"] == "heading" and doc["body"][0]["headingLevel"] == 1


async def test_replace_and_insert_text(store: FakeDocStore) -> None:
    did = (await handlers.documents_create(store, {"title": "T", "body": [{"text": "Hello NAME, welcome"}]}))["documentId"]
    await handlers.documents_batch_update(store, {"documentId": did, "requests": [{"op": "replaceText", "matchText": "NAME", "text": "Jun"}]})
    doc = (await handlers.documents_get(store, {"documentId": did}))["document"]
    assert _texts(doc) == ["Hello Jun, welcome"]
    # insert at global index 5 (after "Hello")
    await handlers.documents_batch_update(store, {"documentId": did, "requests": [{"op": "insertText", "index": 5, "text": " there"}]})
    doc = (await handlers.documents_get(store, {"documentId": did}))["document"]
    assert _texts(doc) == ["Hello there Jun, welcome"]


async def test_delete_range_cross_element(store: FakeDocStore) -> None:
    did = (await handlers.documents_create(store, {"title": "T", "body": [{"text": "AAAA"}, {"text": "BBBB"}]}))["documentId"]
    # flattened "AAAA\nBBBB": delete from index 2 ("AA|AA") to index 7 ("BB|BB") → merge
    await handlers.documents_batch_update(store, {"documentId": did, "requests": [{"op": "deleteRange", "startIndex": 2, "endIndex": 7}]})
    doc = (await handlers.documents_get(store, {"documentId": did}))["document"]
    assert _texts(doc) == ["AABB"]  # head "AA" + tail "BB", middle dropped, elements merged


async def test_revision_concurrency(store: FakeDocStore) -> None:
    did = (await handlers.documents_create(store, {"title": "T"}))["documentId"]
    ok = await handlers.documents_batch_update(store, {"documentId": did, "requiredRevisionId": "rev-0", "requests": [{"op": "appendParagraph", "text": "x"}]})
    assert ok["ok"] is True and ok["revisionId"] == "rev-1"
    stale = await handlers.documents_batch_update(store, {"documentId": did, "requiredRevisionId": "rev-0", "requests": [{"op": "appendParagraph", "text": "y"}]})
    assert stale == {"ok": False, "conflict": True}
    assert await handlers.documents_batch_update(store, {"documentId": "nope01", "requests": []}) == {"ok": False, "notFound": True}


async def test_replace_body_sequence_used_by_ms_put(store: FakeDocStore) -> None:
    # Mirrors the docs-compat MS /content PUT: deleteRange(whole) + insertText(0, line0) + appendParagraph(rest).
    did = (await handlers.documents_create(store, {"title": "T", "body": [{"text": "old line one"}, {"text": "old line two"}]}))["documentId"]
    doc = (await handlers.documents_get(store, {"documentId": did}))["document"]
    doc_len = sum(len(e["text"]) + 1 for e in doc["body"])
    reqs = [{"op": "deleteRange", "startIndex": 0, "endIndex": doc_len},
            {"op": "insertText", "index": 0, "text": "alpha"},
            {"op": "appendParagraph", "text": "beta"}]
    await handlers.documents_batch_update(store, {"documentId": did, "requests": reqs})
    doc2 = (await handlers.documents_get(store, {"documentId": did}))["document"]
    assert _texts(doc2) == ["alpha", "beta"]


async def test_lookup_by_provider_id(store: FakeDocStore) -> None:
    await handlers.documents_create(store, {"title": "Imported", "googleDocumentId": "gdoc_1"})
    got = await handlers.documents_get(store, {"documentId": "gdoc_1"})
    assert got["found"] is True and got["document"]["title"] == "Imported"
