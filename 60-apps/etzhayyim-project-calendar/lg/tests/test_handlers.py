"""Deterministic canonical-handler tests using the in-memory FakeCalendarStore.

Verifies the SSoT behaviors the compat skins depend on: create→read round-trip,
list filtering + offset/limit/total pagination, optimistic-concurrency
(ifSequence) on update/delete, not-found, rsvp, and provider-id lookup — all
without a live kotoba pod.
"""

from __future__ import annotations

import pytest

from lg_calendar import handlers
from lg_calendar.store import FakeCalendarStore


@pytest.fixture()
def store() -> FakeCalendarStore:
    return FakeCalendarStore()


async def test_create_get_roundtrip(store: FakeCalendarStore) -> None:
    res = await handlers.create_event(store, {
        "summary": "Standup",
        "startsAt": "2026-06-02T09:00:00Z",
        "endsAt": "2026-06-02T09:15:00Z",
        "timezone": "Asia/Tokyo",
        "attendees": [{"email": "a@example.com", "responseStatus": "needsAction"}],
    })
    assert res["did"].startswith("did:web:calendar.etzhayyim.com:event:")
    assert res["iCalUid"].endswith("@calendar.etzhayyim.com")
    assert res["event"]["sequence"] == 0

    got = await handlers.get_event(store, {"eventId": res["event"]["uri"].split("/")[-1]})
    assert got["found"] is True
    assert got["event"]["summary"] == "Standup"
    assert got["event"]["startsAt"] == "2026-06-02T09:00:00Z"
    assert got["event"]["attendees"][0]["email"] == "a@example.com"


async def test_get_missing_returns_not_found(store: FakeCalendarStore) -> None:
    got = await handlers.get_event(store, {"eventId": "doesnotexist0001"})
    assert got == {"found": False}


async def test_lookup_by_ical_uid_and_provider_id(store: FakeCalendarStore) -> None:
    res = await handlers.create_event(store, {
        "summary": "Imported",
        "startsAt": "2026-06-03T10:00:00Z",
        "iCalUid": "abc-123@google.com",
        "googleEventId": "gcal_evt_999",
    })
    by_ical = await handlers.get_event(store, {"eventId": "x", "iCalUid": "abc-123@google.com"})
    assert by_ical["found"] is True
    by_gid = await handlers.get_event(store, {"eventId": "gcal_evt_999"})
    assert by_gid["found"] is True
    assert by_gid["event"]["summary"] == "Imported"
    assert res["event"]["googleEventId"] == "gcal_evt_999"


async def test_list_filter_and_pagination(store: FakeCalendarStore) -> None:
    for i in range(5):
        await handlers.create_event(store, {
            "summary": f"E{i}",
            "startsAt": f"2026-06-1{i}T08:00:00Z",
        })
    page1 = await handlers.list_events(store, {"offset": 0, "limit": 2})
    assert page1["total"] == 5
    assert page1["offset"] == 0 and page1["limit"] == 2
    assert len(page1["events"]) == 2
    assert page1["events"][0]["summary"] == "E0"  # sorted by startsAt asc

    page3 = await handlers.list_events(store, {"offset": 4, "limit": 2})
    assert len(page3["events"]) == 1

    ranged = await handlers.list_events(store, {
        "startsAfter": "2026-06-12T00:00:00Z",
        "startsBefore": "2026-06-14T00:00:00Z",
    })
    assert {e["summary"] for e in ranged["events"]} == {"E2", "E3"}


async def test_update_optimistic_concurrency(store: FakeCalendarStore) -> None:
    res = await handlers.create_event(store, {"summary": "v0", "startsAt": "2026-06-02T09:00:00Z"})
    slug = res["event"]["uri"].split("/")[-1]

    ok = await handlers.update_event(store, {"eventId": slug, "ifSequence": 0, "summary": "v1"})
    assert ok["ok"] is True
    assert ok["event"]["summary"] == "v1"
    assert ok["event"]["sequence"] == 1

    stale = await handlers.update_event(store, {"eventId": slug, "ifSequence": 0, "summary": "v2"})
    assert stale == {"ok": False, "conflict": True}

    missing = await handlers.update_event(store, {"eventId": "nope0001", "summary": "x"})
    assert missing == {"ok": False, "notFound": True}


async def test_delete_concurrency_and_removal(store: FakeCalendarStore) -> None:
    res = await handlers.create_event(store, {"summary": "del", "startsAt": "2026-06-02T09:00:00Z"})
    slug = res["event"]["uri"].split("/")[-1]

    conflict = await handlers.delete_event(store, {"eventId": slug, "ifSequence": 9})
    assert conflict == {"ok": False, "conflict": True}

    ok = await handlers.delete_event(store, {"eventId": slug, "ifSequence": 0})
    assert ok == {"ok": True}
    assert (await handlers.get_event(store, {"eventId": slug})) == {"found": False}


async def test_rsvp_updates_attendee(store: FakeCalendarStore) -> None:
    res = await handlers.create_event(store, {
        "summary": "party",
        "startsAt": "2026-06-02T09:00:00Z",
        "attendees": [{"did": "did:web:alice.etzhayyim.com", "responseStatus": "needsAction"}],
    })
    slug = res["event"]["uri"].split("/")[-1]
    r = await handlers.rsvp(store, {"eventId": slug, "respondentDid": "did:web:alice.etzhayyim.com", "response": "accepted"})
    assert r["ok"] is True and r["response"] == "accepted"
    got = await handlers.get_event(store, {"eventId": slug})
    assert got["event"]["attendees"][0]["responseStatus"] == "accepted"
    assert got["event"]["sequence"] == 1


async def test_list_calendars(store: FakeCalendarStore) -> None:
    res = await handlers.list_calendars(store, {})
    assert res["total"] == 1
    assert res["calendars"][0]["calendarId"] == "primary"
    assert res["calendars"][0]["primary"] is True
